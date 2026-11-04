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

    def section(title, value, loc, doc):
        f, a, b = loc
        relative = Path(os.path.relpath(root/f, (root/doc).parent)).as_posix()
        manifest['parts'].append(dict(document=doc, label=title, source_spans=[loc]))
        return f'\n## {title}\n\n【来源：{title}｜[{f} 第{a}—{b}行](<{relative}#L{a}>)】\n\n```text\n{value.strip()}\n```\n'

    for cls in (FeedbackAddAgent, FeedbackReplaceAgent, FeedbackRemoveAgent):
        agent = cls(None, 'offline')
        name = 'feedback_' + agent.stage
        file = f'karma/agents/{name}/agent.py'
        filename = cls.__name__.replace('Feedback','') + '_完整Prompt.md'
        doc = f'karma/agents/{name}/{filename}'
        context = {'stage': agent.stage, 'feedback_scope':'sentence', 'source_sentences':[{'sentence_id':'S1','text':'The module processes data.'}],
                   'current_collection':{'version':'V0','triples':[]},
                   'handoff':[{'indices':[],'source_sentence_ids':['S1'],'problem':'检查源句中的关系'}]}
        with patch.object(agent, '_make_llm_call', return_value=('{}',0,0,0)) as call:
            agent.process(copy.deepcopy(context))
        assert call.call_count == 1
        captured = agent.last_call['messages']
        assert captured[0]['content'] == call.call_args.kwargs['system_prompt']
        assert captured[1]['content'] == call.call_args.args[0]
        marker = '{json.dumps(context, ensure_ascii=False, indent=2)}'
        data = json.dumps(context, ensure_ascii=False, indent=2)
        template = captured[1]['content'].replace('<feedback_input_json>\n'+data+'\n</feedback_input_json>',
                                                   '<feedback_input_json>\n'+marker+'\n</feedback_input_json>')
        assert template != captured[1]['content']
        assert template.replace(marker,data) == captured[1]['content']
        # A second business payload confirms that fixed text is not accidentally redacted.
        alternate = {'stage':agent.stage,'different_data':'sentinel-two','handoff':context['handoff']}
        assert template.replace(marker,json.dumps(alternate,ensure_ascii=False,indent=2)) == agent.build_messages(alternate)[1]['content']
        title = {'add':'遗漏补充','replace':'已有表达修正与拆分','remove':'重复清理'}[agent.stage]
        status = f'当前反馈阶段调用：{title}。默认每句独立执行 Add → Replace → Remove，再汇总整篇；feedback_scope=document 为整篇调用，固定提示相同。历史共享来源条目无法安全分组时显式回退整篇。每句有尚未投递到 Add/Replace 的问题时最多再执行一轮相关阶段。投递成功不代表语义问题已解决。'
        text = f'# {title} Agent 完整 Prompt\n\n2026-11-04。当前运行版本；固定提示全部展开，只有业务输入使用源码表达式表示。示例是固定 few-shot，不是历史运行日志。\n\n{status}\n'
        text += section('System 消息', captured[0]['content'], location(file,'SYSTEM_PROMPT'),doc)
        for part_title,value in agent.prompt_parts(context):
            owner, symbol = {'表达要求':(shared,'COMMON_RULES'),'执行步骤':(file,'TASK_PROMPT'),
                             '本阶段输出':(file,'OUTPUT_RULES'), '示例':(file,'EXAMPLES')}[part_title]
            text += section('User 消息：'+part_title,value,location(owner,symbol),doc)
        input_part = '# 本次输入\n<feedback_input_json>\n'+marker+'\n</feedback_input_json>'
        text += section('User 消息：本次数据',input_part,location(shared,'build_messages'),doc)
        text += '\n## 输入字段及来源\n\n'
        text += '输入由 [karma/core/feedback_pipeline.py](../../core/feedback_pipeline.py) 的 process/run 构造。逐句调度见 [sentence_feedback_pipeline.py](../../core/sentence_feedback_pipeline.py)。feedback_scope 标明范围；sentence 模式的 source_sentences 仅含当前原句，index 是本句当前编号；document 模式为整篇。current_collection 是前一步实际输出；sentence_index 是源句到当前 index 的对应表；unassigned_indices 列出未定位来源的旧条目；comparison_bundle 始终标明原始差异来自 V0；applied_change_log 是实际修改与失败记录的精简版，不含评分或完整历史操作协议；handoff 仅包含交给本阶段且尚未成功投递的问题，indices 已对应当前集合；内部 id、投递状态和历史编号留在程序审计记录中。收到的问题在阶段一核对，模型仅输出本阶段操作及新的转交问题。candidate_entities 仅辅助定位。repair_pass 标记是否为有限返修。\n'
        text += '\n每项 replace 的 new_triples 可以包含多条；替换批次失败时保留该步输入。Remove 对完整集合自主判断重复与保留项。无法修复或有歧义的条目记录 review，保持可追查。\n'
        (root/doc).write_text(text,encoding='utf-8')
        out = (root/doc).parent/'Prompt完整模板.json'
        messages=[captured[0],{'role':'user','content':template}]
        document_context = dict(context, feedback_scope='document')
        with patch.object(agent, '_make_llm_call', return_value=('{}',0,0,0)) as doc_call:
            agent.process(document_context)
        assert template.replace(marker,json.dumps(document_context,ensure_ascii=False,indent=2)) == doc_call.call_args.args[0]
        empty_context = dict(context, handoff=[])
        with patch.object(agent, '_make_llm_call', return_value=('{}',0,0,0)) as empty_call:
            agent.process(empty_context)
        empty_data = json.dumps(empty_context, ensure_ascii=False, indent=2)
        empty_template = empty_call.call_args.args[0].replace('<feedback_input_json>\n'+empty_data+'\n</feedback_input_json>',
                                  '<feedback_input_json>\n'+marker+'\n</feedback_input_json>')
        assert empty_template == template  # Hints change only business data, not fixed instructions.
        assert empty_template.replace(marker, empty_data) == empty_call.call_args.args[0]
        out.write_text(json.dumps({'historical_run':False,'examples':[{'section':title,'condition':'sentence/document 及空/非空 handoff 的固定提示相同','messages':messages}]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        manifest['documents'].append(doc)
        manifest['message_examples'].append(out.relative_to(root).as_posix())
        names[name]=filename
        statuses[name]=status
    return names,statuses
