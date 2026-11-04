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

    # 429/5xx 重试配置
    LLM_BACKOFF_MAX = 30.0
    LLM_BACKOFF_BASE = 2.0  # 首次退避秒数，每次 ×2：2,4,8,16,30,30…

    def _make_llm_call(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> Tuple[str, int, int, float]:
        """
        Make a call to the LLM with error handling and metrics tracking.
        对 429（限流）和 5xx（服务端错误）自动重试 + 指数退避；
        尊重 Retry-After 响应头。其他 4xx（404/401/403）不重试直接抛出。

        Args:
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Override system prompt for this call

        Returns:
            Tuple of (response_content, prompt_tokens, completion_tokens, processing_time)

        Raises:
            Exception: Immediately for non-retryable errors; retryable errors have no attempt limit
        """
        start_time = time.time()
        self.last_llm_call = {'messages': [
            {'role': 'system', 'content': system_prompt or self.system_prompt},
            {'role': 'user', 'content': prompt}], 'raw_response': None, 'retries': []}

        if self.api_mode == "responses":
            return self._make_responses_call(prompt, temperature, max_tokens, system_prompt, start_time)
        if self.api_mode != "chat_completions":
            raise ValueError(f"Unsupported API mode: {self.api_mode}")

        messages = [
            {"role": "system", "content": system_prompt or self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        call_kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature
        }

        if max_tokens:
            call_kwargs["max_tokens"] = max_tokens

        base_url = str(self.client.base_url).rstrip('/')
        url = f"{base_url}/chat/completions"

        api_key = self.client.api_key if hasattr(self.client, 'api_key') else None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        attempt = 0
        while True:
            try:
                # 代理按 NO_PROXY 条件判断；SSL 校验按 SSL_VERIFY 环境变量
                proxy = _proxy_for_url(url)
                client_kwargs = dict(timeout=600.0, verify=_ssl_verify())
                if proxy:
                    client_kwargs["proxy"] = proxy
                with httpx.Client(**client_kwargs) as http_client:
                    response = http_client.post(url, json=call_kwargs, headers=headers)

                    # 其他 4xx（404/401/403）不重试
                    response.raise_for_status()
                    result = response.json()

                content = result["choices"][0]["message"]["content"].strip()
                prompt_tokens = result.get("usage", {}).get("prompt_tokens", 0)
                completion_tokens = result.get("usage", {}).get("completion_tokens", 0)
                processing_time = time.time() - start_time

                # Update metrics
                self.metrics['total_calls'] += 1
                self.metrics['total_prompt_tokens'] += prompt_tokens
                self.metrics['total_completion_tokens'] += completion_tokens
                self.metrics['total_time'] += processing_time

                self.last_llm_call.update(raw_response=content, prompt_tokens=prompt_tokens,
                                          completion_tokens=completion_tokens, elapsed=processing_time)
                return content, prompt_tokens, completion_tokens, processing_time

            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                response = getattr(exc, 'response', None)
                status = getattr(response, 'status_code', None)
                # Keep the original 429/5xx/network retry conditions.
                if status is not None and status != 429 and status < 500:
                    self.metrics['error_count'] += 1
                    self.metrics['total_time'] += time.time() - start_time
                    raise
                wait = min(self.LLM_BACKOFF_MAX, self.LLM_BACKOFF_BASE * 2 ** min(attempt, 4))
                retry_after = response.headers.get('Retry-After') if response is not None else None
                if retry_after:
                    try:
                        requested = float(retry_after)
                        if 0 <= requested < float('inf'):
                            wait = min(self.LLM_BACKOFF_MAX, requested)
                    except ValueError:
                        pass
                attempt += 1
                self.last_llm_call['retries'].append(dict(attempt=attempt, status=status, wait_seconds=wait))
                logger.warning('%s LLM %s, retry %d; waiting %.1fs',
                               type(self).__name__, status or type(exc).__name__, attempt, wait)
                time.sleep(wait)

    def _make_responses_call(
        self,
        prompt: str,
        temperature: float,
        max_tokens: Optional[int],
        system_prompt: Optional[str],
        start_time: float,
    ) -> Tuple[str, int, int, float]:
        """Call an OpenAI-compatible Responses endpoint for API mode 1."""
        try:
            call_kwargs = {
                "model": self.model_name,
                "instructions": system_prompt or self.system_prompt,
                "input": prompt,
                "temperature": temperature,
                "store": False,
            }
            if max_tokens:
                call_kwargs["max_output_tokens"] = max_tokens

            response = self.client.responses.create(**call_kwargs)
            content = (getattr(response, "output_text", "") or "").strip()
            if not content:
                raise ValueError("Responses API returned no text output")

            usage = getattr(response, "usage", None)
            prompt_tokens = getattr(usage, "input_tokens", 0) or 0
            completion_tokens = getattr(usage, "output_tokens", 0) or 0
            processing_time = time.time() - start_time
            self.metrics['total_calls'] += 1
            self.metrics['total_prompt_tokens'] += prompt_tokens
            self.metrics['total_completion_tokens'] += completion_tokens
            self.metrics['total_time'] += processing_time
            self.last_llm_call.update(raw_response=content, prompt_tokens=prompt_tokens,
                                      completion_tokens=completion_tokens, elapsed=processing_time)
            return content, prompt_tokens, completion_tokens, processing_time
        except Exception as error:
            processing_time = time.time() - start_time
            self.metrics['error_count'] += 1
            self.metrics['total_time'] += processing_time
            logger.error(f"{self.__class__.__name__} Responses API call failed: {error}")
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
