"""Read original DocOIE and write an evidence report, never rewrite Gold."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'data/DocIOE'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    data = {d: read(SOURCE / f'DocOIE_{d}_eval_gold.json') for d in ('transportation', 'healthcare')}
    context = {d: read(SOURCE / f'DocOIE_{d}_eval_sent.json') for d in data}
    findings = []

    def add(domain, di, si, triples, reason, notes='无需新增词；按原句分配三元组槽位。'):
        title, targets = list(data[domain].items())[di]
        sentence, annotation = list(targets.items())[si]
        lines = context[domain][title]
        pos = lines.index(sentence)
        findings.append(dict(
            sentence_id=f'docoie_{domain}_doc{di}_target{si}', domain=domain,
            document_title=title, document_index=di, target_index=si,
            source_sentence=sentence, context_before=lines[max(0, pos-1):pos],
            context_after=lines[pos+1:pos+2], original_gold=annotation['triple_gold'],
            proposed_additions=[dict(zip(('sub', 'rel', 'obj'), t)) for t in triples],
            reason=reason, wording_notes=notes,
            status='coverage_gap_identified_expression_proposed_not_applied'))

    def t(di, si, triples, reason, notes='无需新增词；按原句分配三元组槽位。'):
        add('transportation', di, si, triples, reason, notes)

    t(1, 4, [('such illustration and description', 'are to be considered', 'illustrative or exemplary and not restrictive')],
      '原 Gold 仅覆盖 While 从句的 illustrated/described，漏了主句；保留 are to be considered、or 和 not，不拆成无条件属性。')
    t(1, 7, [('specific terms', 'are employed', 'herein')],
      '原 Gold 覆盖术语的使用方式及不用于限制，但没有标出 Although 从句的术语被采用这一事件。')
    t(5, 8, [('It', 'is', 'light-weight')],
      '原 Gold 只有同传统螺母重量相同及比两件式轻的比较，漏了直接表达的 light-weight 属性；不凭常识补重量数值。')
    t(8, 5, [('Skins in the back', 'are', 'taken out')],
      '原句明确并列 taken out 和 placed，Gold 只有 placed 及其目的，没有 taken out。',
      '沿用被动语态；采用系动/助动词与分词分槽，不另加宾语占位符。')
    t(8, 6, [('the regenerated nerve segments', 'are then harvested at', 'one or two weeks post surgery')],
      '原 Gold 标了灌注和切片，漏了 harvested；保留句首时间及 then，不把 one or two 展开成两个确定时间。',
      '时间取自同句句首 At 短语；仅调整位置与大小写，不新增时间信息。')
    t(9, 3, [('Processes for modifying electric motorcycles', 'are also', 'provided')],
      '原 Gold 仅有这些过程可以包含安装防撞杆，漏了主句 Processes ... are also provided。')
    t(11, 7, [('an exemplary locking mechanism', 'has been', 'illustrated'),
              ('any other suitable rotational locking mechanism', 'can be used in', 'other embodiments')],
      '该目标句原 Gold 为空；让步从句说明已展示示例机构，主句说明其他实施例可使用其他适当机构。两条均有明示依据，保留 can 和 other embodiments。',
      '主句中的 in other embodiments 前置短语移入关系/宾语；没有把 can 改成确定使用。')
    t(28, 6, [('the difference among the yields', 'will be significant as',
              'the standard deviation increases, or more printed inverters are serially cascaded')],
      '该目标句原 Gold 为空；保留完整 as 条件/变化关系和 or，不单独断言标准差已经增加，也不把两个分支都当成已发生。',
      '调换前置 as 从句位置；as 的具体因果/条件读法不作额外推断。')
    t(30, 6, [('a hierarchy of the mapping servers', 'can be created such that',
              'scalable policy distribution can be achieved')],
      '该目标句原 Gold 为空；保留 can 和 such that，使用一条带完整结果结构的候选，暂不拆为两个无条件事件。')
    t(32, 5, [('twenty buffer elements', 'are', 'shown')],
      '原 Gold 只有可以采用任意合适数量，漏了 although 从句明确说图中显示20个；不将20认定为系统必要数量。')
    t(13, 4, [('the potential violation', 'is', 'identified')],
      '原 Gold 仅覆盖给驾驶员或责任方发送消息，漏了并列主句前半的违规被识别。')
    t(29, 9, [('the canister', 'is', 'very small and lightweight')],
      '原 Gold 只覆盖可能缺乏足够冲量及方向，漏了 Since 从句明说的小且轻的属性；保留原合并属性，不靠拆两个形容词增加数量。')
    t(33, 3, [('the administrative requirements for food service licensing', 'have become', 'more strict')],
      '原 Gold 有 requirements 的 for 修饰关系及后续所需努力，却没有 have become more strict 的主断言。')
    t(38, 9, [('This tape', 'can then be discarded after', 'the repair is complete')],
      '原 Gold 只标记胶带移除，漏了并列 discarded；保留共享 can 和维修完成后的时间限制。原移除条目本身也应另行补回时间限制。',
      '共享原句 can then be 和 after 时间结构；不能改成已经丢弃。')
    t(24, 1, [('jerking steering movements and hence high quasi-static transverse forces',
              'are experienced as a result of', 'contact with the wheel flange')],
      '原 Gold 只有横向力可能超限，漏了接触轮缘导致所述运动及横向力的主句；保持并列和 hence，不机械交叉展开。',
      'As a result of 前置因果短语移入关系，使用原词。')
    t(22, 3, [('Such issues', 'can be particularly troublesome when',
              'the industrial process is located in a remote area, or when the service personnel are inexperienced in diagnosing network related problems')],
      '原 Gold 仅标了两个条件内部的命题，漏了主句问题在这些条件下可能特别棘手；整条保留 can、when 和 or。旧的两个无条件条目存在范围问题，不能据此认可。')
    add('healthcare', 8, 8, [('The applied frequency', 'is in line with', 'the above descriptions')],
        '原句列举 type、route、form、frequency、uses，原 Gold 分别覆盖其余四项，却漏了 frequency；属于直接并列漏项，不是推断新的用途。',
        '共享 are all in line with ...，单数主语将 are 调整为 is，与旧 Gold 其他单数并列项的做法一致；省去集合分配词 all。')

    # Reproduce the selection of sentences whose complete sentence/Gold pairs
    # were displayed and read during this turn. Ranking ONLY selects reading
    # order; it never decides whether a fact is true or changes an annotation.
    stop = set('a an the of to in on at by and or as is are was were be been being it this that these those which who for with from also all such its their they have has had not may can will would should shall could must'.split())
    words = lambda s: set(re.findall(r'[a-z]+', s.lower()))
    reviewed = []
    stats = {}
    for domain, documents in data.items():
        ids = set()
        ranked = []
        empty = []
        for di, (doc, targets) in enumerate(documents.items()):
            for si, (sentence, annotation) in enumerate(targets.items()):
                gold = annotation['triple_gold']
                if not gold:
                    empty.append(f'docoie_{domain}_doc{di}_target{si}')
                if 1 <= di <= 9 or (di >= 10 and len(gold) <= 1):
                    ids.add((di, si))
                if di >= 10 and len(gold) > 1:
                    unmatched = words(sentence) - words(' '.join(' '.join(t.values()) for t in gold)) - stop
                    ranked.append((len(unmatched), di, si))
        ids.update((di, si) for _, di, si in sorted(ranked, reverse=True)[:25])
        reviewed.extend(f'docoie_{domain}_doc{di}_target{si}' for di, si in sorted(ids))
        stats[domain] = dict(documents=len(documents), target_sentences=sum(map(len, documents.values())),
                             original_triples=sum(len(a['triple_gold']) for ts in documents.values() for a in ts.values()),
                             sentence_gold_pairs_read_this_turn=len(ids), original_zero_gold_sentences=empty)
    extra = [
        dict(domain='transportation', doc=6, target=3, kind='repair_not_add',
             issue='原 Gold are with reference to 丢失主谓 described，应修复原条目，不直接当第二事实加一。'),
        dict(domain='transportation', doc=8, target=8, kind='scope_review',
             issue='not described in details 只描述所限定的那组 processes and methods；若拆出需同时保留 following examples 和指代范围，未计入18条。'),
        dict(domain='transportation', doc=9, target=4, kind='grammatical_completion_review',
             issue='brochure filed herewith 可恢复独立事实，但是否补入 is/was 涉及时态；未计入18条。'),
        dict(domain='healthcare', doc=14, target=0, kind='split_not_missing',
             issue='advertising/scanning/initiating 已包含在原宾语中；展开是粒度调整，不是发现三项漏标。'),
        dict(domain='healthcare', doc=16, target=6, kind='split_not_missing',
             issue='四种服务器都在原 Gold 宾语中，拆成四条不是四个此前缺失的事实，且要保留 may。'),
        dict(domain='healthcare', doc=0, target=3, kind='previous_merge_disputed',
             issue='前次因 may 作用范围将两条合一，是否需要合并待定；本轮未改候选版。'),
        dict(domain='healthcare', doc=0, target=6, kind='previous_merge_disputed',
             issue='前次因 would be desirable 范围将两条合一，是否需要合并待定；本轮未改候选版。'),
    ]
    source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.glob('*_eval_*.json'))}
    report = dict(status='AUDIT_ONLY_NO_GOLD_MODIFIED', source_sha256=source_hashes, corpus_stats=stats,
                  sentence_gold_pairs_read_this_turn=len(reviewed), read_sentence_ids=reviewed,
                  findings_sentence_count=len(findings), proposed_addition_count=sum(len(f['proposed_additions']) for f in findings),
                  findings=findings, separate_issues=extra,
                  limitations='800句做了结构统计，本轮304句逐句查看了目标句及Gold；重点缺口进一步核对上下文。不是800句全部语义审查完成，18不是全数据集漏标总数，也不代表已应用修改。')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    md = ['AI生成', '', '# DocOIE 漏标重新检查', '',
          '本轮仅检查和报告，未修改任何原版或候选版 Gold。', '',
          '原始范围：交通40篇400目标句1137条；医疗40篇400目标句921条。完整上下文不是额外评估目标。', '',
          '本轮对照查看304个此前未审查目标句（交通142、医疗162），并对下列缺口检查相邻上下文。另有先前20句，本轮不重复计数。800句的逐条语义审查尚未完成。', '',
          '发现17句的覆盖缺口，提出18条补充候选：交通17条、医疗1条。包括交通3个原Gold为空的句子。18不包含上一轮新增的2条，也不是整个数据集漏项的总数。', '',
          '“补充候选”表示原文存在未覆盖内容，但具体三元组槽位尚未应用到Gold；不以增加条数为目的。并列长宾语已覆盖的信息、重复改写及修复条目不算新增事实。', '',
          '下列 doc/target 序号均从0开始，来自原始 JSON 顺序；每项同时提供完整文档标题、目标句和原标注，避免仅靠数字定位。', '']
    for i, f in enumerate(findings, 1):
        md += [f'## {i}. {f["sentence_id"]}', '', f'文档：{f["document_title"]}', '',
               '原句：' + f['source_sentence'], '', '原 Gold：', '', '```text']
        md += ['(' + '; '.join(t.values()) + ')' for t in f['original_gold']] or ['[]']
        md += ['```', '', '补充候选：', '', '```text']
        md += ['(' + '; '.join(t.values()) + ')' for t in f['proposed_additions']]
        md += ['```', '', '理由：' + f['reason'], '', '措辞处理：' + f['wording_notes'], '']
    md += ['## 单列的问题，不计入18条', '']
    md += [f'- {e["domain"]} doc{e["doc"]}/target{e["target"]}：{e["issue"]}' for e in extra]
    md += ['', '结论：此前只添加2条是小范围试处理的结果，不足以表示DocOIE的完整漏标情况。还需要对剩余目标句进行语义复核，再确定最终新增、修正和保留列表。', '',
           '机器可读的完整原句、原Gold、相邻上下文、候选和本轮304句ID清单见同目录 audit.json。', '']
    (OUT / '复查结果.md').write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'sentence_gold_pairs_read_this_turn', 'findings_sentence_count', 'proposed_addition_count')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
