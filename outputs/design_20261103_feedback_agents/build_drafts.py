"""Build review drafts only; these prompts are not connected to the pipeline."""
from pathlib import Path
import hashlib
import json
from draft_content import COMMON, INPUTS, OUTPUT, TASKS, SYSTEMS, FEWSHOTS

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'karma/agents/relationship_extraction/agent.py'
def link(a,b):
    return f'[karma/agents/relationship_extraction/agent.py 第{a}—{b}行](../../karma/agents/relationship_extraction/agent.py#L{a})'

SCORES='''# 新三元组的评分
先检查源句是否支持这条完整三元组，再给 confidence、clarity、relevance 打分，范围为 0.0 到 1.0。
confidence：源句对这条陈述的支持程度。原文说“可能”，三元组也保留“可能”，不因此降低支持程度。
clarity：主体、关系和客体是否清楚。短语较长不等于表达不清楚。
relevance：这项事实与文档主题的相关程度。相关程度低不等于没有原文依据。
发现错误先修正，不用低分代替修正；没有依据的新事实不输出。
三个分数分别判断，示例中的数值只展示格式，不要求沿用。
'''

manifest={'status':'proposal_not_runtime','revision':2,'date':'2026-11-03','source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'agents':{}}
for role in TASKS:
    system=SYSTEMS[role]+' 完整回复采用 User 指定的 JSON 结构。'
    parts=[('共同规则',COMMON,f'用直白表述改写自 {link(197,208)}、{link(223,276)}、{link(297,311)}；自主检查和历史差异说明是拟新增内容。'),
           ('本阶段步骤',TASKS[role],f'分配及改写自 {link(251,264)}、{link(279,333)}；Replace 一条换多条是新的拟定输出方式。')]
    if role!='Remove':parts.append(('评分',SCORES,f'按原意改写自 {link(57,68)}。'))
    parts.extend([('本次输入',INPUTS,'拟新增输入说明；花括号为待实现的数据变量。'),
                  ('输出格式',OUTPUT,f'由 {link(441,477)} 重写；replace.new_triples 尚未接入现有程序。'),
                  ('完整输入输出示例',FEWSHOTS[role],f'参考 {link(335,391)} 并增加本次讨论的情况；演示数据，不是历史运行记录。')])
    user='\n\n'.join(p[1].strip() for p in parts)
    md=f'# {role} Agent Prompt 草案（第 2 版）\n\n2026-11-03。设计稿，尚未接入运行。每条 replace 直接包含一条或多条新三元组，拆分结果无需另外输出 add。\n\n[分配与案例核查](反馈Prompt分配与案例核查.md)\n\n## System 消息\n\n来源：任务说明｜由 {link(481,484)} 改写。\n\n```text\n{system}\n```\n'
    for title,text,source in parts:
        md+=f'\n## User 消息：{title}\n\n来源：{title}｜{source}\n\n```text\n{text.strip()}\n```\n'
    (OUT/f'{role}Agent_Prompt草案.md').write_text(md,encoding='utf-8')
    manifest['agents'][role]={'status':'proposal_not_runtime','messages':[{'role':'system','content':system},{'role':'user','content':user}]}
(OUT/'Prompt草案模板.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Generated three revised draft prompts and JSON templates. Runtime unchanged.')
