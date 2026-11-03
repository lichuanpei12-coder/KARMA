from pathlib import Path
import json
import re
from urllib.parse import unquote
from draft_content import FEWSHOTS

out=Path(__file__).resolve().parent
templates=json.loads((out/'Prompt草案模板.json').read_text(encoding='utf-8'))
report={'scope':'draft_completeness_and_links_only','agents':{},'links':0,'html':{}}
for role,record in templates['agents'].items():
    md=(out/f'{role}Agent_Prompt草案.md').read_text(encoding='utf-8')
    blocks=re.findall(r'```text\n(.*?)\n```',md,re.S)
    assert blocks[0]==record['messages'][0]['content']
    assert '\n\n'.join(blocks[1:])==record['messages'][1]['content']
    assert '自己检查' in record['messages'][1]['content']
    assert 'handoff_results' in record['messages'][1]['content']
    assert 'proposal_not_runtime'==record['status']
    report['agents'][role]={'blocks':len(blocks),'role_content_equal':True}
report['fewshots']={}
for role,examples in FEWSHOTS.items():
    count=0
    for part in examples.split('# 示例：')[1:]:
        data=part.split('输入：\n',1)[1]
        inp=json.JSONDecoder().raw_decode(data)[0]
        reply=json.loads(part.split('完整回复：\n',1)[1])
        indices={t['index'] for t in inp['current_triples']}
        source=inp['source_sentences'][0]['text']
        assert set(reply)=={'reviewed_sentence_ids','reviewed_indices','issues','handoff','handoff_results','add','replace','remove'}
        assert set(reply['reviewed_indices'])==indices
        assert all(not reply[k] for k in ('add','replace','remove') if k!=role.lower())
        for item in reply['replace']:
            assert item['index'] in indices and len(item['new_triples'])>=1
        triples=reply['add']+[t for item in reply['replace'] for t in item['new_triples']]
        for t in triples:
            assert t['evidence'] in source and t['source_sentence_ids']==['S1']
            assert all(0<=t[k]<=1 for k in ('confidence','clarity','relevance'))
            assert all(t[k] for k in ('head','relation','tail'))
        deleted={r['index'] for r in reply['remove']}
        for r in reply['remove']:
            assert r['index'] in indices and r['keep_index'] in indices-deleted
        count+=1
    report['fewshots'][role]=count
assert report['fewshots']=={'Add':4,'Replace':6,'Remove':3}
for p in out.glob('*.md'):
    txt=p.read_text(encoding='utf-8')
    assert '\ufffd' not in txt
    for target in re.findall(r'\]\(([^)]+)\)',txt):
        file,_,frag=target.partition('#')
        dest=(out/unquote(file)).resolve()
        assert dest.is_file(),target
        if frag.startswith('L'):
            assert 1<=int(frag[1:])<=len(dest.read_text(encoding='utf-8').splitlines())
        report['links']+=1
    html=p.with_suffix('.html').read_text(encoding='utf-8')
    ids=set(re.findall(r'id="(section-\d+)"',html))
    refs=re.findall(r'href="#(section-\d+)"',html)
    assert refs and all(ref in ids for ref in refs)
    assert 'toc-filter' in html
    report['html'][p.with_suffix('.html').name]={'headings':len(ids),'valid_toc':True}
(out/'草案完整性核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
