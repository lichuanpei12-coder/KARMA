"""Experiment-only transport: persist every request/attempt without credentials."""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from karma.core.base_agent import _proxy_for_url, _ssl_verify


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


class RecordedCalls:
    def __init__(self, root, config, api_key, client_factory=None, sleep=time.sleep):
        self.root, self.config, self.api_key = Path(root), config, api_key
        self.client_factory = client_factory or httpx.Client
        self.sleep = sleep
        self.stage = 'unassigned'
        self.records = []
        self.auth_failed = False

    def _redact(self, text):
        if self.api_key:
            text = text.replace(self.api_key, '[REDACTED]')
        return re.sub(r'(https?://)[^/\s@]+@', r'\1[REDACTED]@', text)

    def bind(self, agent):
        # Instance-only injection; the production agent class remains unchanged.
        def call(prompt, temperature=0.1, max_tokens=None, system_prompt=None):
            return self.call(agent, prompt, temperature, max_tokens, system_prompt)
        agent._make_llm_call = call
        return agent

    def call(self, agent, prompt, temperature, max_tokens, system_prompt):
        mode = self.config['api_mode']
        system = system_prompt or agent.system_prompt
        messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}]
        payload = {'model': self.config['model'], 'temperature': temperature}
        if mode == 'responses':
            payload.update(instructions=system, input=prompt, store=False)
            if max_tokens:
                payload['max_output_tokens'] = max_tokens
        else:
            payload['messages'] = messages
            if max_tokens:
                payload['max_tokens'] = max_tokens
        suffix = 'responses' if mode == 'responses' else 'chat/completions'
        url = self.config['base_url'].rstrip('/') + '/' + suffix
        record = {'id': len(self.records), 'stage': self.stage, 'agent': type(agent).__name__,
                  'started_at': datetime.now(timezone.utc).isoformat(),
                  'url': url, 'messages': messages, 'payload': payload,
                  'status': 'pending', 'attempts': []}
        self.records.append(record)
        path = self.root / self.stage / f'call_{record["id"]:03d}.json'
        save(path, record)
        start = time.monotonic()
        for number in range(self.config.get('max_retries', 2) + 1):
            attempt = {'number': number + 1}
            record['attempts'].append(attempt)
            retry = False
            wait = min(2 ** (number + 1), 30)
            try:
                kwargs = {'timeout': self.config.get('timeout', 600), 'verify': _ssl_verify()}
                proxy = _proxy_for_url(url)
                if proxy:
                    kwargs['proxy'] = proxy
                with self.client_factory(**kwargs) as client:
                    response = client.post(url, json=payload, headers={
                        'Authorization': 'Bearer ' + self.api_key, 'Content-Type': 'application/json'})
                attempt['http_status'] = response.status_code
                attempt['response_body'] = self._redact(response.text)
                if response.status_code >= 400:
                    self.auth_failed |= response.status_code in (401, 403)
                    retry = response.status_code == 429 or response.status_code >= 500
                    try:
                        wait = min(60, max(0, float(response.headers.get('Retry-After', wait))))
                    except ValueError:
                        pass
                    raise ValueError(f'HTTP {response.status_code}')
                data = response.json()
                usage = data.get('usage') or {}
                if mode == 'responses':
                    content = ''.join(part.get('text', '') for item in data.get('output', [])
                                      if item.get('type') == 'message'
                                      for part in item.get('content', []) if part.get('type') == 'output_text')
                    finish = data.get('status')
                    complete = finish == 'completed'
                    truncated = finish == 'incomplete'
                    pt, ct = usage.get('input_tokens'), usage.get('output_tokens')
                else:
                    choice = data['choices'][0]
                    content = choice['message']['content']
                    finish = choice.get('finish_reason')
                    complete = finish == 'stop'
                    truncated = finish == 'length'
                    pt, ct = usage.get('prompt_tokens'), usage.get('completion_tokens')
                if not isinstance(content, str) or not content.strip():
                    raise ValueError('Response has no usable text content')
                record.update(content=content, returned_model=data.get('model'), finish_reason=finish,
                              prompt_tokens=pt, completion_tokens=ct)
                if not complete:
                    record['status'] = 'truncated' if truncated else 'incomplete_response'
                    raise ValueError(f'Unfinished response: {finish}')
                attempt['status'] = record['status'] = 'success'
                record['elapsed_seconds'] = time.monotonic() - start
                save(path, record)
                # BaseAgent interface uses numeric usage; the persisted record keeps unknown as null.
                return content.strip(), pt or 0, ct or 0, record['elapsed_seconds']
            except Exception as exc:
                attempt['status'] = 'failed'
                attempt['error'] = self._redact(f'{type(exc).__name__}: {exc}')
                retry |= isinstance(exc, httpx.RequestError)
                if record['status'] == 'pending':
                    record['status'] = ('response_parse_failed' if attempt.get('http_status', 500) < 400
                                        else 'api_failed')
                record['elapsed_seconds'] = time.monotonic() - start
                save(path, record)
                if retry and number < self.config.get('max_retries', 2):
                    attempt['retry_wait_seconds'] = wait
                    save(path, record)
                    self.sleep(wait)
                    record['status'] = 'pending'
                    continue
                raise RuntimeError(f'Call {record["id"]} failed; see saved attempt record') from None
