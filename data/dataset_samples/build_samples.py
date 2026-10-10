import json, os, zipfile
from pathlib import Path

audit = Path(os.environ['TEMP']) / 'codex-relation-dataset-audit'
out = Path(__file__).parent
samples = {}

def read_json_records(text):
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]

def spo_samples(records, source):
    selected = []
    for line, rec in enumerate(records, 1):
        if not rec.get('spo_list'):
            continue
        spo = rec['spo_list'][0]
        obj = spo['object']
        obj = obj.get('@value') if isinstance(obj, dict) else obj
        selected.append({'source': source, 'record': line, 'text': rec['text'],
                         'triple': [spo['subject'], spo['predicate'], obj],
                         'raw_annotation': spo})
        if len(selected) == 10:
            break
    return selected

with zipfile.ZipFile(audit / 'kaggle-duie.zip') as z:
    name = next(n for n in z.namelist() if n.endswith('duie_dev.json'))
    samples['DuIE'] = spo_samples(read_json_records(z.read(name).decode('utf-8-sig')), name)

samples['CMeIE'] = spo_samples(read_json_records((audit / 'cmeie-dev.jsonl').read_text(encoding='utf-8-sig')), 'Aunderline/CMeIE/CMeIE_dev.jsonl')

with zipfile.ZipFile(audit / 'sanwen.zip') as z:
    selected = []
    names = sorted(n for n in z.namelist() if '/relation_extraction/Testing/' in n and n.endswith('.ann'))
    for name in names:
        annotations = z.read(name).decode('utf-8-sig').splitlines()
        entities = {}
        relations = []
        for line in annotations:
            if line.startswith('T'):
                ident, position, word = line.split('\t', 2)
                entities[ident] = (word, position)
            elif line.startswith('R'):
                relations.append(line)
        if not relations:
            continue
        raw = relations[0]
        relation_id, value = raw.split('\t', 1)
        label, arg1, arg2 = value.split()
        h_id, t_id = arg1.split(':')[1], arg2.split(':')[1]
        h, t = entities[h_id], entities[t_id]
        text = z.read(name[:-4]+'.txt').decode('utf-8-sig')
        starts = [int(h[1].split()[1]), int(t[1].split()[1])]
        ends = [int(h[1].split()[2]), int(t[1].split()[2])]
        excerpt_start = max(0, min(starts)-15)
        excerpt_end = min(len(text), max(ends)+15)
        excerpt = text[excerpt_start:excerpt_end]
        selected.append({'source':name, 'record':relation_id, 'text':excerpt,
                         'text_is_excerpt':True, 'excerpt_start':excerpt_start,
                         'triple':[h[0], label, t[0]], 'raw_annotation':raw,
                         'entity_annotations':{h_id:h, t_id:t}})
        if len(selected) == 10:
            break
    samples['SanWen'] = selected

geology_text = (audit / 'geology-entity-training-2.json').read_text(encoding='utf-8-sig')
# The source contains extra JSON after the first complete array. The first
# array alone contains more than the requested ten examples; do not repair it.
data, geology_end = json.JSONDecoder().raw_decode(geology_text)
selected = []
for group, records in enumerate(data, 1):
    for idx, rec in enumerate(records, 1):
        selected.append({'source':'Entity Training Set 2.json', 'record':f'{group}.{idx}',
                         'text':None, 'triple':[rec['head'],rec['relation'],rec['tail']],
                         'raw_annotation':rec})
        if len(selected) == 10: break
    if len(selected) == 10: break
samples['Geology'] = selected

if (out / 'patent-first10.json').exists():
    records = read_json_records((out / 'patent-first10.json').read_text(encoding='utf-8-sig'))
    selected = []
    for idx, rec in enumerate(records,1):
        if not rec.get('spo_list'): continue
        spo = rec['spo_list'][0]
        h, t = spo['subject'], spo['object']
        text = rec['text']
        selected.append({'source':'中药专利数据集/test.json', 'record':idx, 'text':text,
                         'triple':[text[h[0]:h[1]+1],spo['predicate'],text[t[0]:t[1]+1]],
                         'raw_annotation':spo})
        if len(selected)==10: break
    samples['TPSCRE'] = selected

source_urls = {
    'DuIE':'https://www.kaggle.com/datasets/mushansanren/duiedata',
    'CMeIE':'https://huggingface.co/datasets/Aunderline/CMeIE/tree/main',
    'SanWen':'https://github.com/lancopku/Chinese-Literature-NER-RE-Dataset',
    'Geology':'https://data.mendeley.com/datasets/mwwbc7cgy8/2',
    'TPSCRE':'https://www.scidb.cn/en/detail?dataSetId=e9c545b78cce49dc81436a015430ac4c',
}
for dataset, entries in samples.items():
    assert len(entries) == 10, (dataset, len(entries))
    for entry in entries:
        entry['source_url'] = source_urls[dataset]
        assert len(entry['triple']) == 3 and all(isinstance(x,str) and x for x in entry['triple'])
        if entry['text'] is not None:
            assert entry['triple'][0] in entry['text'] and entry['triple'][2] in entry['text'], (dataset,entry['record'])

(out/'samples.json').write_text(json.dumps(samples,ensure_ascii=False,indent=2),encoding='utf-8')
report = ['# 中文关系抽取数据集：各10条真实标注样例', '',
          '共5个数据集、50条三元组。DuIE、CMeIE、TPSCRE各取前10条有标注记录的第一条关系；SanWen取10个不同测试文档中的第一条关系；地质灾害取第一个分组中的前10个三元组。', '',
          '这是标注结构抽样核查，不是对标注事实、完整性或全数据集质量的审核。保持原始实体文字、关系标签和方向，不纠正可疑标注。', '',
          'CMeIE此次使用Hugging Face的第三方镜像；SanWen使用作者原始仓库，并非此前找到的OpenDataLab镜像。SanWen只显示有关实体附近的原文节选。地质灾害两个JSON没有每条三元组对应的原文，该文件另有JSON格式问题；本报告只解析首个完整JSON数组，未修复源文件。', '']
for dataset in ['DuIE','TPSCRE','SanWen','CMeIE','Geology']:
    report.extend([f'## {dataset}', '', f"来源：[数据页面]({source_urls[dataset]})", '', '| 编号 | 主体 | 关系 | 客体 |', '|---|---|---|---|'])
    for idx, entry in enumerate(samples[dataset],1):
        h,r,t = entry['triple']
        report.append(f'| {idx} | {h} | {r} | {t} |')
    report.append('')
    for idx, entry in enumerate(samples[dataset],1):
        report.extend([f'### 样例{idx}', '', f"文件：`{entry['source']}`；记录：`{entry['record']}`", ''])
        if entry['text'] is None:
            report.append('原文：此JSON条目未提供对应原文。')
        else:
            label = '原文节选' if entry.get('text_is_excerpt') else '原文'
            report.extend([f'{label}：', '', entry['text']])
        report.extend(['', '原始关系标注：', '', '```json',json.dumps(entry['raw_annotation'],ensure_ascii=False,indent=2),'```',''])
        if 'entity_annotations' in entry:
            report.extend(['实体编号映射：', '', '```json',json.dumps(entry['entity_annotations'],ensure_ascii=False,indent=2),'```',''])
(out/'samples.md').write_text('\n'.join(report),encoding='utf-8')
for dataset, entries in samples.items():
    print(dataset, 'samples=',len(entries))
    for entry in entries:
        print(json.dumps({k:entry[k] for k in ['record','triple']},ensure_ascii=False))
