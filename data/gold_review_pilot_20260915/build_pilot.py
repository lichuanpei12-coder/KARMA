"""Materialize explicitly reviewed pilot decisions; not a general filtering algorithm.

No model output is used. Originals and current active datasets are read-only inputs.
Run from the repository root: python -B data/gold_review_pilot_20260915/build_pilot.py
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
BENCH = ROOT / 'data/BenchIE_FL_KARMA_Starter'
DOC = ROOT / 'data/DocIOE'
FIELDS = ('head', 'relation', 'tail')
SAMPLE_IDS = [228, 85, 19, 34, 240, 2]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def triple(h, r, t):
    return dict(zip(FIELDS, (h, r, t)))


def parse_bench():
    result = {}
    for line_no, line in enumerate((BENCH / 'benchie-annotated_300.txt').read_text(encoding='utf-8').splitlines(), 1):
        if line.startswith('sent_id:'):
            label, sentence = line.split('\t', 1)
            sid = int(label.split(':')[1])
            result[sid] = {'sentence': sentence, 'source_line': line_no, 'clusters': []}
            cluster = None
        elif re.match(r'^\d+--> Cluster ', line):
            cluster = {'label': line, 'source_line': line_no, 'expressions': []}
            result[sid]['clusters'].append(cluster)
        elif line.count('-->') == 2:
            if cluster is None:
                cluster = {'label': 'implicit', 'source_line': line_no, 'expressions': []}
                result[sid]['clusters'].append(cluster)
            cluster['expressions'].append({'source_line': line_no,
                                          'triple': dict(zip(FIELDS, [x.strip() for x in line.split('-->')]))})
    return result


def build():
    source = parse_bench()
    baseline = read(BENCH / 'before_source_grounded/gold.json')
    baseline_input = read(BENCH / 'before_source_grounded/input.json')
    groups = {name: {'input': {}, 'gold': {}} for name in ('benchie_fl', 'docoie_transportation', 'docoie_healthcare')}
    records = []
    source_map = {}
    coverage = []
    counts = Counter()
    disputes = []
    snapshots = {}
    original_refs = {}

    for sid in SAMPLE_IDS:
        key = f'benchie_{sid}'
        assert baseline_input[key] == [source[sid]['sentence']]
        groups['benchie_fl']['input'][key] = baseline_input[key]
        groups['benchie_fl']['gold'][key] = []
        snapshots[key] = baseline[key]
        assert len(source[sid]['clusters']) == len(baseline[key])
        original_refs[key] = set(range(1, len(baseline[key]) + 1))
        counts['benchie_original_clusters'] += len(source[sid]['clusters'])
        counts['benchie_original_expressions'] += sum(len(c['expressions']) for c in source[sid]['clusters'])
        source_map[key] = {'dataset': 'BenchIE_FL', 'sentence': source[sid]['sentence'],
                           'source_line': source[sid]['source_line'], 'target': True,
                           'context_sentences': [], 'clusters': source[sid]['clusters']}

    def decide(group, key, refs, action, outputs, reason, evidence=None, edits=None,
               unresolved=None, approved_alternatives=None):
        old = [snapshots[key][i-1] for i in refs]
        out = groups[group]['gold'][key]
        new_ids = []
        for t in outputs:
            assert set(t) == set(FIELDS) and all(isinstance(t[f], str) and t[f] for f in FIELDS)
            if t in out:
                raise ValueError(f'Duplicate pilot gold: {key}: {t}')
            out.append(t)
            new_ids.append(f'{key}:fact:{len(out)}')
        ev = evidence or [source_map[key]['sentence']]
        assert all(fragment in source_map[key]['sentence'] for fragment in ev)
        rec = {'sentence_id': key, 'dataset': group, 'source_ids': refs,
               'source_id_unit': 'cluster_ordinal' if group == 'benchie_fl' else 'target_sentence_triple_ordinal',
               'original_annotations': old, 'new_fact_ids': new_ids, 'new_annotations': outputs,
               'operation': action, 'evidence_fragments': ev,
               'word_changes': edits or [], 'reason': reason,
               'unresolved': unresolved,
               'approved_alternatives': approved_alternatives or [],
               'status': 'pending' if unresolved else 'reviewed_pilot_proposal'}
        records.append(rec)
        if unresolved:
            disputes.append({'sentence_id': key, 'source_ids': refs, 'question': unresolved})

    def b(sid, refs, action, outputs, reason, **kw):
        decide('benchie_fl', f'benchie_{sid}', refs, action, outputs, reason, **kw)

    # Required example 228: evaluate the original sentence, including the 'or'.
    b(228, [1], 'select_source_expression', [triple('The permanent members', 'are', 'the provost')],
      '选择原簇已有的原文方向，不再把主语宾语倒置并将 are 改成 is。',
      evidence=['The permanent members are the provost'],
      edits=[{'kind': 'restore_source_direction', 'detail': '使用原句主语 The permanent members 和关系 are；不新增词。'}])
    b(228, [2], 'select_source_expression', [triple('The permanent members', 'are', 'the Carl H. Pforzheimer University Professor')],
      '并列宾语共享 are。中间的 the provost 不阻止该成员事实成立。',
      evidence=['The permanent members are', 'the Carl H. Pforzheimer University Professor'])
    schools = ['the Faculty of Arts and Sciences', 'Harvard Business School', 'Harvard Law School', 'Harvard Medical School']
    # Preserve the original shared alternatives, not a deans x designees assertion.
    for index, school in enumerate(schools):
        refs = [5 + 2*index, 6 + 2*index]
        if index == 0:
            refs = [3, 4] + refs
        b(228, refs, 'repair_alternative_scope',
          [triple('The permanent members', 'are', f'the deans or designees from {school}')],
          '原句列出各学校的 deans or designees。保留 or；不同时断言每所学校的两类角色都任成员。泛化的 deans/designees 条目由带学校限定的成员事实覆盖。',
          evidence=['The permanent members are', 'the deans or designees from the following Schools', school],
          edits=[{'kind': 'restore_shared_or_and_from', 'detail': '组合原文共享成分；无新增词、无语态转换。'}])
    for c in range(13, 21):
        b(228, [c], 'remove_fact', [],
          '原句陈述成员由院长或代表担任，不能据此分别断言每校均具有 deans 和 designees；has 也不是这里的原文关系。原有学校成员信息已由保留 or 的表达覆盖。')
    coverage.append({'sentence_id': 'benchie_228', 'review': '已覆盖 provost、教授职位、四所学校对应的院长或代表成员；保留 or，不恢复全部20条。', 'unresolved': False})

    # Required example 85: individual decisions, shared syntax; no when blacklist.
    for c, original in enumerate(baseline['benchie_85'], 1):
        if c == 1:
            reason = '过去时 were proven 直接陈述技能已得到证明；保留 readily。'
        elif c <= 5:
            reason = 'when 从句在此描述已发生的动员/召回，与技能得到证明的事件相联系；两个并列主语和谓语共享 were。'
        elif c <= 7:
            reason = 'when 将技能证明与所述过去事件联系，句末 during 为该事件提供时间；保留原 Gold 的两个时间表达。'
        elif c <= 15:
            reason = '按原句通常的并列 VP 读法，句末 during 修饰 were mobilized and recalled back to active duty；共享两个主语和两项时间。逐项保留，不因 when 或非连续片段删除。'
        else:
            reason = 'squadrons 和 personnel 分别参与动员及召回；mobilize/recall 可对各并列项成立，不是必须共同才能完成的集合动作。原文 were 直接共享。'
        b(85, [c], 'keep', [original], reason,
          edits=[{'kind': 'shared_source_components', 'detail': '共享并列主语、were、谓语及原句末尾时间状语；没有在本次新增词。'}] if c > 1 else [])
    coverage.append({'sentence_id': 'benchie_85', 'review': '复核全部19簇后保留19条，覆盖技能证明、动员、召回及原文两个时期；采用末尾时间状语修饰并列谓语的通常读法。', 'unresolved': False})

    for c, original in enumerate(baseline['benchie_19'], 1):
        b(19, [c], 'keep', [original],
          '职业起点、年份和影片由原句明确给出；film + 片名直接支持类型判断。无需为增加数量另拆事实。' if c < 4 else
          'film `` A New Oath `` 是明确的类型与名称结构；保留旧 Gold 的 is 作为系动词补全，不借助外部知识。',
          edits=[{'kind': 'existing_grammatical_completion', 'added_relative_to_source': ['is'], 'detail': '原 Gold 已有，表达 film 与片名的类型关系；本次没有新增。'}] if c == 4 else [])
    coverage.append({'sentence_id': 'benchie_19', 'review': '4条原 Gold 保留，覆盖职业起点、1947、影片及片名类型；无新增独立事实。', 'unresolved': False})

    for c, original in enumerate(baseline['benchie_34'], 1):
        if 8 <= c <= 13:
            b(34, [c], 'pending', [], '原句把 sculptors and painters 与三个国家并列，未明确每一职业在每个国家都有成员。保留原标注供复核，不机械生成职业×国家组合。',
              unresolved='能否分别断言该职业在这个国家有人参加？整组来自三国不必然支持六个职业×国家组合。')
        else:
            b(34, [c], 'keep', [original],
              '保留有明确依据的活动、首次、1982、参加者总数和群体、国家列表及地点。thirty 只修饰整个 sculptors and painters 群体，不分配为两组各30人。' if c != 6 else
              'Pine Plains, New York 是原句地点标注结构；保留既有 is located in，不使用外部地理知识。',
              edits=[{'kind': 'existing_structural_completion', 'added_relative_to_source': ['is', 'located'], 'detail': '旧 Gold 把原句地名层级结构显式写为位置关系；本次不进一步改写。'}] if c == 6 else [])
    coverage.append({'sentence_id': 'benchie_34', 'review': '9条有依据的旧 Gold 保留，6条职业×国家组合待定；总人数30没有被拆成各职业人数。', 'unresolved': True})

    b(240, [1, 2, 4], 'repair_conditional_scope', [baseline['benchie_240'][1]],
      '保留原簇2的完整 if 表达。原簇1的无条件丢弃、原簇4的无条件 too small 都在这个条件命题中，不单独当作已发生事实计分。',
      evidence=['These objects are thrown away if their screen projection is too small'])
    b(240, [3], 'pending', [], 'their screen projection 可以表达对象与投影的指称联系，但单列 have 关系会增加原句未直接使用的关系表达；暂不决定删除整个事实。',
      unresolved='这里是否将 their screen projection 单列为对象具有投影的结构事实？试处理先保留原标注待确认。')
    coverage.append({'sentence_id': 'benchie_240', 'review': '条件与结果由1条完整 Gold 保留；不会把 if 条件当成已成立；对象—投影的单列关系待定。', 'unresolved': True})

    for c in range(1, 6):
        b(2, [c], 'keep', [baseline['benchie_2'][c-1]], '保留原句直接陈述的上铐对象、栏杆/窗户附着关系、留在那里和悬脚状态；允许原句插入成分间的有据组合。')
    b(2, [6, 8], 'merge_duplicate_fact', [baseline['benchie_2'][5]],
      '原簇6与8描述同一次被留下及相同 nearly five hours。选择原文主动表达 Graner left him there for，保留 nearly；不另计被动改写版本。',
      evidence=['Graner handcuffed him to the bars of a cell window and left him there', 'for nearly five hours'])
    b(2, [7], 'repair_source_expression', [triple('feet', 'dangling off', 'the floor')],
      '绝对结构 feet dangling off the floor 直接描述被留下者的脚部状态；恢复原文表达，去掉旧代表额外补入的 his 和 were，不删除该事实。',
      evidence=['feet dangling off the floor'],
      edits=[{'kind': 'remove_unnecessary_completion', 'removed_from_old': ['his', 'were'], 'restored_from_source': ['the'], 'detail': 'feet 指向同句被 Graner 留下的 him，由绝对结构依附关系确定。'}])
    coverage.append({'sentence_id': 'benchie_2', 'review': '8簇对应7个计分事实；主动与被动时长表达合并，保留脚部修饰事实及 nearly five hours。', 'unresolved': False})

    # DocOIE: chosen sentences are ORIGINAL gold targets; neighbours are context only.
    for domain, target_indices in [('transportation', [0, 2, 3]), ('healthcare', [0, 3, 8])]:
        raw_gold = read(DOC / f'DocOIE_{domain}_eval_gold.json')
        raw_context = read(DOC / f'DocOIE_{domain}_eval_sent.json')
        document_id = next(iter(raw_gold))
        for target_index in target_indices:
            sentence = list(raw_gold[document_id])[target_index]
            key = f'docoie_{domain}_doc0_target{target_index}'
            original_raw = raw_gold[document_id][sentence]['triple_gold']
            originals = [triple(t['sub'], t['rel'], t['obj']) for t in original_raw]
            snapshots[key] = originals
            original_refs[key] = set(range(1, len(originals)+1))
            group = f'docoie_{domain}'
            groups[group]['input'][key] = [sentence]
            groups[group]['gold'][key] = []
            positions = [i for i, s in enumerate(raw_context[document_id]) if s == sentence]
            assert len(positions) == 1
            pos = positions[0]
            context = [{'sentence': raw_context[document_id][i], 'context_index': i, 'evaluation_target': False}
                       for i in (pos-1, pos+1) if 0 <= i < len(raw_context[document_id])]
            source_map[key] = {'dataset': 'DocOIE', 'domain': domain, 'document_id': document_id,
                               'target_index_in_gold_document': target_index,
                               'context_index': pos, 'sentence': sentence, 'target': True,
                               'context_sentences': context, 'original_sub_rel_obj': original_raw}
            counts['docoie_original_triples'] += len(originals)
            def d(refs, action, outputs, reason, **kw):
                decide(group, key, refs, action, outputs, reason, **kw)
            if domain == 'transportation' and target_index == 0:
                for c, t in enumerate(originals, 1):
                    d([c], 'keep', [t], 'because 从句陈述背景原因，elements/operations 可以共享谓语；保留 do not 的局部否定。')
                d([], 'supplement', [triple('a discussion of such elements and operations', 'may not be provided', 'herein')],
                  '反向检查发现原 Gold 漏掉主句。直接保留 may not，不把可能不提供变成确定不提供；该事实与三个原因事实不同。',
                  evidence=['a discussion of such elements and operations may not be provided herein'])
                review = '原3条保留，补充原文明示但漏标的主句1条；未将上下文句加入目标。'
            elif domain == 'transportation' and target_index == 2:
                t = dict(originals[0]);t['head'] = 'validation of the vehicle identity'
                d([1], 'repair_typo', [t], '仅修正 vlidation 拼写，使其与原文 validation 一致。',
                  edits=[{'kind': 'typo', 'old': 'vlidation', 'new': 'validation'}])
                d([2, 5], 'merge_duplicate_fact', [originals[1]], '两条 components make up the vehicle 指向同句同一组成关系；合并重复，保留 the components。')
                d([3], 'pending', [], '长宾语中的 generated by... 限定信息来源，不能随意删除。更关键的是 as well as information 究竟与 integrity 还是 components 并列，影响 ensures 的范围。',
                  unresolved='原 Gold 的 ensures information 是否应为 ensures the integrity of information？不能在范围不明确时擅自补出 integrity；原标注原样保存。')
                d([4], 'keep', [originals[3]], '生成来源修饰语直接支持，保留 any of the components that make up the vehicle，以免扩大到任意组件。',
                  edits=[{'kind': 'existing_grammatical_completion', 'added_relative_to_source': ['is'], 'detail': '旧 Gold 已有 is；generated by 本身在原句中是被动修饰语，不是主动转被动。'}])
                review = '修正一处明确拼写；合并重复组成关系；保留完整生成来源限定。ensures 的并列范围仍有1项争议。'
            elif domain == 'transportation' and target_index == 3:
                for c, t in enumerate(originals, 1):
                    d([c], 'keep', [t], '既有拆分覆盖定义、括号同位说明、存储能力和格式可读性。computer readable medium 等术语不按词数拆分，不新增无依据的关系。',
                      edits=[{'kind': 'existing_grammatical_completion', 'added_relative_to_source': ['is'], 'detail': '原 Gold 已有系动词；来自括号同位结构或形容词修饰，不在本次另行补词。'}] if c in (2, 3, 4, 5) else [])
                review = '原5条已有合理拆分，全部保留；不因长术语继续拆分。'
            elif domain == 'healthcare' and target_index == 0:
                for c, t in enumerate(originals, 1):
                    d([c], 'keep', [t], 'a place 在两条中指向同一地点；relative clause is remote from 直接给出地点属性，保留 typically，不另加站点位置推论。')
                review = '原2条保留；长地点描述已由共享 a place 的关系分解，不额外扩充。'
            elif domain == 'healthcare' and target_index == 3:
                d([1, 2], 'repair_modal_scope',
                  [triple('the robot face', 'may have', 'a voice recognition system that allows the user to grant access with a voice command')],
                  '保留 may 和原句完整功能修饰。此处先用一个完整三元组保留可能配置的系统及其功能，不把这种可能配置直接写成已存在的系统实例。',
                  evidence=['The robot face may also have a voice recognition system that allows the user to grant access with a voice command'],
                  edits=[{'kind': 'restore_relative_clause_scope', 'detail': '把旧第二条的功能重新置于第一条的系统描述中；全部内容来自原句。'}])
                review = '两条合为1条保留 may 的完整系统描述；未删除功能，也未为拆分而新增现实存在断言。'
            else:
                d([1], 'keep', originals, '普通控制样本：原句和旧 Gold 均保留 may 及原文被动语态；旧标注的多余空格不影响语义，本次不为格式另作改动。')
                review = '原1条保留，不变更语态或情态。'
            coverage.append({'sentence_id': key, 'review': review,
                             'unresolved': domain == 'transportation' and target_index == 2})

    for key, refs in original_refs.items():
        used = [i for r in records if r['sentence_id'] == key for i in r['source_ids']]
        assert len(used) == len(set(used)) and set(used) == refs, key
    for group, data in groups.items():
        assert list(data['input']) == list(data['gold'])
        dump(OUT / group / 'input.json', data['input'])
        dump(OUT / group / 'gold.json', data['gold'])

    metrics = {}
    for group, data in groups.items():
        rs = [r for r in records if r['dataset'] == group]
        original_count = sum(len(snapshots[key]) for key in data['input'])
        metrics[group] = {
            'sentences': len(data['input']), 'old_representative_or_triple_count': original_count,
            'original_expression_rows': sum(len(c['expressions']) for key in data['input'] for c in source_map[key]['clusters']) if group == 'benchie_fl' else original_count,
            'original_fact_clusters': counts['benchie_original_clusters'] if group == 'benchie_fl' else None,
            'proposed_gold_count': sum(len(v) for v in data['gold'].values()),
            'duplicate_facts_reduced': sum(len(r['source_ids'])-len(r['new_annotations']) for r in rs if r['operation'] == 'merge_duplicate_fact'),
            'entire_facts_removed': sum(len(r['source_ids']) for r in rs if r['operation'] == 'remove_fact'),
            'scope_repair_net_reduction': sum(len(r['source_ids'])-len(r['new_annotations']) for r in rs if r['operation'] in ('repair_alternative_scope', 'repair_conditional_scope', 'repair_modal_scope')),
            'split_source_facts': 0, 'split_output_facts': 0,
            'supplemented_facts': sum(len(r['new_annotations']) for r in rs if r['operation']=='supplement'),
            'unresolved_source_items': sum(len(r['source_ids']) for r in rs if r['unresolved']),
            'zero_output_sentences': [key for key, ts in data['gold'].items() if not ts],
            'operations': dict(Counter(r['operation'] for r in rs)),
        }
        assert original_count - metrics[group]['duplicate_facts_reduced'] - metrics[group]['entire_facts_removed'] - metrics[group]['scope_repair_net_reduction'] - metrics[group]['unresolved_source_items'] + metrics[group]['supplemented_facts'] == metrics[group]['proposed_gold_count']
    dump(OUT / 'source_map.json', source_map)
    dump(OUT / 'original_gold_snapshot.json', snapshots)
    dump(OUT / 'decisions.json', records)
    dump(OUT / 'pending.json', disputes)
    dump(OUT / 'coverage_review.json', coverage)
    sources = [BENCH/'benchie-annotated_300.txt', BENCH/'before_source_grounded/gold.json', BENCH/'before_source_grounded/input.json']
    sources += [DOC/f'DocOIE_{d}_eval_{kind}.json' for d in ('transportation','healthcare') for kind in ('gold','sent')]
    dump(OUT / 'manifest.json', {'status': 'PILOT_AWAITING_USER_REVIEW_NOT_FOR_FORMAL_SCORING',
                               'rule_basis': 'User original prompt; minimal justified edits; no added adjacency/string filtering rules',
                               'source_dataset': 'BenchIE_FL, not original BenchIE; DocOIE transportation and healthcare',
                               'source_files': [{'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],
                               'metrics': metrics, 'unresolved_source_items': sum(m['unresolved_source_items'] for m in metrics.values())})

    report = ['AI生成', '', '# 原提示词试处理结果（待确认）', '',
              '本批仅处理12个目标句：BenchIE_FL 6句、DocOIE transportation 3句、healthcare 3句。未覆盖当前运行数据；不使用模型抽取结果决定 Gold。', '',
              'Gold 文件是试处理草案。待定条目保存在 pending.json 和 decisions.json 中；因此本批不用于正式评分。原始事实簇的全部备选表达保存在 source_map.json，未自动将所有备选判为合格或另计事实。', '',
              '## 数量', '', '| 数据 | 句子 | 原表达行 | 原事实簇 | 原代表/三元组 | 新 Gold | 重复合并减少 | 整事实删除 | 范围修复净减少 | 补充 | 待定原条目 |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name, m in metrics.items():
        report.append(f"| {name} | {m['sentences']} | {m['original_expression_rows']} | {m['original_fact_clusters'] if m['original_fact_clusters'] is not None else '不适用'} | {m['old_representative_or_triple_count']} | {m['proposed_gold_count']} | {m['duplicate_facts_reduced']} | {m['entire_facts_removed']} | {m['scope_repair_net_reduction']} | {m['supplemented_facts']} | {m['unresolved_source_items']} |")
    report += ['', '本批没有新增拆分操作（拆分原事实数0、新产生事实数0）；原 Gold 已有的合理拆分尽量保留。原始簇内多表达选择代表造成的表达行压缩不计为事实删除；范围修复与真正重复事实合并分开统计。', '',
               '## 逐句结果（两个指定案例在前）', '']
    for group, data in groups.items():
        for key, ts in data['gold'].items():
            report += [f'### {key}', '', source_map[key]['sentence'], '',
                       f"旧参考 {len(snapshots[key])} 条 → 本批明确提议 {len(ts)} 条。", '', '```text']
            report += ['(' + '; '.join(t[f] for f in FIELDS) + ')' for t in ts]
            report += ['```', '', next(c['review'] for c in coverage if c['sentence_id']==key), '']
            for r in records:
                if r['sentence_id']==key and r['operation']!='keep':
                    report.append(f"- 原编号 {r['source_ids'] or '新增'}：{r['operation']}。{r['reason']}")
            report.append('')
    report += ['## 待定项', '']
    for dispute in disputes:
        report.append(f"- {dispute['sentence_id']} 原编号 {dispute['source_ids']}：{dispute['question']}")
    report += ['', '## 文件使用与范围', '',
               '- `benchie_fl/`、`docoie_transportation/`、`docoie_healthcare/`：各自试处理 input/Gold；样本编号一致。',
               '- `source_map.json`：原始标注、事实簇全部备选、原始行号或文档与目标句位置；DocOIE 邻句仅标作 context，不进入待评测 input。',
               '- `decisions.json`：逐簇/逐三元组的原标注、新标注、操作、证据、补词/改写和判定理由。',
               '- `coverage_review.json`：逐句反向覆盖检查。',
               '- `pending.json`：未决问题；没有静默删除。',
               '- `original_gold_snapshot.json`：本批修改前参考，不覆盖源文件。',
               '- `manifest.json`：来源与统计。',
               '- `build_pilot.py`：人工明确决策的机械导出脚本，不是可直接推广到全量的字符串筛选器。', '',
               '数量骤减重点复核：benchie_228 的减少来自保留 or、撤销各校两类角色都存在的 has 断言；benchie_240 的减少来自保留 if 范围；benchie_34 的减少主要是6条职业×国家条目待定。没有零 Gold 句。确认本批规则与待定项后才扩大处理范围。', '']
    (OUT / '试处理结果.md').write_text('\n'.join(report), encoding='utf-8')
    print(json.dumps({'metrics': metrics, 'pending_items': len(disputes)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    build()
