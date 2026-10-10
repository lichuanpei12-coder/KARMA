"""Create immutable snapshots and a conservative full-size candidate.

Only explicitly reviewed decisions change annotations. Other records are preserved
and labelled unreviewed, never presented as semantically verified.
"""
import copy
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BENCH = ROOT / 'data/BenchIE_FL_KARMA_Starter'
DOC = ROOT / 'data/DocIOE'
PILOT = ROOT / 'data/gold_review_pilot_20260915'
F = ('head', 'relation', 'tail')


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def save(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def triple(h, r, t):
    return dict(zip(F, (h, r, t)))


def copyfile(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)


def main():
    paths = {
        'b0': OUT/'benchie_fl/v0_original_starter',
        'b1': OUT/'benchie_fl/v1_without_xxx',
        'b2': OUT/'benchie_fl/v2_strict_623',
        'b3': OUT/'benchie_fl/v3_pilot',
        'b4': OUT/'benchie_fl/v4_minimal_changes_candidate',
        'd0': OUT/'docoie/v0_local_original',
        'd1': OUT/'docoie/v1_pilot',
        'd2': OUT/'docoie/v2_minimal_changes_candidate',
    }
    if any(p.exists() for p in paths.values()):
        raise RuntimeError('A version folder already exists; do not overwrite snapshots. Choose a new version name.')
    # Read and validate everything before publishing files.
    with zipfile.ZipFile(ROOT/'data/BenchIE_FL_KARMA_Starter.zip') as z:
        original_bytes = {name: z.read(name) for name in ('input.json','gold.json','benchie-annotated_300.txt')}
    original_gold = json.loads(original_bytes['gold.json'].decode('utf-8-sig'))
    binput = read(BENCH/'before_source_grounded/input.json')
    bold = read(BENCH/'before_source_grounded/gold.json')
    assert len(original_gold)==len(binput)==299 and sum(map(len,original_gold.values()))==1822
    assert sum(map(len,bold.values()))==1806
    current = read(BENCH/'gold.json')
    assert len(current)==267 and sum(map(len,current.values()))==623
    pilot_records = read(PILOT/'decisions.json')
    pilot_sources = read(PILOT/'source_map.json')
    # Source sentences for additional reviewed BenchIE_FL samples.
    bsents = {k:v[0] for k,v in binput.items()}
    modifications = []
    pending = []
    review_notes = {}
    bnew = copy.deepcopy(bold)
    docs = {d:read(DOC/f'DocOIE_{d}_eval_gold.json') for d in ('transportation','healthcare')}
    contexts = {d:read(DOC/f'DocOIE_{d}_eval_sent.json') for d in docs}
    dnew = copy.deepcopy(docs)

    def apply(group, key, originals, rs, sentence):
        result = []
        used = []
        for r in rs:
            used.extend(r['source_ids'])
            entry = copy.deepcopy(r)
            entry['source_sentence'] = sentence
            entry['round'] = 'pilot_import' if r.get('dataset') else 'continued_review'
            if r.get('unresolved'):
                # Minimal edit rule: disputed originals remain provisionally intact.
                entry['applied_annotations'] = copy.deepcopy(r['original_annotations'])
                entry['disposition'] = 'original_retained_pending_review'
                pending.append({'dataset':group,'sentence_id':key,'source_ids':r['source_ids'],
                                'question':r['unresolved'],'original_annotations':r['original_annotations']})
            else:
                entry['applied_annotations'] = copy.deepcopy(r['new_annotations'])
                entry['disposition'] = 'applied' if r['operation']!='keep' else 'unchanged_after_review'
            result.extend(entry['applied_annotations'])
            entry['dataset'] = group
            modifications.append(entry)
        assert sorted(used)==list(range(1,len(originals)+1)), key
        review_notes[key] = 'reviewed_with_pending' if any(r.get('unresolved') for r in rs) else 'reviewed'
        return result

    # Merge approved-direction pilot proposals. Pending items do not disappear.
    for key, source in pilot_sources.items():
        rs = [r for r in pilot_records if r['sentence_id']==key]
        if source['dataset']=='BenchIE_FL':
            bnew[key]=apply('benchie_fl',key,bold[key],rs,source['sentence'])
        else:
            domain=source['domain'];doc=source['document_id'];sentence=source['sentence']
            old=[triple(t['sub'],t['rel'],t['obj']) for t in docs[domain][doc][sentence]['triple_gold']]
            out=apply('docoie_'+domain,key,old,rs,sentence)
            dnew[domain][doc][sentence]['triple_gold']=[dict(zip(('sub','rel','obj'),[t[f] for f in F])) for t in out]

    def record(key, originals, refs, action, new, reason, edits=None, issue=None):
        return {'sentence_id':key,'source_ids':refs,'original_annotations':[originals[i-1] for i in refs],
                'new_annotations':new,'operation':action,'reason':reason,'word_changes':edits or [],
                'unresolved':issue}

    # Additional BenchIE_FL review: 3 complete sentences, 25 original representatives.
    for sid in (1,23,77):
        key=f'benchie_{sid}';old=bold[key];rs=[]
        for i,t in enumerate(old,1):
            action='keep';new=[t];edits=[]
            reason='原句共享成分直接支持，保留原 Gold，避免再次采用连续子串过滤。'
            if sid==1 and i in (3,6,7):
                action='remove_fact';new=[]
                reason='用户明确排除的 had 关系：原文给出任职关系，不另外生成国家/法院拥有职务的关系。任职事实仍保留。'
            elif sid==23 and i==1:
                action='repair_source_wording';new=[triple(t['head'],'including',t['tail'])]
                reason='including 原文直接出现，省去原代表不必要补出的 are；保留后续疫苗及例示关系。'
                edits=[{'removed_from_old':['are'],'added':[]}]
            elif sid==23 and i in (2,3):
                reason='rabies vaccination by Louis Pasteur in 1886 直接支持施事和年份。保留原 Gold 的 was done 语法展开；不把明确的名词事件结构误判为无依据。'
                edits=[{'already_in_old_not_new':['was','done'],'basis':'名词事件及 by/in 修饰语'}]
            elif sid==23 and i==4:
                reason='successful rabies vaccination 直接支持成功属性；保留原 Gold 的系词展开，不删除修饰事实。'
                edits=[{'already_in_old_not_new':['was'],'basis':'形容词 successful'}]
            elif sid==23 and i==5:
                # Copular agreement, not an external medical inference.
                action='repair_agreement';new=[triple('rabies','is','a viral disease')]
                reason='including 将 rabies vaccination 作为 other viral diseases 的疫苗实例；沿用原簇类型关系，仅修正单复数和冠词，不使用外部医学知识。'
                edits=[{'old':'viral diseases','new':'a viral disease','basis':'必要的一致性调整'}]
            elif sid==77 and i>=8:
                reason='such venues as 后的专名列表直接标明场地类型；旧 Gold 的 is 为结构补全，保留类型事实，不依据词不连续删除。'
                edits=[{'already_in_old_not_new':['is'],'basis':'such venues as 的列举结构'}]
            rs.append(record(key,old,[i],action,new,reason,edits))
            rs[-1]['source_id_unit']='triple_index_in_before_source_grounded_gold'
            rs[-1]['original_cluster_ordinals']=[([2,3,4,5,7][i-1]) if sid==23 else i]
            rs[-1]['evidence_fragments']=[bsents[key]]
        bnew[key]=apply('benchie_fl',key,old,rs,bsents[key])
    pending.append({'dataset':'benchie_fl','sentence_id':'benchie_85','source_ids':list(range(1,20)),
                    'question':'19条是否独立计分，以及时间是否对各主体/动作逐项展开；用户已质疑。暂保留旧19条，不擅自压缩为3条。',
                    'original_annotations':bold['benchie_85']})
    review_notes['benchie_85']='reviewed_with_pending'
    pending.append({'dataset':'benchie_fl','sentence_id':'benchie_1','source_ids':[1,2,4,5],
                    'question':'带限定与不带限定的任职表达是否分别计分，和第85句同属粒度问题；暂保持原条目。',
                    'original_annotations':[bold['benchie_1'][i-1] for i in (1,2,4,5)]})
    review_notes['benchie_1']='reviewed_with_pending'

    # Complete the first annotated document in each DocOIE domain (14 new targets).
    for domain in docs:
        doc=next(iter(docs[domain]))
        for idx,(sentence,annotation) in enumerate(docs[domain][doc].items()):
            key=f'docoie_{domain}_doc0_target{idx}'
            if key in pilot_sources:continue
            old=[triple(t['sub'],t['rel'],t['obj']) for t in annotation['triple_gold']]
            rs=[]
            if domain=='healthcare' and idx==6:
                new=triple(old[0]['head'],old[0]['relation'],'remote medical consultation with a system that was relatively inexpensive and easy to install into existing operating rooms')
                rs=[record(key,old,[1,2],'repair_desired_scope',[new],
                           'would be desirable 支配系统需求描述。合回完整期望，不将相对便宜且易安装写成一个已经存在系统的无条件事实。')]
            else:
                for i,t in enumerate(old,1):
                    action='keep';new=[t];edits=[];issue=None
                    reason='结合目标句和邻句复核，原有事实有直接依据，保持措辞、情态与对象限定，不为数量另拆。'
                    if domain=='transportation' and idx==1 and i==4:
                        action='repair_source_expression';new=[triple('the controller','may query the ECU in order to determine',t['tail'])]
                        reason='恢复 controller 为主语并保留 may 与原句目的结构，省去旧标注人为加入的 is。'
                        edits=[{'removed':['is'],'shared_from_source':['may'],'basis':'同一查询动作的目的状语'}]
                    elif domain=='transportation' and idx==6:
                        issue='which 的先行项以及 may 对 instructions stored 的适用范围仍需确定；不擅自把存储或执行断言改成无条件事实。'
                        reason='此句指代和可能实施范围有歧义；当前保留原标注，标作待复核。'
                    elif domain=='transportation' and idx==7:
                        action='restore_restriction';new=[triple(t['head'],t['relation'],'illustration purposes only')]
                        reason='原文 purposes only 中的 only 是明确限制，补回漏掉的原词，不增加事实。'
                        edits=[{'restored_from_source':['only']}]
                    elif domain=='healthcare' and idx==5 and i==2:
                        action='split_identity_and_trademark';new=[triple(t['head'],t['relation'],'Intuitive Surgical, Inc.'),triple(t['head'],'is sold under the trademark','Da Vinci')]
                        reason='厂商与商标不是同一实体。将旧长宾语拆为销售方和商标两条，均来自 sold by ... under the trademark ...。'
                        edits=[{'shared':['is sold'],'source_phrase':'sold by Intuitive Surgical, Inc. under the trademark Da Vinci'}]
                    elif domain=='healthcare' and idx==5 and i==4:
                        action='repair_source_expression';new=[triple('a robotic system','allows a surgeon to remotely perform a surgical procedure through','use of robot arms')]
                        reason='用原句 allows ... through 表达手段，替换原 Gold 的事件名词主语加 is through；不新增手段事实。'
                    elif domain=='healthcare' and idx==7 and i==2:
                        action='repair_source_expression';new=[triple('Alert icon','can be selected by the user at the remote station to generate','an alert indicator')]
                        reason='保留 can 的可能性和 to generate 的目的，恢复原句主语；不把可能选择改成实际选择。'
                    elif domain=='healthcare' and idx==9 and i==2:
                        issue='rapidly 是否同时修饰 or 后的 move through a captured video clip 有范围歧义；暂保留原 Gold。'
                    elif domain=='healthcare' and idx==9 and i==3:
                        action='repair_source_expression';new=[triple('the user','can move through a captured video clip by moving','the slide bar')]
                        reason='保留共享 can 和第二个动作的 by moving 手段；省去旧 Gold 额外的 is 和范围不明的 rapidly。'
                        edits=[{'removed_from_old':['is','rapidly'],'shared_from_source':['can']}]
                    rs.append(record(key,old,[i],action,new,reason,edits,issue))
            if domain=='transportation' and idx==7:
                rs.append(record(key,old,[],'supplement',[triple('specific exemplary embodiments','have been','discussed')],
                                 '反向检查：While 从句明确陈述已讨论示例实施例，补充该漏标事实；不是假设事件。'))
            pos=contexts[domain][doc].index(sentence)
            for r in rs:
                r['source_id_unit']='target_sentence_triple_ordinal'
                r['evidence_fragments']=[sentence]
                r['context_only']=contexts[domain][doc][max(0,pos-1):pos]+contexts[domain][doc][pos+1:pos+2]
            updated=apply('docoie_'+domain,key,old,rs,sentence)
            dnew[domain][doc][sentence]['triple_gold']=[dict(zip(('sub','rel','obj'),[t[f] for f in F])) for t in updated]

    # All semantic decisions above have completed before any original is copied.
    for name,raw in original_bytes.items():
        dest=paths['b0']/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    for name in ('input.json','gold.json'):
        copyfile(BENCH/'before_source_grounded'/name,paths['b1']/name)
    for f in BENCH.iterdir():
        if f.is_file() and (f.suffix in ('.json','.md')):copyfile(f,paths['b2']/f.name)
    for sub in ('input','gold'):
        for f in (BENCH/sub).glob('*.json'):copyfile(f,paths['b2']/sub/f.name)
    for domain in ('transportation','healthcare'):
        for suffix in ('gold','sent'):
            name=f'DocOIE_{domain}_eval_{suffix}.json';copyfile(DOC/name,paths['d0']/name)
    for f in (DOC/'transport').glob('*.json'):copyfile(f,paths['d0']/'transport'/f.name)
    copyfile(DOC/'DocOIE_transportation_gold_input.json',paths['d0']/'DocOIE_transportation_gold_input.json')
    for sourcegroup,dest in [('benchie_fl',paths['b3']),('docoie_transportation',paths['d1']/'transportation'),('docoie_healthcare',paths['d1']/'healthcare')]:
        for name in ('input.json','gold.json'):copyfile(PILOT/sourcegroup/name,dest/name)
    for name in ('manifest.json','decisions.json','pending.json','source_map.json','coverage_review.json','试处理结果.md'):
        for dest in (paths['b3'],paths['d1']):copyfile(PILOT/name,dest/'shared_review_records'/name)
    save(paths['b4']/'input.json',binput);save(paths['b4']/'gold.json',bnew)
    batches=[];keys=list(binput)
    for batch in range(20):
        ids=keys[batch*15:(batch+1)*15]
        save(paths['b4']/'input'/f'{batch}.json',{k:binput[k] for k in ids})
        save(paths['b4']/'gold'/f'{batch}.json',{k:bnew[k] for k in ids})
        batches.append({'batch':batch,'sample_ids':ids,'sample_count':len(ids),'triple_count':sum(len(bnew[k]) for k in ids)})
    save(paths['b4']/'batch_manifest.json',batches)
    save(paths['b4']/'review_status.json',{k:review_notes.get(k,'unreviewed_original_retained') for k in bnew})
    for domain,content in dnew.items():
        dest=paths['d2']/domain
        save(dest/'eval_gold.json',content)
        dinput={doc:list(targets) for doc,targets in content.items()}
        save(dest/'input.json',dinput)
        save(dest/'gold.json',{doc:[triple(t['sub'],t['rel'],t['obj']) for a in targets.values() for t in a['triple_gold']] for doc,targets in content.items()})
        status=[]
        for di,(doc,targets) in enumerate(content.items()):
            flat=[]
            for si,(sentence,ann) in enumerate(targets.items()):
                key=f'docoie_{domain}_doc{di}_target{si}'
                flat.extend(triple(t['sub'],t['rel'],t['obj']) for t in ann['triple_gold'])
                context_positions=[i for i,s in enumerate(contexts[domain][doc]) if s==sentence]
                status.append({'sentence_id':key,'document_id':doc,'target_sentence':sentence,
                               'context_positions':context_positions,
                               'review_status':review_notes.get(key,'unreviewed_original_retained')})
            save(dest/'gold'/f'{di}.json',flat)
        save(dest/'review_status.json',status)
        copyfile(DOC/f'DocOIE_{domain}_eval_sent.json',dest/'context_only.json')
    for dest,group in ((paths['b4'],'benchie_fl'),(paths['d2'],'docoie')):
        save(dest/'changes.json',[r for r in modifications if r['dataset'].startswith(group)])
        save(dest/'pending.json',[r for r in pending if r['dataset'].startswith(group)])
    summary={'status':'FULL_SIZE_CANDIDATE_PARTIALLY_REVIEWED_NOT_FINAL_GOLD',
             'benchie_fl':{'samples':len(bnew),'gold':sum(map(len,bnew.values())),
                           'reviewed_sentences':sum(k.startswith('benchie_') for k in review_notes),'total_sentences':299},
             'docoie':{domain:{'documents':len(dnew[domain]),'target_sentences':sum(len(v) for v in dnew[domain].values()),
                               'gold':sum(len(a['triple_gold']) for v in dnew[domain].values() for a in v.values()),
                               'reviewed_sentences':sum(k.startswith('docoie_'+domain) for k in review_notes)} for domain in dnew},
             'additional_reviewed_sentences':17,'total_reviewed_sentences':len(review_notes),
             'pending_records':len(pending),'original_pending_items_retained':True,
             'pending_source_references':sum(len(r['source_ids']) for r in pending),
             'version_paths':{k:str(p.relative_to(ROOT)) for k,p in paths.items()},
             'active_paths_unchanged':True,'scoring_code_unchanged':True}
    save(OUT/'version_manifest.json',summary)
    for code,dest in paths.items():
        save(dest/'snapshot_manifest.json',{'version':code,'created':'2026-09-15',
             'status':summary['status'] if code in ('b4','d2') else 'HISTORICAL_SNAPSHOT',
             'files':[{'path':str(f.relative_to(dest)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(dest.rglob('*')) if f.is_file()]})
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
