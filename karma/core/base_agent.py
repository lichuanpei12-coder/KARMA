"""
Base agent class for the KARMA framework.

This module provides the abstract base class that all KARMA agents inherit from,
ensuring consistent interfaces and shared functionality.
"""
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional
import time
import logging
from urllib.parse import urlparse
from openai import OpenAI
import httpx
from .api_retry import RequestPacer, call_with_retry

logger = logging.getLogger(__name__)

# === API 连接配置（改回原状：删掉这段 + settings.py:22 改回 https://api.modelarts-maas.com/v2 + httpx.Client 改回硬编码 proxy/verify）===
os.environ.setdefault("SSL_VERIFY", "false")              # SSL 校验关闭
os.environ.setdefault("NO_PROXY", ".huawei.com,.localhost")  # 华为内网域名不走代理
# 默认代理（非 NO_PROXY 域名时使用）
_DEFAULT_PROXY = os.environ.get("KARMA_PROXY", "")


def _proxy_for_url(url):
    """根据 NO_PROXY 决定是否用代理：命中 NO_PROXY 的域名返回 None（直连）。"""
    no_proxy = os.environ.get("NO_PROXY", "")
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        host = ""
    host = host.lower()
    for pattern in no_proxy.split(","):
        pattern = pattern.strip().lower()
        if not pattern:
            continue
        # 命中：host == pattern 或 host 以 .pattern 结尾（如 models.ascend.huawei.com 命中 .huawei.com）
        if host == pattern or host.endswith("." + pattern) or host.endswith(pattern):
            return None
    return _DEFAULT_PROXY


def _ssl_verify():
    """SSL_VERIFY=true 校验，其他（含 false）不校验。"""
    return os.environ.get("SSL_VERIFY", "false").lower() == "true"
# === API 连接配置结束 ===



class BaseAgent(ABC):
    """
    Abstract base class for all KARMA agents.

    This class provides common functionality including LLM client management,
    token tracking, error handling, and performance monitoring.

    Attributes:
        client: OpenAI client instance
        model_name: LLM model identifier
        system_prompt: System prompt for the agent
        metrics: Performance tracking metrics
    """

    def __init__(self, client: OpenAI, model_name: str, system_prompt: str = ""):
        """
        Initialize the base agent.

        Args:
            client: OpenAI client instance
            model_name: LLM model identifier
            system_prompt: System prompt for the agent
        """
        self.client = client
        self.model_name = model_name
        self.system_prompt = system_prompt
        # The pipeline sets this for all agents.  Keep the current implementation
        # as the default for direct use of an individual agent.
        self.api_mode = "chat_completions"
        self.request_pacer = RequestPacer()
        self.last_llm_call = {}
        self.metrics = {
            'total_calls': 0,
            'total_prompt_tokens': 0,
            'total_completion_tokens': 0,
            'total_time': 0.0,
            'error_count': 0
        }

    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """
        Main processing method for the agent.

        This method must be implemented by all concrete agent classes.
        """
        pass

    def _make_llm_call(self, prompt: str, temperature: float = 0.1,
                       max_tokens: Optional[int] = None,
                       system_prompt: Optional[str] = None) -> Tuple[str, int, int, float]:
        """Both API modes retry transient failures indefinitely, with paced backoff."""
        start = time.monotonic()
        system = system_prompt or self.system_prompt
        messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}]
        audit = {'messages': messages, 'api_mode': self.api_mode, 'retries': [], 'raw_response': None}
        self.last_llm_call = audit

        def request():
            if self.api_mode == 'responses':
                kwargs = dict(model=self.model_name, instructions=system, input=prompt,
                              temperature=temperature, store=False)
                if max_tokens:
                    kwargs['max_output_tokens'] = max_tokens
                # Pipeline SDK client has max_retries=0: one common retry policy.
                return self.client.responses.create(**kwargs)
            if self.api_mode != 'chat_completions':
                raise ValueError(f'Unsupported API mode: {self.api_mode}')
            kwargs = dict(model=self.model_name, messages=messages, temperature=temperature)
            if max_tokens:
                kwargs['max_tokens'] = max_tokens
            url = str(self.client.base_url).rstrip('/') + '/chat/completions'
            config = dict(timeout=600.0, verify=_ssl_verify())
            proxy = _proxy_for_url(url)
            if proxy:
                config['proxy'] = proxy
            with httpx.Client(**config) as client:
                response = client.post(url, json=kwargs, headers={
                    'Authorization': f'Bearer {self.client.api_key}', 'Content-Type': 'application/json'})
                response.raise_for_status()
                return response.json()
        try:
            result = call_with_retry(request, self.request_pacer, audit['retries'], type(self).__name__)
            if self.api_mode == 'responses':
                content = (getattr(result, 'output_text', '') or '').strip()
                usage = getattr(result, 'usage', None)
                prompt_tokens = getattr(usage, 'input_tokens', 0) or 0
                completion_tokens = getattr(usage, 'output_tokens', 0) or 0
            else:
                content = result['choices'][0]['message']['content'].strip()
                prompt_tokens = result.get('usage', {}).get('prompt_tokens', 0)
                completion_tokens = result.get('usage', {}).get('completion_tokens', 0)
            if not content:
                raise ValueError('LLM returned no text output')
            elapsed = time.monotonic() - start
            audit.update(raw_response=content, prompt_tokens=prompt_tokens,
                         completion_tokens=completion_tokens, elapsed=elapsed)
            self.metrics['total_calls'] += 1
            self.metrics['total_prompt_tokens'] += prompt_tokens
            self.metrics['total_completion_tokens'] += completion_tokens
            self.metrics['total_time'] += elapsed
            return content, prompt_tokens, completion_tokens, elapsed
        except Exception as exc:
            elapsed = time.monotonic() - start
            audit.update(error_type=type(exc).__name__, elapsed=elapsed)
            self.metrics['error_count'] += 1
            self.metrics['total_time'] += elapsed
            raise

    def _extract_float_from_text(self, text: str, default: float = 0.5) -> float:
        """
        Extract a float value from text response.

        Args:
            text: Text containing float value
            default: Default value if no float found

        Returns:
            Extracted float value, clamped to [0.0, 1.0]
        """
        import re

        # Look for float numbers in the text
        float_matches = re.findall(r"[-+]?\d*\.\d+|\d+", text)
        if float_matches:
            try:
                score = float(float_matches[0])
                # Clamp to [0.0, 1.0]
                return max(0.0, min(1.0, score))
            except ValueError:
                pass

        return default

    def _parse_json_response(self, response: str) -> List[Dict]:
        """
        Parse JSON response from LLM with error handling.

        Args:
            response: LLM response containing JSON

        Returns:
            Parsed JSON data as list of dictionaries
        """
        import json

        try:
            # Try to find JSON array in response
            if "[" in response and "]" in response:
                json_str = response[response.find("["):response.rfind("]")+1]
                return json.loads(json_str)

            # Try to parse the entire response as JSON
            return json.loads(response)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return []

    def get_metrics(self) -> Dict:
        """
        Get performance metrics for this agent.

        Returns:
            Dictionary of performance metrics
        """
        return self.metrics.copy()

    def reset_metrics(self):
        """Reset all performance metrics."""
        self.metrics = {
            'total_calls': 0,
            'total_prompt_tokens': 0,
            'total_completion_tokens': 0,
            'total_time': 0.0,
            'error_count': 0
        }

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(model={self.model_name})"

    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return f"{self.__class__.__name__}(model={self.model_name}, calls={self.metrics['total_calls']})"
