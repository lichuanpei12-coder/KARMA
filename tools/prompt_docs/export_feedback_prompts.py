"""Export actual feedback messages with dynamic context replaced by its expression."""
import ast
import copy
import json
import os
from pathlib import Path
from unittest.mock import patch

from karma.agents.feedback_add.agent import FeedbackAddAgent
from karma.agents.feedback_replace.agent import FeedbackReplaceAgent
from karma.agents.feedback_remove.agent import FeedbackRemoveAgent
from karma.core.data_structures import KnowledgeTriple
from karma.core.triple_overlap import rank_triple_overlap


def export_feedback(root, manifest):
    names, statuses = {}, {}
    shared = 'karma/agents/feedback_common.py'

    def location(file, symbol):
        tree = ast.parse((root/file).read_text(encoding='utf-8'))
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == symbol for t in n.targets):
                return (file, n.lineno, n.end_lineno)
            if isinstance(n, ast.FunctionDef) and n.name == symbol:
                return (file, n.lineno, n.end_lineno)
        raise ValueError((file, symbol))

    def section(title, value, locations, doc):
        links = []
        for file, start, end in locations:
            relative = Path(os.path.relpath(root/file, (root/doc).parent)).as_posix()
            links.append(f'[{file} 第{start}—{end}行](<{relative}#L{start}>)')
        manifest['parts'].append(dict(document=doc, label=title, source_spans=locations))
        source = ' · '.join(links)
        return f'\n### {title}\n\n【来源：{title}｜{source}】\n\n```text\n{value.strip()}\n```\n'

    def capture(agent, context):
        with patch.object(agent, '_make_llm_call', return_value=('{}',0,0,0)) as call:
            agent.process(copy.deepcopy(context))
        assert call.call_count == 1
        messages = agent.last_call['messages']
        assert messages[0]['content'] == call.call_args.kwargs['system_prompt']
        assert messages[1]['content'] == call.call_args.args[0]
        return messages

    for cls in (FeedbackAddAgent, FeedbackReplaceAgent, FeedbackRemoveAgent):
        agent = cls(None, 'offline')
        name = 'feedback_' + agent.stage
        file = f'karma/agents/{name}/agent.py'
        filename = cls.__name__.replace('Feedback','') + '_完整Prompt.md'
        doc = f'karma/agents/{name}/{filename}'
        title = {'add':'遗漏补充','replace':'已有表达修正与拆分','remove':'重复清理'}[agent.stage]
        status = f'当前反馈阶段调用：{title}。逐句模式下每句独立执行 Add、Replace、Remove。整篇模式下按该篇处理文本选择语言。系统提示和输出协议在两种语言间共用。'
        text = f'# {title} Agent 完整 Prompt\n\n{status}\n'
        language = location('karma/agents/prompt_language.py', 'uses_chinese_prompt')
        text += (f'\n中文与英文各展示一套实际发送的 System 和 User。语言按当前源句决定。'
                 f' [语言选择源码](../prompt_language.py#L{language[1]})\n')
        templates = []
        for language_name, source, alternate in (
            ('英文', 'The tray holds the sample.', 'The lid covers the tray.'),
            ('中文', '气压不足时，装置会暂停输送。', '压力恢复后，装置会重新启动。'),
        ):
            sample = {'sentence_id':'S1','text':source}
            context = {'stage': agent.stage, 'source_sentences':[sample],
                       'current_collection':{'version':'V0','triples':[]}}
            if agent.stage == 'remove':
                triples = [KnowledgeTriple('The tray', 'holds', 'the sample', source_sentence_ids=['S1'])
                           if language_name == '英文' else
                           KnowledgeTriple('气压不足时，装置', '会暂停', '输送', source_sentence_ids=['S1'])
                           for _ in range(2)]
                context['current_collection']['triples'] = [dict(index=i, **t.to_dict()) for i,t in enumerate(triples)]
                context['lexical_overlap'] = rank_triple_overlap(triples, 'V0')
            captured = capture(agent, context)
            marker = '{json.dumps(context, ensure_ascii=False, indent=2)}'
            data = json.dumps(context, ensure_ascii=False, indent=2)

            def verify_input(payload):
                actual = capture(agent, payload)
                assert actual[0] == captured[0]
                assert template.replace(marker, json.dumps(payload, ensure_ascii=False, indent=2)) == actual[1]['content']

            template = captured[1]['content'].replace(
                '<feedback_input_json>\n'+data+'\n</feedback_input_json>',
                '<feedback_input_json>\n'+marker+'\n</feedback_input_json>',
            )
            assert template != captured[1]['content']
            assert template.replace(marker, data) == captured[1]['content']
            verify_input(dict(context, source_sentences=[sample, {'sentence_id':'S2', 'text':alternate}]))
            verify_input(dict(context, source_sentences=[{'sentence_id':'S1', 'text':alternate}]))
            if agent.stage == 'remove':
                empty = dict(context, current_collection={'version':'V0','triples':[]},
                             lexical_overlap=rank_triple_overlap([], 'V0'))
                verify_input(empty)
            zh = language_name == '中文'
            task_locations = [location(file, 'TASK_PROMPT')]
            if agent.stage == 'replace':
                task_locations = [location(file, 'TASK_TEMPLATE'),
                                  location(file, 'CHINESE_TASK_PROMPT' if zh else 'TASK_PROMPT')]
            elif zh and agent.chinese_task_prompt:
                task_locations = [location(file, 'CHINESE_TASK_PROMPT')]
            part_locations = {
                '执行步骤': task_locations,
                '表达要求': [location(shared,'CHINESE_EXPRESSION_RULES' if zh else 'ENGLISH_EXPRESSION_RULES'),
                             location(shared,'COMMON_RULES')],
                '本阶段输出': [location(shared,'OUTPUT_RULES')],
                '示例': [location(file,'CHINESE_EXAMPLES' if zh else 'EXAMPLES')],
            }
            text += f'\n## {language_name}输入\n'
            text += section('System 消息', captured[0]['content'], [location(file,'SYSTEM_PROMPT')], doc)
            for part_title, value in agent.prompt_parts(context):
                text += section('User 消息 · '+part_title, value, part_locations[part_title], doc)
            input_part = '# 本次输入\n<feedback_input_json>\n'+marker+'\n</feedback_input_json>'
            text += section('User 消息 · 本次数据', input_part, [location(shared,'build_messages')], doc)
            templates.append({
                'section': f'{title} · {language_name}',
                'condition': f'源句选用{language_name}提示。逐句和整篇共用固定提示。',
                'messages': [captured[0], {'role':'user','content':template}],
            })
        text += '\n## 输入字段及来源\n\n'
        text += '输入由 [karma/core/feedback_pipeline.py](../../core/feedback_pipeline.py) 的 process 构造。逐句调度见 [sentence_feedback_pipeline.py](../../core/sentence_feedback_pipeline.py)。范围由程序筛选输入，模型不接收 feedback_scope 字段或模式说明；逐句模式的 source_sentences 仅含当前原句，index 是本句当前编号；整篇模式输入整篇材料。current_collection 是前一步实际输出；sentence_index 是源句到当前 index 的对应表；unassigned_indices 列出未定位来源的旧条目；comparison_bundle 始终标明原始差异来自 V0；applied_change_log 是实际修改与失败记录的精简版，不含评分或完整历史操作协议。candidate_entities 仅辅助定位。\n'
        text += '\n每个 Agent 对核实的问题在当次回复中给出必要的新增、替换、拆分或删除。涉及输入编号的操作作为一组执行，编号冲突或操作无效时保留原输入。Add 只做独立新增时可分别接受有效条目。审计按阶段记录实际操作与失败原因。\n'
        if agent.stage == 'remove':
            f, a, b = location('karma/core/triple_overlap.py', 'rank_triple_overlap')
            text += f'\n词重合排序来源：[{f} 第{a}—{b}行](../../core/triple_overlap.py#L{a})。\n'
            _, token_line, _ = location('lexical_tokens.py', 'overlap_tokens')
            text += 'lexical_overlap 在每次 Remove 调用前由当前集合重算，basis_version 对应 current_collection.version。pairs 以编号顺序列出全部 n(n−1)/2 对，每对出现一次，含零重合项，无阈值和数量截断。每对分别提供 overall_rank、containment_rank，同分同排名；模型重点检查任一排名靠前的条目对，再覆盖其余条目。\n'
            text += f'Remove 和宽松评估共用 [字词切分函数](../../../lexical_tokens.py#L{token_line})。每个汉字计一次，其余文本转小写后按空白和汉字边界切分。Remove 合并 head、relation、tail 后计数，宽松评估按对应字段计数。令两条计数单位总数为 A、B，重合数为 C，overlap_f1=2C/(A+B)，left_containment=C/A，right_containment=C/B，空分母计 0。包含排名使用两侧包含率的较大值。事实判断依据源句、字段角色和限定归属。\n'
        (root/doc).write_text(text,encoding='utf-8')
        out = (root/doc).parent/'Prompt完整模板.json'
        out.write_text(json.dumps({'historical_run':False,'examples':templates},
                                  ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        manifest['documents'].append(doc)
        manifest['message_examples'].append(out.relative_to(root).as_posix())
        names[name]=filename
        statuses[name]=status
    return names,statuses
