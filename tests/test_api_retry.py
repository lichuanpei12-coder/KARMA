import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace
import httpx
from openai import RateLimitError
from karma.agents.feedback_add.agent import FeedbackAddAgent
from karma.agents.text_generation.agent import TextGenerationAgent


class RetryTests(unittest.TestCase):
    def response(self, status, body=None, headers=None):
        return httpx.Response(status, json=body or {}, headers=headers,
                              request=httpx.Request('POST', 'https://offline.invalid/api'))

    def agent(self, mode):
        client = SimpleNamespace(base_url='https://offline.invalid', api_key='offline',
                                 responses=SimpleNamespace(create=Mock()))
        agent = FeedbackAddAgent(client, 'offline')
        agent.api_mode = mode
        return agent

    def test_chat_rate_limit_beyond_old_limit_then_success(self):
        agent = self.agent('chat_completions')
        responses = [self.response(429, headers={'Retry-After': '3'}) for _ in range(9)]
        responses.append(self.response(200, {'choices': [{'message': {'content': '{}'}}]}))
        with patch('httpx.Client.post', side_effect=responses) as post, patch('karma.core.base_agent.time.sleep') as sleep:
            self.assertEqual(agent._make_llm_call('test')[0], '{}')
        self.assertEqual(post.call_count, 10)
        self.assertEqual(len(agent.last_llm_call['retries']), 9)
        self.assertTrue(all(c.args == (3.0,) for c in sleep.call_args_list))

    def test_responses_keeps_original_sdk_error_handling(self):
        agent = self.agent('responses')
        exc = RateLimitError('limited', response=self.response(429), body={})
        agent.client.responses.create.side_effect = exc
        with patch('karma.core.base_agent.time.sleep') as sleep:
            with self.assertRaises(RateLimitError):
                agent._make_llm_call('test')
        self.assertEqual(agent.client.responses.create.call_count, 1)
        sleep.assert_not_called()

    def test_network_and_server_failures_retry(self):
        agent = self.agent('chat_completions')
        with patch('httpx.Client.post', side_effect=[httpx.ConnectError('offline'), self.response(503),
                   self.response(200, {'choices': [{'message': {'content': 'ok'}}]})]), patch('karma.core.base_agent.time.sleep'):
            self.assertEqual(agent._make_llm_call('test')[0], 'ok')
        self.assertEqual(len(agent.last_llm_call['retries']), 2)

    def test_keyboard_interrupt_escapes_retry(self):
        agent = self.agent('chat_completions')
        with patch('httpx.Client.post', return_value=self.response(429)), \
                patch('karma.core.base_agent.time.sleep', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                agent._make_llm_call('test')

    def test_non_retryable_errors_keep_original_agent_fallback(self):
        for status in (400, 401, 403):
            with self.subTest(status=status):
                a = self.agent('chat_completions')
                g = TextGenerationAgent(a.client, 'offline')
                with patch('httpx.Client.post', return_value=self.response(status)) as post, \
                        patch('karma.core.base_agent.time.sleep') as sleep:
                    text = g.generate_grouped([dict(sentence_id='S1', triples=[dict(index=0, head='a', relation='b', tail='c')])])
                self.assertEqual(text, 'a : b : c')
                self.assertEqual(g.last_grouped_generation[0]['generation_status'], 'literal_fallback')
                self.assertEqual(post.call_count, 1)
                sleep.assert_not_called()

    def test_quota_error_429_uses_same_unlimited_retry(self):
        for code in ('insufficient_quota', 'billing_hard_limit_reached'):
            with self.subTest(code=code):
                agent = self.agent('chat_completions')
                responses = [self.response(429, {'error': {'code': code}})] * 7
                responses.append(self.response(200, {'choices': [{'message': {'content': 'ok'}}]}))
                with patch('httpx.Client.post', side_effect=responses) as post, patch('karma.core.base_agent.time.sleep'):
                    self.assertEqual(agent._make_llm_call('test')[0], 'ok')
                self.assertEqual(post.call_count, 8)

    def test_exponential_wait_caps_at_30_forever(self):
        agent = self.agent('chat_completions')
        responses = [self.response(503) for _ in range(12)]
        responses.append(self.response(200, {'choices': [{'message': {'content': 'ok'}}]}))
        with patch('httpx.Client.post', side_effect=responses), patch('karma.core.base_agent.time.sleep') as sleep:
            self.assertEqual(agent._make_llm_call('test')[0], 'ok')
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2,4,8,16]+[30]*8)

    def test_retry_after_keeps_original_numeric_support_and_caps_30(self):
        for value, expected in [('120',30),('5',5),('invalid',2),('nan',2),('-1',2)]:
            with self.subTest(value=value):
                agent = self.agent('chat_completions')
                with patch('httpx.Client.post', side_effect=[self.response(429,headers={'Retry-After':value}),
                        self.response(200,{'choices':[{'message':{'content':'ok'}}]})]), \
                        patch('karma.core.base_agent.time.sleep') as sleep:
                    agent._make_llm_call('test')
                sleep.assert_called_once_with(expected)

    def test_408_409_keep_original_no_retry_policy(self):
        for status in (408,409):
            agent = self.agent('chat_completions')
            with patch('httpx.Client.post',return_value=self.response(status)) as post, \
                    patch('karma.core.base_agent.time.sleep') as sleep:
                with self.assertRaises(httpx.HTTPStatusError):
                    agent._make_llm_call('test')
            post.assert_called_once()
            sleep.assert_not_called()
