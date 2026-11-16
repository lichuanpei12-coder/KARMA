import json
import unittest
from unittest.mock import patch

from karma.agents.feedback_add.agent import FeedbackAddAgent
from karma.agents.feedback_operations import apply_operations, validate_reply
from karma.agents.feedback_remove.agent import FeedbackRemoveAgent
from karma.agents.feedback_replace.agent import FeedbackReplaceAgent
from karma.agents.relationship_extraction.agent import RelationshipExtractionAgent
from karma.agents.text_generation.agent import TextGenerationAgent
from karma.core.data_structures import KnowledgeTriple


class PromptLanguageTests(unittest.TestCase):
    def test_relationship_agent_can_switch_back_to_english(self):
        agent = RelationshipExtractionAgent(None, "offline")
        english_system = agent.system_prompt
        with patch.object(agent, "_make_llm_call", return_value=("[]", 0, 0, 0)) as call:
            agent.process(["超压时，PLC会关闭阀门。"], [])
            self.assertIn("停电时，值班员", call.call_args.kwargs["system_prompt"])
            agent.process(["The sensor reports a reading."], [])
            self.assertEqual(call.call_args.kwargs["system_prompt"], english_system)

    def test_grouped_reconstruction_can_select_chinese_without_sending_source_text(self):
        agent = TextGenerationAgent(None, "offline")
        source = "仅在预热完成后，PLC才会启动P2。"
        groups = [{"sentence_id": "S1", "text": source, "triples": [
            {"index": 0, "head": "PLC", "relation": "会启动", "tail": "P2"}
        ]}]
        reply = '[{"sentence_id":"S1","text":"PLC会启动P2。"}]'
        with patch.object(agent, "_make_llm_call", return_value=(reply, 0, 0, 0)) as call:
            agent.process([], sentence_groups=groups, scope="sentence")
        prompt = call.call_args.args[0]
        self.assertIn("中文组保留输入用词", prompt)
        self.assertNotIn(source, prompt)
        self.assertNotIn("仅在预热完成后", prompt)

    def test_chinese_feedback_examples_apply_with_current_operation_schema(self):
        for cls in (FeedbackAddAgent, FeedbackReplaceAgent, FeedbackRemoveAgent):
            with self.subTest(agent=cls.__name__):
                agent = cls(None, "offline")
                sample_lines = agent.chinese_examples_prompt.splitlines()
                context = json.loads(next(line.split("：", 1)[1] for line in sample_lines
                                          if line.startswith("输入：")))
                reply = json.loads(next(line.split("：", 1)[1] for line in sample_lines
                                        if line.startswith("输出：")))
                sentences = context["source_sentences"]
                triples = [KnowledgeTriple(**{key: value for key, value in item.items() if key != "index"})
                           for item in context["current_collection"]["triples"]]
                messages = agent.build_messages(context)
                self.assertIn(agent.chinese_examples_prompt, messages[1]["content"])
                self.assertNotIn(agent.examples_prompt, messages[1]["content"])
                validate_reply(reply, agent.stage, triples, sentences)
                _, audit = apply_operations(agent.stage, triples, reply, sentences)
                self.assertEqual(audit["status"], "applied")
