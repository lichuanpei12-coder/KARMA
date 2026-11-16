# BenchIE 中文版 · KARMA 输入与评估 Gold

| 文件 | 用途 | 结构 |
| --- | --- | --- |
| `benchie_zh_karma_input.json` | KARMA 抽取和反馈 | `doc_id` → 单元素句子列表，可传给 `main.py --input` |
| `benchie_zh_gold_clusters.json` | 事实簇评估 | `doc_id` → 事实簇列表。每个簇有 `cluster_id` 和 `variants`，每个变体有 `head`、`relation`、`tail` |

两个 JSON 均为 UTF-8。`doc_id` 形如 `benchie-zh-001`，末尾数字对应 BenchIE 原始 `sent_id`。KARMA 内部为每条样本的唯一源句分配 `S1`。评估按 `doc_id` 对齐运行清单与 Gold。

Gold 共 300 个样本、995 个事实簇、1,368 条原始标注行。第 249、294 句的 Gold 是空列表。事实簇评估器会展开方括号内的可选片段。

## 运行与评估

在 KARMA 根目录用 Git Bash 运行基线和反馈。基线脚本默认用这份中文输入，取前 5 个样本。反馈脚本读取这次生成的基线。 [基线脚本](../../../run_baseline.sh) · [反馈脚本](../../../run_revision.sh)

```bash
bash run_baseline.sh
bash run_revision.sh
python evaluate_benchie.py "实际的反馈输出目录"
```

将示例中的目录替换为反馈脚本打印的路径。评估器默认读取本目录的事实簇 Gold，输出 `benchie_evaluation/eval_benchie.json`。反馈清单有基线、拆分后和最终三个阶段，基线清单单独提供第一轮得分。评估器按本次运行的样本 ID 计分。

- `benchie_exact` 按 BenchIE 的事实簇精确命中规则统计。共享写法命中第一个匹配簇，重复命中次数单独列出。
- `han_overlap_lenient` 按字段计算汉字和其他字词的部分重合。每对预测与事实簇先选重合得分最高的合法写法，再按配对 F1 之和做一对一配对。三个对应字段都要有重合才允许配对。

评分报告包含总分、逐句预测、命中簇和未覆盖的簇。 [评分入口](../../../evaluate_benchie.py)

## 来源与转换记录

- 原句来自 [sample300_zh.txt](../data/sentences/sample300_zh.txt)，与 [中文 Gold 原始标注](../data/gold/benchie_gold_annotations_zh.txt) 中的 300 个句子头逐条一致。去掉用于逐字分隔的单空格，连续三个及以上的空格还原为一个普通空格，以保留 `Great Northern Nekoosa` 等多词名称。保留原标点和文字。
- 原始 Gold 第 2,080 行的 `2 0 6 :` 按前后编号还原为第 206 句的第 3 簇。保留其下一行三元组，因此派生 Gold 有 995 个独立事实簇。
- 原始 Gold 第 2,851 行（第 287 句第 3 簇）的客体中，`450万美元的]` 有一个落单的右方括号。派生版去掉这个括号，保留金额文字及其余成对的可选标记。
- 原始文件保留。数据来源为 [BenchIE](https://github.com/gkiril/benchie)，按其数据许可 CC BY 4.0 署名，研究引用见 [BenchIE 论文](https://aclanthology.org/2022.acl-long.307/)。
