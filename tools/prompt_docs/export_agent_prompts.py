"""Export every agent's prompt with source spans and explicit runtime branches."""
import ast
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT))
from karma.agents.ingestion.agent import IngestionAgent
from karma.agents.reader.agent import ReaderAgent
from karma.agents.summarizer.agent import SummarizerAgent
from karma.agents.entity_extraction.agent import EntityExtractionAgent
from karma.agents.relationship_extraction.agent import RelationshipExtractionAgent
from karma.agents.triple_splitting.agent import TripleSplittingAgent
from karma.agents.text_generation.agent import TextGenerationAgent
from karma.agents.text_comparison.agent import TextComparisonAgent
from karma.core.data_structures import KGEntity,KnowledgeTriple
from karma.core.sentence_groups import grouped_difference_context,unassigned_group_note

captured={'grouped':{},'non_grouped':{}}
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
SOURCE='The module processes data.'
triples=[KnowledgeTriple('The module','processes','data',source_sentence_ids=['S1'])]
entities=[KGEntity('example_module','Component','The module')]
sentences=[dict(sentence_id='S1',text=SOURCE)]

def cap(a,action,response):
    with patch.object(a,'_make_llm_call',return_value=(response,0,0,0)) as call:
        action()
    assert call.call_count==1
    return dict(system=call.call_args.kwargs.get('system_prompt') or a.system_prompt,user=call.call_args.args[0])

for variant in ['normal','legacy_difference']:
    groups=[dict(sentence_id='S1',text=SOURCE,triples=[dict(index=0,head='The module',relation='processes',tail='data',source_sentence_ids=['S1'])])]
    recon=[dict(sentence_id='S1',text_b=SOURCE,generation_status='generated',triple_indices=[0])]
    diff=dict(unique_to_text_a=[],unique_to_text_b=[],sentence_differences=[dict(recon[0],text_a=SOURCE,unique_to_text_a=[],unique_to_text_b=[],comparison_status='compared')])
    if variant=='legacy_difference':diff.pop('sentence_differences')
    calls={}
    a=TextGenerationAgent(None,'offline')
    calls['generation']=cap(a,lambda:a.process(copy.deepcopy(triples),sentence_groups=groups,scope='sentence'),'[{"sentence_id":"S1","text":"The module processes data."}]')
    a=TextComparisonAgent(None,'offline')
    calls['comparison']=cap(a,lambda:a.process(SOURCE,SOURCE,sentence_groups=groups,reconstructions=recon,scope='sentence'),'[{"sentence_id":"S1","unique_to_text_a":[],"unique_to_text_b":[]}]')
    a=EntityExtractionAgent(None,'offline')
    calls['entity_feedback']=cap(a,lambda:a.revise_entities(SOURCE,entities,copy.deepcopy(triples),diff),'[]')
    captured['grouped'][variant]=calls

for agent_class, key in ((TextGenerationAgent,'generation'),(TextComparisonAgent,'comparison')):
    a=agent_class(None,'offline')
    if key=='generation':
        document_call=cap(a,lambda:a.process(triples,sentence_groups=groups,scope='document'),'[{"sentence_id":"S1","text":"The module processes data."}]')
    else:
        document_call=cap(a,lambda:a.process(SOURCE,SOURCE,sentence_groups=groups,reconstructions=recon,scope='document'),'[{"sentence_id":"S1","unique_to_text_a":[],"unique_to_text_b":[]}]')
    assert document_call==captured['grouped']['normal'][key]

a=TextGenerationAgent(None,'offline')
captured['non_grouped']['generation']=cap(a,lambda:a.process(copy.deepcopy(triples)),SOURCE)
a=TextComparisonAgent(None,'offline')
captured['non_grouped']['comparison']=cap(a,lambda:a.process(SOURCE,SOURCE),'{"unique_to_text_a":[],"unique_to_text_b":[]}')

new={}
a=IngestionAgent(None,'offline');new['ingestion']=cap(a,lambda:a._extract_metadata(SOURCE),'{}')
a=ReaderAgent(None,'offline');new['reader']=cap(a,lambda:a._batch_score_relevance([dict(text=SOURCE,section='content')]),'0.8')
a=SummarizerAgent(None,'offline');new['summarizer']=cap(a,lambda:a._summarize_single_segment(SOURCE),SOURCE)
a=EntityExtractionAgent(None,'offline');new['entity_first']=cap(a,lambda:a.process([SOURCE]),'[]')
a=RelationshipExtractionAgent(None,'offline');new['relationship_first']=cap(a,lambda:a.process([SOURCE],entities,sentences=sentences),'[]')
a=TripleSplittingAgent(None,'offline');new['splitting']=cap(a,lambda:a.process(SOURCE,copy.deepcopy(triples)),'{"add":[],"remove":[],"replace":[]}')

def path(agent):return f'karma/agents/{agent}/agent.py'
sources={p.as_posix():p.read_text(encoding='utf-8-sig').splitlines() for p in (ROOT/'karma/agents').glob('*/agent.py')}
for extra in ['karma/core/sentence_groups.py','karma/core/pipeline.py','karma/agents/feedback_common.py','karma/core/sentence_feedback_pipeline.py','karma/core/feedback_pipeline.py','karma/core/base_agent.py','karma/core/api_retry.py']:
    sources[(ROOT/extra).as_posix()]=(ROOT/extra).read_text(encoding='utf-8').splitlines()
trees={p:ast.parse('\n'.join(lines)) for p,lines in sources.items()}
def scope(filename,name):
    tree=trees[(ROOT/filename).as_posix()]
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name:return (filename,n.lineno,n.end_lineno)
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets):return (filename,n.lineno,n.end_lineno)
    raise ValueError((filename,name))
def pipeline_call(attribute):
    tree=trees[(ROOT/'karma/core/pipeline.py').as_posix()]
    for n in ast.walk(tree):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute):
            obj=n.func.value
            if isinstance(obj,ast.Attribute) and obj.attr==attribute:
                return ('karma/core/pipeline.py',n.lineno,n.end_lineno)
    raise ValueError(attribute)

def pipeline_line(fragment):
    lines=sources[(ROOT/'karma/core/pipeline.py').as_posix()]
    n=next(i for i,l in enumerate(lines,1) if fragment in l)
    return ('karma/core/pipeline.py',n,n)

def ref(loc):
    f,a,b=loc
    return f'{f} 第{a}'+(f'—{b}行' if b!=a else '行')

def source_line(title,locs,doc):
    by_file={}
    for f,a,b in locs:by_file.setdefault(f,[]).append((a,b))
    links=[]
    for f,spans in by_file.items():
        relative=Path(os.path.relpath(ROOT/f,(ROOT/doc).parent)).as_posix()
        lines='、'.join(str(a) if a==b else f'{a}—{b}' for a,b in spans)
        links.append('['+f+' 第'+lines+'行](<'+relative+'#L'+str(spans[0][0])+'>)')
    return '【来源：'+title+'｜'+'；'.join(links)+'】'
def const_system(agent):
    f=path(agent);tree=trees[(ROOT/f).as_posix()]
    n=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='system_prompt' for t in n.targets))
    return ast.literal_eval(n.value)
def display_text(t):
    # Only tighten blank lines for documentation; prompt wording remains intact.
    lines=t.strip('\n\r').splitlines()
    result=[]
    for line in lines:
        if not line.strip():
            if result and result[-1]!='':result.append('')
        else:result.append(line)
    while result and result[-1]=='':result.pop()
    return '\n'.join(result)
def code(t):return '```text\n'+display_text(t)+'\n```\n\n'

def prompt_markdown(text):
    """Keep source links outside fenced blocks so Markdown renders them blue."""
    output=[];body=[]
    def flush():
        if any(l.strip() for l in body):output.append(code('\n'.join(body)))
        body.clear()
    for line in text.splitlines():
        if line.startswith('【来源：') and line.endswith('】'):
            flush();output.append(line+'\n\n')
        elif line in ['【System 消息】','【User 消息】','【源码保留的 System】']:
            flush();output.append('**'+line.strip('【】')+'**\n\n')
        else:body.append(line)
    flush()
    return ''.join(output)
def table(h,rs):return '\n'.join(['| '+' | '.join(h)+' |','| '+' | '.join(['---']*len(h))+' |']+['| '+' | '.join(str(c).replace('|','\\|').replace('\n','<br>') for c in r)+' |' for r in rs])+'\n\n'

# Maps literal fragments back to their physical source lines. Dynamic fields map
# to the formatting expression in the owning function, rather than sample text.
def clean(line):
    s=line.strip()
    s=re.sub(r'^(?:[A-Za-z_][\w.]*\s*=\s*|return\s+)?f?"""','',s)
    s=re.sub(r'""".*$','',s)
    s=re.sub(r'^system_prompt="(.*)"\)\)?[,;]?$',r'\1',s)
    return s.replace('{{','{').replace('}}','}').strip()
TAG_TOKENS={k:k.upper() for k in ['source_text','source_sentences_json','sentence_groups_json','current_triples_json','candidate_entities_json','current_entities_json','text_difference_json','triple_groups_json','full_source_text','sentence_pairs_json']}
def redact(text):
    substitutions={}
    for tag,token in TAG_TOKENS.items():
        pattern=re.compile(r'(<'+tag+r'>\n)(.*?)(\n</'+tag+r'>)',re.S)
        found=list(pattern.finditer(text))
        if found:
            assert len(found)==1
            substitutions[token]=found[0][2]
            text=pattern.sub(lambda m:m[1]+'{{'+token+'}}'+m[3],text)
    return text,substitutions

def variable_template(text,pools):
    """Expand fixed instructions; represent only business input by source expressions."""
    original=text
    bindings={}
    for tag in TAG_TOKENS:
        pattern=re.compile(r'(<'+tag+r'>\n)(.*?)(\n</'+tag+r'>)',re.S)
        found=list(pattern.finditer(text))
        if not found:continue
        assert len(found)==1
        expression=None
        for filename,a,b in pools:
            nodes=[n for n in ast.walk(trees[(ROOT/filename).as_posix()]) if isinstance(n,ast.JoinedStr) and a<=n.lineno<=b]
            for node in nodes:
                for i,value in enumerate(node.values[:-1]):
                    if isinstance(value,ast.Constant) and isinstance(value.value,str) and value.value.endswith('<'+tag+'>\n') and isinstance(node.values[i+1],ast.FormattedValue):
                        expression=ast.unparse(node.values[i+1].value);break
                if expression:break
            if expression:break
        if not expression:
            expression={'triple_groups_json':'json.dumps(payload, ensure_ascii=False, indent=2)',
                        'sentence_pairs_json':'json.dumps(pairs, ensure_ascii=False, indent=2)',
                        'text_difference_json':'json.dumps(data, ensure_ascii=False, indent=2)',
                        'full_source_text':'text_a'}[tag]
        marker='{'+expression+'}'
        bindings[marker]=dict(tag=tag,value=found[0][2],expression=expression)
        text=pattern.sub(lambda m:m[1]+marker+m[3],text)
    rebuilt=text
    for marker,item in bindings.items():rebuilt=rebuilt.replace(marker,item['value'])
    assert rebuilt==original
    return text,bindings
def locations(fragment,pools):
    # Source locations point to the interpolation expression, not to synthetic data.
    fragment,_=redact(fragment)
    hits={}
    for line in fragment.splitlines():
        value=line.strip()
        if not value or not re.search(r'[A-Za-z\u4e00-\u9fff]',value):continue
        if re.fullmatch(r'\{\{[A-Z_]+\}\}',value):
            token=value[2:-2]
            tag=next((tag for tag,t in TAG_TOKENS.items() if t==token),None)
            if tag:
                found=False
                for f,a,b in pools:
                    lines=sources[(ROOT/f).as_posix()]
                    for i in range(a,b+1):
                        if '<'+tag+'>' in lines[i-1]:
                            # Dedicated formatter may put its JSON expression below the delimiter.
                            end=next((j for j in range(i,b+1) if '</'+tag+'>' in lines[j-1]),i)
                            hits.setdefault(f,[]).extend([i,end]);found=True;break
                    if found:break
                if found:continue
        found=False
        for f,a,b in pools:
            lines=sources[(ROOT/f).as_posix()]
            exact=[i for i in range(a,b+1) if clean(lines[i-1])==value]
            if not exact:
                exact=[i for i in range(a,b+1) if len(value)>10 and value in lines[i-1].replace('{{','{').replace('}}','}')]
            if exact:
                hits.setdefault(f,[]).append(exact[0]);found=True;break
        # Variable expressions and inserted data have no literal source counterpart.
        if not found and '{{' in value:
            exprs={'DOCUMENT_TEXT':'{sample_text}','FORMATTED_SEGMENTS':'{chr(10).join(segment_texts)}',
                   'INPUT_TEXT':'{text}','LINEARIZED_TRIPLES':'{linearized_triples}',
                   'TEXT_A':'{text_a}','TEXT_B':'{text_b}'}
            expr=exprs.get(value.strip('{}'))
            for f,a,b in pools:
                positions=[i for i in range(a,b+1) if expr and expr in sources[(ROOT/f).as_posix()][i-1]]
                if positions:
                    hits.setdefault(f,[]).append(positions[0]);found=True;break
            if not found:
                f,a,b=pools[0];hits.setdefault(f,[]).extend([a,b])
    if not hits:
        return pools[:1],True
    spans=[]
    for f,ns in hits.items():
        ordered=sorted(set(ns));start=end=ordered[0]
        for n in ordered[1:]:
            if n-end<=3:end=n
            else:spans.append((f,start,end));start=end=n
        spans.append((f,start,end))
    return spans,False

manifest=dict(git_head=head,documents=[],parts=[],source_files={},message_examples=[])
def annotated(label,text,pools,doc):
    # Split at semantic headings, keeping each heading with its expanded body.
    chunks=re.split(r'(?=^[ \t]*#{1,3}[ \t]+\S)',text,flags=re.M)
    assert ''.join(chunks)==text
    merged=[];pending=''
    for chunk in chunks:
        pending+=chunk
        meaningful=[line for line in pending.splitlines() if line.strip() and not re.match(r'^[ \t]*#{1,3}[ \t]+',line)]
        if meaningful:merged.append(pending);pending=''
    if pending:
        if merged:merged[-1]+=pending
        else:merged.append(pending)
    chunks=merged
    assert ''.join(chunks)==text
    output=''
    i=0
    for c in chunks:
        if not c.strip():continue
        i+=1
        first=next(line.strip() for line in c.splitlines() if line.strip())
        part_title=re.sub(r'^#{1,3}\s*','',first) if first.startswith('#') else '任务说明'
        if label=='System Prompt' and part_title=='抽取规则':part_title+='（展开 FACT_RULES）'
        locs,fallback=locations(c,pools)
        output+=source_line(part_title,locs,doc)+'\n'+display_text(c)+'\n\n'
        manifest['parts'].append(dict(document=doc,label=label,part=i,title=part_title,source_spans=locs,assembly_range=fallback))
        assert any(line.strip() and not re.match(r'^\s*#{1,3}\s+',line) for line in c.splitlines())
    cleaned=re.sub(r'^【来源：[^\n]*】\n','',output,flags=re.M)
    assert [l for l in cleaned.splitlines() if l.strip()]==[l for l in text.splitlines() if l.strip()]
    return output

GROUPHELP=[scope('karma/core/sentence_groups.py','grouped_difference_context')]
def pools(agent,method,system=False):
    f=path(agent)
    out=[scope(f,method)]
    if agent=='entity_extraction':out += [scope(f,'ENTITY_RULES'),scope(f,'_output_instructions'),scope(f,'difference_context')]+GROUPHELP
    if agent=='relationship_extraction':out += [scope(f,'FACT_RULES')]
    return out

STATUS={
'ingestion':'当前process只做文本规范化，_extract_metadata调用已注释，metadata=None；下面完整prompt属于保留但未由当前process调用的元数据入口。',
'reader':'普通文档准备阶段会分批调用相关性评分，每批最多5段；回放已保存基线时可能跳过准备阶段。每段送给评分的文本目前截取前500字符并加省略号。',
'summarizer':'当前pipeline默认跳过摘要；仅环境变量KARMA_USE_SUMMARIZER为非空值时启用。直接调用摘要方法且输入长度小于15字符时，也不调用模型。',
'entity_extraction':'当前pipeline第一轮执行实体抽取，第二轮执行实体反馈。两轮共用同一System，但User不同；每次调用只使用对应轮次的一套消息。',
'relationship_extraction':'当前仅执行第一轮基线关系抽取。第二轮关系反馈已移到 feedback_add、feedback_replace、feedback_remove，由 FeedbackPipeline 依次调用。三元组分数由程序固定填入0.8，模型只输出事实和证据。',
'triple_splitting':'拆分阶段通过process调用专用System和User；只生成add/replace；程序兼容旧响应中的空remove。回放或跳过阶段时是否执行，以实际入口为准。',
'text_generation':'当前pipeline默认text_scope=sentence，由generate_sentences逐句调用generate_grouped，每次只传一个分组。text_scope=document时一次传入全部分组；两种模式固定System和User相同，仅输入范围不同。另一条generate_text路径只在不传分组或直接调用时使用，不会同时发送。',
'text_comparison':'当前pipeline默认text_scope=sentence，由compare_sentences逐句调用compare_grouped，每次只传对应源句及重建文本；全文标签也仅包含本句。text_scope=document时一次传入全部分组。两种模式固定提示相同，仅输入范围不同。另一条compare路径只在不传分组或直接调用时使用，不会与当前版本叠加。',
'conflict_resolution':'当前process执行Python矛盾关系和置信度比较规则，不调用模型。源码定义了System字符串，但当前没有实际发送的User或模型请求。',
'evaluator':'当前process执行Python加权评分和阈值筛选，不调用模型。源码System字符串不参与运行决策；实际逻辑以finalize_triples和_aggregate_scores为准，不能把字符串里的最低分条件当成已执行检查。',
'schema_alignment':'当前pipeline中初始化和调用均被注释。即使单独调用该类，现有process也是Python类型/关系映射，没有模型调用；定义的System不代表当前生效。',
}
NAMES={'ingestion':'摄入Agent_完整Prompt.md','reader':'阅读Agent_完整Prompt.md','summarizer':'摘要Agent_完整Prompt.md','entity_extraction':'实体抽取Agent_完整Prompt.md','relationship_extraction':'关系抽取Agent_完整Prompt.md','triple_splitting':'拆分Agent_完整Prompt.md','text_generation':'重建文本Agent_完整Prompt.md','text_comparison':'文本对比Agent_完整Prompt.md','conflict_resolution':'冲突处理Agent_完整Prompt.md','evaluator':'评估Agent_完整Prompt.md','schema_alignment':'模式对齐Agent_完整Prompt.md'}

for agent,filename in NAMES.items():
    target=ROOT/'karma/agents'/agent/filename
    f=path(agent)
    doc=target.relative_to(ROOT).as_posix()
    t=f'# {filename[:-3]}\n\n整理日期：2026-11-04。代码版本：`{head}`。行号对应整理时源码；后续修改源码后应重新导出。\n\n'
    t+='## 当前运行是否使用这套Prompt\n\n'+STATUS[agent]+'\n\n'
    t+=source_line('调用入口与System/User发送',[scope(f,'process'),scope('karma/core/base_agent.py','_make_llm_call')],doc)+'\n\n'
    t+='Chat Completions 与 Responses 使用同一套 System/User 内容，底层调用共用持续重试机制。\n\n'
    if agent in ['text_generation','text_comparison']:
        t+='当前流水线传参位置：'+ref(pipeline_call('text_generation_agent' if agent=='text_generation' else 'text_comparison_agent'))+'。**当前流程只选择分组版本；附录中的非分组版本不会一起执行。**\n\n'
    if agent=='ingestion':t+='元数据调用被注释的位置：'+ref(scope(f,'process'))+'。\n\n'
    if agent=='summarizer':t+='摘要开关：'+ref(pipeline_line('KARMA_USE_SUMMARIZER'))+'。\n\n'
    if agent=='schema_alignment':t+='未启用位置：'+ref(pipeline_line('# self.schema_alignment_agent ='))+'；'+ref(pipeline_line('# aligned_entities, aligned_relationships ='))+'。\n\n'
    t+='## 展示说明\n\n固定文本全部展开，仅运行数据用源码变量或表达式表示。每个入口保留一份按顺序排列的System和User；每部分前用一行相对路径链接标注来源，可点击查看源码。来源链接放在代码块外以保持蓝色显示。“【来源：…】”和消息角色标记只用于阅读。同目录[Prompt完整模板.json](Prompt完整模板.json)保存不含阅读标注的角色结构。\n\n'
    message_examples=[]
    variants=[]
    if agent in ['ingestion','reader','summarizer']:
        method={'ingestion':'_extract_metadata','reader':'_batch_score_relevance','summarizer':'_summarize_single_segment'}[agent]
        c=copy.deepcopy(new[agent])
        value='Segment 1:\n'+SOURCE+'...' if agent=='reader' else SOURCE
        expression={'ingestion':'sample_text','reader':'chr(10).join(segment_texts)','summarizer':'text'}[agent]
        c['user']=c['user'].replace(value,'{'+expression+'}')
        variants.append(('当前条件下的完整版本' if agent!='ingestion' else '保留入口的完整版本（当前process未调用）',c,pools(agent,'__init__'),pools(agent,method)))
    elif agent in ['entity_extraction','relationship_extraction']:
        entity=agent=='entity_extraction'
        key='entity' if entity else 'relationship'
        variants.append(('第一轮：基线抽取',new[key+'_first'],pools(agent,'__init__'),pools(agent,'_extract_entities_from_text' if entity else '_extract_relationships_from_text')))
        if entity:
            method='revise_entities'
            variants.append(('第二轮：反馈修订',captured['grouped']['normal'][key+'_feedback'],pools(agent,'__init__'),pools(agent,method)))
    elif agent=='triple_splitting':variants.append(('拆分阶段完整版本',new['splitting'],pools(agent,'process'),pools(agent,'process')))
    elif agent in ['text_generation','text_comparison']:
        key='generation' if agent=='text_generation' else 'comparison'
        method='generate_grouped' if key=='generation' else 'compare_grouped'
        wrapper='generate_sentences' if key=='generation' else 'compare_sentences'
        t+=source_line('逐句入口与调度', [scope(f,wrapper),pipeline_call(agent+'_agent')],doc)+'\n\n'
        variants.append(('当前默认：逐句调用（整篇模式复用相同固定提示）',captured['grouped']['normal'][key],pools(agent,method),pools(agent,method)))
        c=copy.deepcopy(captured['non_grouped'][key])
        if key=='generation':c['user']=c['user'].replace('The module : processes : data','{linearized_triples}')
        else:c['user']=c['user'].replace('文本A：\n'+SOURCE,'文本A：\n{text_a}').replace('文本B：\n'+SOURCE,'文本B：\n{text_b}')
        variants.append(('附录：当前pipeline不使用的非分组入口',c,pools(agent,'__init__'),pools(agent,'_build_generation_prompt' if key=='generation' else '_build_comparison_prompt')))
    else:
        variants.append(('源码保留的System（当前不会发送给模型）',dict(system=const_system(agent),user=''),pools(agent,'__init__'),[]))
    for title,c,sp,up in variants:
        user,bindings=variable_template(c['user'],up) if c['user'] else ('',{})
        reconstructed=user
        for marker,item in bindings.items():reconstructed=reconstructed.replace(marker,item['value'])
        assert reconstructed==c['user']
        message_examples.append(dict(section=title,data_origin='固定文本完整展开，仅运行数据保留源码变量表达式',
                                     messages=[dict(role='system',content=c['system']),dict(role='user',content=user)] if c['user'] else [],
                                     declared_system=c['system'] if not c['user'] else None))
        t+='## '+title+'\n\n'
        system_display=annotated('System Prompt',c['system'],sp,doc)
        if user:
            user_display=annotated('User Prompt',user,up,doc)
            t+=prompt_markdown('【System 消息】\n'+system_display+'【User 消息】\n'+user_display)
            if bindings:t+='动态数据位置：\n\n'+table(['源码变量/表达式','输入位置'],[(item['expression'],item['tag']) for item in bindings.values()])
            assert not re.search(r'\{\{[A-Z_]+\}\}',c['user'])
        else:t+=prompt_markdown('【源码保留的 System】\n'+system_display)+'当前没有User Prompt，也没有_make_llm_call调用。该类实际行为由'+ref(scope(f,'process'))+'及其调用的Python方法决定。\n\n'
    if agent in ['text_generation','text_comparison','entity_extraction']:
        t+='## 条件说明：UNASSIGNED出现时才添加\n\n此句由'+ref(scope('karma/core/sentence_groups.py','unassigned_group_note'))+'返回：\n\n'+code(unassigned_group_note([dict(sentence_id='UNASSIGNED')]).rstrip('\n'))
        if agent=='entity_extraction':
            t+='差异块的插入位置见'+ref(scope('karma/core/sentence_groups.py','grouped_difference_context'))+'。'
            t+='\n\n'
        else:t+='插入到当前分组User的业务输入标签之前，拼接位置见'+ref(scope(f,'generate_grouped' if agent=='text_generation' else 'compare_grouped'))+'。\n\n'
    if agent=='entity_extraction':
        key='entity_feedback'
        u,_=variable_template(captured['grouped']['legacy_difference'][key]['user'],[scope(f,'difference_context')]+GROUPHELP+[scope(f,'revise_entities')])
        label='# 文本差异\n' if agent=='entity_extraction' else '# 输入四：文本差异\n'
        a=u.index(label)+len(label);b=u.index('</text_difference_json>',a)+len('</text_difference_json>')
        t+='## 附录：差异数据没有sentence_differences时\n\n只有该键不存在时，才用下列兼容差异说明替换正文对应块；不与分组差异说明重复发送。第一轮抽取的diff参数为真时，也会在User输出要求附近追加相应差异块；一般初始抽取没有diff。\n\n'
        t+=prompt_markdown(annotated('兼容差异块',u[a:b],[scope(f,'difference_context')],doc))
    if agent=='text_comparison':
        t+='## 附录：非分组比较焦点\n\n仅非分组入口的focus非空时插入，当前分组版本不使用。位置：'+ref(scope(f,'_build_comparison_prompt'))+'。\n\n'+code('比较焦点：{focus}')
    if agent=='evaluator':t+='## 实际评估逻辑的源码\n\n阈值筛选：'+ref(scope(f,'finalize_triples'))+'；加权公式：'+ref(scope(f,'_aggregate_scores'))+'。这是运行时的Python逻辑，不是向LLM发送的另一段prompt。\n\n'
    if agent=='conflict_resolution':t+='## 实际冲突处理逻辑的源码\n\n'+ref(scope(f,'resolve_conflicts'))+'；'+ref(scope(f,'_find_contradiction'))+'。\n\n'
    t+='## 文档维护\n\n固定文本来自程序拼接结果，运行数据按源码变量表示，回填核验通过。生成脚本位于tools/prompt_docs/export_agent_prompts.py，源码修改后需重新导出。\n'
    assert '\ufffd' not in t and t.count('```')%2==0
    target.write_text(t,encoding='utf-8')
    assert not re.search(r'\{\{[A-Z_]+\}\}',t)
    example_path=target.parent/'Prompt完整模板.json'
    example_path.write_text(json.dumps(dict(git_head=head,historical_run=False,examples=message_examples),ensure_ascii=False,indent=2),encoding='utf-8')
    manifest['message_examples'].append(example_path.relative_to(ROOT).as_posix())
    manifest['documents'].append(doc)

from export_feedback_prompts import export_feedback
feedback_names, feedback_status = export_feedback(ROOT, manifest)
NAMES.update(feedback_names)
STATUS.update(feedback_status)

index='# Agent Prompt总览与当前调用路线\n\n更新日期：2026-11-04。导出时 Git HEAD：`'+head+'`；文档内容取自当前工作区源码，包含本次未提交修改，精确文件哈希见导出核验 JSON。\n\n'
index+='## 当前运行的prompt是否唯一\n\n每一次模型调用只采用一套确定的System和User；程序按调用入口选择分支，不会把所有分支prompt一起发给模型。实体抽取仍分两轮；关系抽取只负责基线，反馈由 Add → Replace → Remove 三个 Agent 执行。每个阶段独立核查并接收前一步实际输出；各 Agent 内部采用核对问题、生成操作、复核输出三个阶段。问题由程序传递，模型只输出本阶段操作与 handoff。新事实按单句依据抽取。重建文本与比较当前由pipeline传入sentence_groups，使用分组版本；“非分组User”只是未传该参数时保留的另一条入口。默认 text_scope=sentence，每个分组单独调用重建和对比；feedback_scope=sentence，每句独立完成 Add→Replace→Remove。两个配置均可选 document，恢复整篇调用。逐句反馈遇到历史多来源或无法分组的条目时显式回退整篇并记录。所有请求顺序执行，共享最小请求间隔；可恢复 API 错误持续退避重试。\n\n'
index+='运行范围、限流重试及回放命令见 [逐句运行与API重试说明](逐句运行与API重试说明.md)。\n\n'
index+='## 各Agent文档与当前状态\n\n'+table(['Agent','完整Prompt文档','运行状态'],[(a,f'[{NAMES[a][:-3]}](<{a}/{NAMES[a]}>)',STATUS[a]) for a in NAMES])
index+='## 当前分组调用的源码证据\n\n'+ref(pipeline_call('text_generation_agent'))+'；文本对比：'+ref(pipeline_call('text_comparison_agent'))+'；实体：'+ref(pipeline_call('entity_extraction_agent'))+'；基线关系：'+ref(pipeline_call('relationship_extraction_agent'))+'；三步反馈：'+ref(pipeline_call('feedback_pipeline'))+'。\n\n'
index+='## 阅读方式\n\n每个文档按轮次/入口连续展示同一请求的System和User，每部分前仅用一行说明内容、相对文件路径和源码行号。固定内容全部展开，仅运行数据保留变量表达式。各Agent目录的Prompt完整模板.json保存不含阅读标注的角色结构。\n'
indexpath=ROOT/'karma/agents/Prompt总览.md';indexpath.write_text(index,encoding='utf-8')
manifest['documents'].insert(0,indexpath.relative_to(ROOT).as_posix())
for p in sources:manifest['source_files'][str(Path(p).relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(Path(p).read_bytes()).hexdigest()
for part in manifest['parts']:
    assert part['source_spans']
    for filename,a,b in part['source_spans']:
        assert 1<=a<=b<=len(sources[(ROOT/filename).as_posix()])
(OUT/'全Agent导出与行号核验.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Exported',len(NAMES),'agent documents and index;',len(manifest['parts']),'annotated prompt parts.')
