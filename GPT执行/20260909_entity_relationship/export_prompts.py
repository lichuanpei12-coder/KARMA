"""Render before/after prompts with the same synthetic input, without API calls."""
from pathlib import Path
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from karma.agents.entity_extraction.agent import EntityExtractionAgent
from karma.agents.relationship_extraction.agent import RelationshipExtractionAgent
from karma.core.data_structures import KGEntity, KnowledgeTriple


def load_old(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old_e = load_old('entity_before', HERE / 'before/karma/agents/entity_extraction/agent.py').EntityExtractionAgent(None, 'offline')
old_r = load_old('relationship_before', HERE / 'before/karma/agents/relationship_extraction/agent.py').RelationshipExtractionAgent(None, 'offline')
new_e = EntityExtractionAgent(None, 'offline')
new_r = RelationshipExtractionAgent(None, 'offline')
source = 'The controller may query the ECU. The sensor monitors the road.'
e1 = [KGEntity(name, name=name) for name in ('The controller', 'the ECU', 'phantom device')]
e2 = [KGEntity(name, name=name) for name in ('The controller', 'the ECU', 'The sensor', 'the road')]
baseline = [KnowledgeTriple('The controller', 'controls', 'the ECU'), KnowledgeTriple('the ECU', 'stores', 'phantom device')]
diff = {'unique_to_text_a': ['The sensor monitors the road.'],
        'unique_to_text_b': ['The ECU stores phantom device.']}
captured = []


def capture(agent, title, invoke, reply='[]'):
    def fake(prompt, **kwargs):
        captured.append((title, kwargs.get('system_prompt') or agent.system_prompt, prompt))
        return reply, 0, 0, 0
    agent._make_llm_call = fake
    invoke()


for label, e, r in [('修改前', old_e, old_r), ('修改后', new_e, new_r)]:
    capture(e, label + '：第一轮 Entity', lambda: e.process([source], {}))
    capture(r, label + '：第一轮 Relationship', lambda: r.process([source], e1, {}))
    if label == '修改前':
        capture(e, label + '：第二轮 Entity', lambda: e.process([source], diff))
        capture(r, label + '：第二轮 Relationship', lambda: r.revise_relationships(source, baseline, diff),
                '{"add":[],"remove":[],"replace":[]}')
    else:
        capture(e, label + '：第二轮 Entity', lambda: e.revise_entities(source, e1, baseline, diff))
        capture(r, label + '：第二轮 Relationship', lambda: r.revise_relationships(source, baseline, diff, e2),
                '{"add":[],"remove":[],"replace":[]}')

lines = ['# Entity / Relationship 修改前后完整提示词', '',
         '使用同一段人工示例捕获实际发送给模型的 system 与 user 内容；未调用 API。',
         '“修改前”是本次修改开始时的本地版本，已经包含此前的三元组增量审校。',
         '第二轮 Entity 修改前没有 E1/T1 输入，修改后有；第二轮 Relationship 修改后增加 E2。', '']
for title, system, user in captured:
    lines.extend(['## ' + title, '', '### System', '', '```text', system.strip(), '```', '',
                  '### User', '', '```text', user.strip(), '```', ''])
(HERE / 'prompt_comparison.md').write_text('\n'.join(lines), encoding='utf-8')
(HERE / 'rendered_prompts.json').write_text(json.dumps(
    [{'stage': title, 'system': system, 'user': user} for title, system, user in captured],
    ensure_ascii=False, indent=2), encoding='utf-8')
print('Captured', len(captured), 'prompt pairs')
