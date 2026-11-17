# BenchIE 中文版 · KARMA 输入与评估 Gold

| 文件 | 用途 | 结构 |
| --- | --- | --- |
| `benchie_zh_karma_input.json` | KARMA 抽取和反馈 | `doc_id` → 单元素句子列表，可传给 `main.py --input` |
| `benchie_zh_gold_clusters.json` | 事实簇评估 | `doc_id` → 事实簇列表。每个簇有 `cluster_id` 和 `variants`，每个变体有 `head`、`relation`、`tail` |
| `benchie_gold_annotations_zh.txt` | 逐句查看参考标注 | 与评估 Gold JSON 同步，保留逐字分隔格式和事实簇编号 |

两个 JSON 均为 UTF-8。`doc_id` 形如 `benchie-zh-001`，末尾数字对应 BenchIE 原始 `sent_id`。KARMA 内部为每条样本的唯一源句分配 `S1`。评估按 `doc_id` 对齐运行清单与 Gold。

Gold 共 300 个样本、995 个事实簇、1,134 条标注记录。第 249、294 句的 Gold 是空列表。

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

整理标注时，簇内去重按三个字段合并后的词频判断。实际运行评分时，精确匹配和宽松匹配均在对应字段上比较，因此同词但字段划分不同的预测可能得到不同分数。

评分报告包含总分、逐句预测、命中簇和未覆盖的簇。 [评分入口](../../../evaluate_benchie.py)

## 来源与转换记录

- 原句来自 [sample300_zh.txt](../data/sentences/sample300_zh.txt)，与 [中文 Gold 原始标注](../data/gold/benchie_gold_annotations_zh.txt) 中的 300 个句子头逐条一致。去掉用于逐字分隔的单空格，连续三个及以上的空格还原为一个普通空格，以保留 `Great Northern Nekoosa` 等多词名称。保留原标点和文字。
- 原始 Gold 第 2,080 行的 `2 0 6 :` 对应第 206 句的第 3 簇。整理版按这个簇边界读入下一行三元组，共有 995 个独立事实簇。
- 第 2 句补上「铁栏杆」并将「悬在地板上」改为「悬空离地」。第 287 句原始 Gold 有一个落单的右方括号，整理版保留对应文字。
- 上游标注的方括号表示可选成分，例如 `[曾]担任` 可展开成「曾担任」和「担任」。本版去掉标记，保留括号内文字，评估时使用保留了可选成分的写法。
- 每个事实簇内对三元组两两计算词重合。沿用 KARMA 的分词方式，单个汉字算一个单位，非汉字文本转成小写，按空白和汉字边界分词。合并三个字段的词频，词项及次数完全一致时，保留一种语义边界较清楚的写法。共比较 671 对，合并 234 条重复记录，事实簇编号保持一致。
- 上游资料见 [BenchIE 原始标注](../data/gold/benchie_gold_annotations_zh.txt)。数据来自 [BenchIE](https://github.com/gkiril/benchie)，按 CC BY 4.0 署名。[BenchIE 论文](https://aclanthology.org/2022.acl-long.307/)
