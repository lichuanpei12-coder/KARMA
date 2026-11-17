import json
import unittest
from unittest.mock import patch

from karma.agents.entity_extraction.agent import EntityExtractionAgent
from karma.agents.feedback_add.agent import FeedbackAddAgent
from karma.agents.feedback_operations import apply_operations, validate_reply
from karma.agents.feedback_remove.agent import FeedbackRemoveAgent
from karma.agents.feedback_replace.agent import FeedbackReplaceAgent
from karma.agents.relationship_extraction.agent import RelationshipExtractionAgent
from karma.agents.text_generation.agent import TextGenerationAgent
from karma.agents.triple_splitting.agent import TripleSplittingAgent
from karma.core.data_structures import KnowledgeTriple


class PromptLanguageTests(unittest.TestCase):
    def test_both_entity_rounds_select_chinese_rules_only_for_chinese_source(self):
        agent = EntityExtractionAgent(None, "offline")
        with patch.object(agent, "_make_llm_call", return_value=("[]", 0, 0, 0)) as call:
            for text, chinese in (("站台西侧的临时检票口设有两台验票机。", True),
                                  ("The station has two ticket machines.", False)):
                agent.process([text])
                baseline = call.call_args
                agent.revise_entities(text, [], [], {"sentence_differences": []})
                feedback = call.call_args
                self.assertEqual(baseline.kwargs["system_prompt"], feedback.kwargs["system_prompt"])
                for request in (baseline, feedback):
                    self.assertEqual("一套左右滑轮固定在支架上" in request.kwargs["system_prompt"], chinese)
                    self.assertEqual('"context": "控制器可以查询ECU。ECU存储读数。"' in request.args[0], not chinese)

    def test_relationship_agent_can_switch_back_to_english(self):
        agent = RelationshipExtractionAgent(None, "offline")
        english_system = agent.system_prompt
        with patch.object(agent, "_make_llm_call", return_value=("[]", 0, 0, 0)) as call:
            agent.process(["超压时，PLC会关闭阀门。"], [])
            chinese_system = call.call_args.kwargs["system_prompt"]
            for rule in ("停电时，值班员", "在一些实施例中", "每条三元组表达一个独立事实",
                         "候选名单可能遗漏", "对应不明确时保留原文代词"):
                self.assertIn(rule, chinese_system)
            agent.process(["The sensor reports a reading."], [])
            self.assertEqual(call.call_args.kwargs["system_prompt"], english_system)

    def test_splitter_sends_chinese_structure_examples(self):
        agent = TripleSplittingAgent(None, "offline")
        with patch.object(agent, "_make_llm_call", return_value=('{"add":[],"replace":[]}', 0, 0, 0)) as call:
            for text in ("车站设有检票机。", "The station has a ticket machine."):
                agent.process(text, [])
                prompt = call.call_args.args[0]
                self.assertIn("每条关系按源句语义确定主体和客体，三元组之间可以首尾相接，也可以共享主体或关系", prompt)
            self.assertNotIn("机箱装有处理信号的模块", prompt)
            self.assertIn("The system includes a module that processes data.", prompt)
        self.assertIn("机箱装有处理信号的模块", call.call_args_list[0].args[0])

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
                inputs = [line.split("：", 1)[1] for line in sample_lines if line.startswith("输入：")]
                outputs = [line.split("：", 1)[1] for line in sample_lines if line.startswith("输出：")]
                self.assertGreaterEqual(len(inputs), 3)
                self.assertEqual(len(inputs), len(outputs))
                for sample_input, sample_output in zip(inputs, outputs):
                    context, reply = json.loads(sample_input), json.loads(sample_output)
                    sentences = context["source_sentences"]
                    triples = [KnowledgeTriple(**{k: v for k, v in item.items() if k != "index"})
                               for item in context["current_collection"]["triples"]]
                    messages = agent.build_messages(context)
                    self.assertIn(agent.chinese_examples_prompt, messages[1]["content"])
                    self.assertNotIn(agent.examples_prompt, messages[1]["content"])
                    validate_reply(reply, agent.stage, triples, sentences)
                    _, audit = apply_operations(agent.stage, triples, reply, sentences)
                    has_operations = any(reply.get(key) for key in ("add", "replace", "remove"))
                    self.assertEqual(audit["status"], "applied" if has_operations else "no_changes")
