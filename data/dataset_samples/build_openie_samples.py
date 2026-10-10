import json
import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent
AUDIT = Path(os.environ['TEMP']) / 'codex-relation-dataset-audit'
datasets = {}

span = json.loads((AUDIT / 'spansaoke-test.json').read_text(encoding='utf-8'))
datasets['SpanSAOKE'] = {
    'source': 'https://github.com/Lvzhh/MGD-GNN/blob/main/data/test.json',
    'status': '实际文件，前10条句子记录；保留全部spo_list，包含符号表达。',
    'samples': [dict(record=i+1, id=r['unique_id'], text=r['sentence'],
                     triples=[[s['subject'], s['predicate'], s['object']] for s in r['spo_list']],
                     raw_record=r) for i, r in enumerate(span[:10])]
}

with zipfile.ZipFile(AUDIT / 'aprcoie.zip') as z:
    apr = json.loads(z.read('APRCOIE_v1-V_I/data/data_regular.json'))
datasets['APRCOIE'] = {
    'source': 'https://github.com/jialin666/APRCOIE_v1/blob/V_I/data/data_regular.json',
    'status': '实际文件data_regular.json前10条记录；triples-char及triples-number是JSON字符串，需再次解析。',
    'samples': [dict(record=i+1, id=r['id'], text=r['sentence'],
                     triples=json.loads(r['triples-char']), raw_record=r) for i, r in enumerate(apr[:10])]
}
for s in datasets['APRCOIE']['samples']:
    words = json.loads(s['raw_record']['words'])
    indices = json.loads(s['raw_record']['triples-number'])
    resolved = [[''.join(words[i] for i in part) for part in t] for t in indices]
    assert resolved == s['triples']

with zipfile.ZipFile(AUDIT / 'coer.zip') as z:
    coer = ET.fromstring(z.read('COER-master/test_result.xml'))
selected = []
seen = set()
for r in coer.findall('relation'):
    text = r.findtext('origin_text')
    if text in seen:
        continue
    seen.add(text)
    args = r.findall('entity_pair/argument')
    selected.append(dict(id=r.attrib['id'], text=text,
                         triples=[[args[0].text, r.find('relation_phrase').attrib['phrase_text'], args[1].text]],
                         raw_record=ET.tostring(r, encoding='unicode')))
    if len(selected) == 10:
        break
datasets['COER'] = {
    'source': 'https://github.com/TJUNLP/COER/blob/master/test_result.xml',
    'status': '实际文件test_result.xml自动抽取结果；依次选前10个不同原文，每个原文展示第一次出现的relation。不是人工金标准；未取得COERKB网盘全量文件。',
    'samples': selected
}

li = '李白(701年－762年), 深受庄子思想影响，爽朗大方，爱饮酒作诗，喜交友，代表作有《望庐山瀑布》等著名诗歌。'
paper = [
    (li, ['李白', '深受X影响', '庄子思想'], 'Table 1: Relations'),
    (li, ['李白', '爱', '[饮酒|作诗]'], 'Table 1: Relations'),
    (li, ['李白', '喜', '交友'], 'Table 1: Relations'),
    (li, ['李白', 'BIRTH', '701年'], 'Table 1: Attribute'),
    (li, ['李白', 'DEATH', '762年'], 'Table 1: Attribute'),
    (li, ['李白', '代表作', '《望庐山瀑布》'], 'Table 1: Attribute'),
    (li, ['李白', 'DESC', '爽朗大方'], 'Table 1: Description'),
    (li, ['《望庐山瀑布》', 'ISA', '著名诗歌'], 'Table 1: Concept'),
    ('山东的GDP高于所有西部的省份。', ['山东的GDP', '高于', '西部的所有省份'], 'Table 2: Correct Facts'),
    ('李白游览了雄奇灵秀的泰山。', ['李白', '游览', '泰山'], 'Table 2: Correct Facts'),
]
datasets['SAOKE'] = {
    'source': 'https://arxiv.org/abs/1904.12535',
    'pdf_copy': 'https://bimsa.net/doc/publication/4442.pdf',
    'status': '仅原论文Table 1和Table 2的10条格式示例，来源于3个句子；未取得SAOKE_DATA.json，未核对是否出现在数据包中。不是10条数据集记录。',
    'samples': [dict(id=where, text=text, triples=[triple], kind='paper_format_example') for text, triple, where in paper]
}

for name, info in datasets.items():
    assert len(info['samples']) == 10
    for s in info['samples']:
        assert s['text'] and s['triples']
        assert all(len(t) == 3 and all(isinstance(v, str) and v for v in t) for t in s['triples'])

(ROOT / 'openie_samples.json').write_text(json.dumps(datasets, ensure_ascii=False, indent=2), encoding='utf-8')
md = ['# 中文开放信息抽取样例核对', '',
      '核对日期：2026-09-17。SpanSAOKE、APRCOIE、COER各10条来自实际文件；SAOKE只有10条论文格式示例，不能视为已核对的下载包样本。', '',
      '三元组使用原文件字段；没有纠正原始拼写、裁剪实体或补全语义。开放抽取不保证每个结果都语义正确，符号表达也不能直接当作普通实体名。', '']
for name in ['SpanSAOKE', 'SAOKE', 'COER', 'APRCOIE']:
    info = datasets[name]
    md += [f'## {name}', '', info['status'], '', f"来源：{info['source']}", '']
    for i, s in enumerate(info['samples'], 1):
        md += [f"### 样例 {i}（ID：{s['id']}）", '', '原文：' + s['text'], '', '结果：']
        md += ['- ' + json.dumps(t, ensure_ascii=False) for t in s['triples']]
        md += ['']
        if 'raw_record' in s:
            raw = s['raw_record']
            md += ['原始记录：', '', '```' + ('xml' if isinstance(raw, str) else 'json'),
                   raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False, indent=2), '```', '']
(ROOT / 'openie_samples.md').write_text('\n'.join(md), encoding='utf-8')
for name, info in datasets.items():
    print(name, info['status'])
    for i, s in enumerate(info['samples'], 1):
        print(i, s['id'], s['text'], json.dumps(s['triples'][0], ensure_ascii=False))
