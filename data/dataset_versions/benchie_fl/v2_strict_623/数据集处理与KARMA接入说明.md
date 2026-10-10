AI生成

> 版本提示：下文记录的是2026-09-08的旧版处理（299个样本、1,806条 Gold）。2026-09-14已按“原文依据、禁止补词和语态转换”的新要求重选，当前为267个样本、623条 Gold。请优先阅读同目录《原文严格重选说明.md》；旧版完整 input/Gold 已保存在 `before_source_grounded/`。当前20个分片也已更新，不能继续与旧版抽取结果按顺序混用。

# BenchIE^FL Starter 数据集处理与 KARMA 接入说明

记录日期：2026-09-08。本文记录当前已完成的修改、处理理由、操作顺序、使用方法和验证范围，方便复现与交接。

## 1. 目标与适用范围

将 BenchIE^FL Starter 接入现有 KARMA，作为句子级开放关系三元组抽取的数据源，并用项目现有 `evaluate.py` 比较两轮抽取结果。

这里的“开放”指关系不限定在预先列出的关系集合中，例如 `served as`、`became` 可以直接成为关系文本。`benchie_1` 是样本编号，不是关系 schema。

该数据集每个样本只有一句话，适合测试句子内事实抽取；不能单独验证长文档处理、跨句指代和文档级关系抽取能力。

## 2. 原始来源与 Starter 已有转换

- 官方仓库：https://github.com/rali-udem/benchie_fl
- 官方 Gold：https://github.com/rali-udem/benchie_fl/blob/main/gold/benchie-annotated%28300%29.txt
- 论文：https://arxiv.org/abs/2407.16860

本地 `benchie-annotated_300.txt` 与核对时的官方 Gold 文本一致，仅在文件末尾多一个换行。该原始文件未被本次清理和拆分修改，可以用于追溯。

官方标注使用事实簇（cluster）：同一个事实可以有多种合法三元组表达；方括号中的词表示可选词。Starter 到手时已经将每个事实簇简化为一条代表三元组，放入 `gold.json`。本次没有重新执行这个转换，也没有确认其选择代表表达的全部规则；已确认转换后的三元组数量与原始事实簇数量逐样本一致。

原始文本包含300个句子编号，其中第109句没有 Gold 三元组。Starter 原有 `input.json` 和 `gold.json` 均不包含 `benchie_109`，剩余299个样本。这个缺口是到手时已有的处理，本次保留原编号，没有重新编号补齐。

## 3. 修改前后数据量

| 项目 | 清理前 | 清理后 |
|---|---:|---:|
| input 样本数 | 299 | 299 |
| Gold 样本数 | 299 | 299 |
| Gold 三元组数 | 1,822 | 1,806 |
| 含 XXX 的 Gold 三元组数 | 16 | 0 |
| 空 Gold 样本数 | 0 | 0 |

删除操作涉及15个样本，其中 `benchie_23` 删除2条，其余受影响样本各删除1条。

## 4. 清理 XXX 的原理与步骤

部分 Gold 形如 `(game, ended, XXX)`。其中 `XXX` 是缺少宾语时使用的占位符，不能作为普通尾实体参与当前知识三元组处理。根据用户要求，删除含该占位符的整条 Gold 三元组。

实际步骤：

1. 读取完整 `gold.json`，遍历每个样本的三元组列表。
2. 检查 `head`、`relation`、`tail` 是否有字段等于字符串 `XXX`。本次找到的16条均为 `tail == "XXX"`。
3. 先统计删除数量和受影响样本，确认删除后不会有样本变成空列表。
4. 从完整 `gold.json` 删除这16个三元组对象，并正确处理 JSON 逗号。
5. 重新解析文件，确认 JSON 有效、仍有299个样本、剩余1,806条三元组，且无 XXX、无空 Gold。

这里删除的是 Gold 中的三元组，不是对应的输入句子。每个受影响样本仍有其他合法 Gold，因此 `input.json` 无需删样本。

本次没有修改原始标注文本，删除内容可从原始文本追溯恢复。以后若按官方完整任务进行评测，应使用原始标注，而非这个过滤版本。

## 5. 保留 benchie_ID 的原因

输入结构示例：

```json
{
  "benchie_1": ["He served as the first Prime Minister of Australia ..."]
}
```

Gold 结构示例：

```json
{
  "benchie_1": [
    {"head": "He", "relation": "served as", "tail": "Prime Minister"}
  ]
}
```

编号把原文与 Gold 联系起来，也能对应官方 `sent_id`。保留编号便于人工定位、检查配对和后续实现按 ID 对齐。

当前 KARMA 的 `_load_document()` 对 JSON 调用 `d.values()`，将每个列表中的字符串用空格拼接。编号不参与拼接，因此不会作为输入文本发送给模型。直接删键并改成顶层数组，会与当前加载逻辑不兼容。

注意：当前输入加载器和 Gold 加载器最终都只返回内容列表，没有把 ID 传入后续评分。实际评分仍依赖顺序，并不自动按 `benchie_ID` 匹配。此次拆分保证了两侧键的顺序一致。

## 6. 拆成20份的原理与步骤

拆分用于缩短单次运行、便于查看和分批管理。每批包含多个独立句子；没有把约15个句子合并为一篇文档。KARMA 仍逐个样本执行抽取。

实际步骤：

1. 在完成 XXX 清理后，读取完整 `input.json` 和 `gold.json`。
2. 获取 input 中原有的样本顺序，检查 Gold 样本数量相同且所有 ID 存在。
3. 设定20个分片，每片上限为 `ceil(299 / 20) = 15` 个样本。
4. 按顺序切片：第0片取位置0～14，第1片取位置15～29，依此类推。
5. 对每片使用同一组 ID，分别从 input 和 Gold 取值，生成配对的两个 JSON 对象，保留样本 ID 和原顺序。
6. 写入 `input/0.json`～`input/19.json` 以及 `gold/0.json`～`gold/19.json`，使用 UTF-8 无 BOM 编码。
7. 生成 `batch_manifest.json`，记录每批编号、文件位置、样本数、三元组数和首尾样本 ID。
8. 按数字顺序合并20份，验证内容及键顺序与完整文件一致。

结果：前19份各15个样本，最后一份14个样本。共299个样本、1,806条 Gold。第7份跨过缺失的 `benchie_109`，仍按15个实际样本计数。

目录结构：

```text
BenchIE_FL_KARMA_Starter/
├── benchie-annotated_300.txt   # 保留的原始事实簇标注
├── input.json                # 完整输入
├── gold.json                 # 清理后的完整 Gold
├── input/
│   ├── 0.json
│   ├── ...
│   └── 19.json
├── gold/
│   ├── 0.json
│   ├── ...
│   └── 19.json
├── batch_manifest.json
└── 数据集处理与KARMA接入说明.md
```

这些分片是由完整文件生成的副本。以后若修改完整 Gold，分片不会自动更新，需要重新生成并复核一致性。

## 7. evaluate.py 改了什么

只调整了 Gold 加载函数和相关命令行提示，没有修改评分算法、阈值或两轮结果的匹配规则。

原来的 `load_gold()` 只支持目录，并将每个数字命名 JSON 文件当作一个样本。因此，仅将299个样本拆成20个文件，并不能自动兼容原来的评测器：文件代表一个批次，而原逻辑认为文件代表一个样本。

现在 `load_gold(gold_source)` 统一返回“样本三元组列表的列表”，具体逻辑为：

- 参数是文件：直接解析这个文件。
- 文件根节点为列表：视为单个样本，兼容 DocIOE 旧格式。
- 文件根节点为对象：按对象内部顺序取各样本对应的三元组列表，展开为多个样本；若样本值不是列表则报错。
- 参数是目录：按文件名的数字顺序读取 JSON，再把各文件返回的样本列表依次合并。该目录内的 JSON 文件名必须能转换成整数。

因此支持以下调用来源：

| Gold 来源 | 加载得到的样本数 |
|---|---:|
| `data/DocIOE/transport` | 40 |
| `data/BenchIE_FL_KARMA_Starter/gold/0.json` | 15 |
| `data/BenchIE_FL_KARMA_Starter/gold/19.json` | 14 |
| `data/BenchIE_FL_KARMA_Starter/gold.json` | 299 |
| `data/BenchIE_FL_KARMA_Starter/gold` | 299 |

不要将整个 Starter 根目录当作 Gold 目录传入，它包含 `input.json` 等非数字命名、用途不同的文件。

当前对齐规则仍是：Gold 样本 `i` 对应抽取输出序号 `2*i`（第一轮）和 `2*i+1`（第二轮）。前19批每批正常应产生30个抽取结果文件，最后一批28个；完整数据正常应产生598个。这里不包含 `_dump_...` 等调试文件。

默认设置没有切换：不指定 Gold 参数时，当前候选与默认路径仍指向 DocIOE Transportation。使用 BenchIE 必须显式传入对应 Gold 文件或目录。

## 8. 运行方式

在已安装依赖并配置 API 的 PowerShell 中，进入项目目录：

```powershell
cd "E:\huawei after\KARMA"
```

先运行第0批：

```powershell
python main.py --input "data/BenchIE_FL_KARMA_Starter/input/0.json" --domain general
```

抽取完成后，将下面的 `实际时间戳目录` 替换成本次在 `data/result` 下生成的目录名，再评分：

```powershell
python evaluate.py "data/result/实际时间戳目录" "data/BenchIE_FL_KARMA_Starter/gold/0.json"
```

其他批次同理：输入第几批，就使用同编号 Gold 和该批次自己的结果目录。不能将某个分片的结果与完整 Gold 配对。

完整数据一次运行和评分：

```powershell
python main.py --input "data/BenchIE_FL_KARMA_Starter/input.json" --domain general
python evaluate.py "data/result/实际时间戳目录" "data/BenchIE_FL_KARMA_Starter/gold.json"
```

完整数据的评分也可将第二个参数替换为 `data/BenchIE_FL_KARMA_Starter/gold`。

`--domain general` 用于传入一般领域上下文；这不代表项目内所有智能体原有的生物医学提示词都已改为通用提示词。本次没有修改这些提示词，实际抽取质量仍需通过真实运行评估。

20批分别运行后，当前程序不会自动汇总20个结果目录。不要直接平均各批 F1 当作全量微平均指标；若需要全量指标，应统一汇总匹配计数或增加经过验证的跨批评测逻辑。

## 9. 已完成的验证与结论边界

本地验证实际导入了 `KARMAPipeline` 和 `evaluate`，调用现有 `_load_document()`、`load_gold()` 以及三元组文本序列化函数。为避免初始化模型客户端和创建运行目录，使用未初始化的管线对象，仅调用不依赖客户端的 JSON 加载方法。

已通过：

- 20个 input 分片均能被实际 KARMA 加载函数读取。
- 20个配对 Gold 分片均能被实际评测加载函数读取。
- 每批 input 与 Gold 的 ID 顺序、样本数量一致。
- 输入文本非空；Gold 非空；head、relation、tail 均为非空字符串且不含 XXX。
- 完整输入与分片重组后的加载结果一致。
- 完整 Gold 文件、Gold 分片目录和分片重组后的加载结果一致。
- 总计299个样本、1,806条三元组。
- 旧 DocIOE Gold 目录仍能加载40个样本。
- 修改后的评测脚本通过语法检查。

结论：数据结构、加载接口和现有样本顺序已支持切换。上述检查没有调用模型或 embedding API，没有执行完整抽取及评分，不能据此断言网络、额度、模型响应和完整管线全部正常。下一步应以第0批进行真实端到端验证。

## 10. 如何解释评测结果

当前 Starter 已将官方事实簇压缩为单条代表三元组，并删除16条 XXX Gold。项目 `evaluate.py` 使用三元组文本的向量相似度、头尾相似度检查及现有匹配计数规则，不是官方 BenchIE^FL 评分实现。

因此结果应描述为“基于 BenchIE^FL Starter 清理版本、使用 KARMA 项目评测器得到的成绩”，不能直接称为官方 BenchIE^FL 成绩。代表表达压缩可能影响合法变体的匹配，删除 XXX 也改变了评测目标集合。

本地 DocIOE 与本版本规模比较：

| 数据集 | 输入单位数 | 有 Gold 的句子数 | Gold 三元组数 |
|---|---:|---:|---:|
| BenchIE^FL Starter（清理后） | 299个单句样本 | 299 | 1,806 |
| DocIOE Transportation | 40篇文档 | 400 | 1,137 |
| DocIOE Healthcare | 40篇文档 | 400 | 921 |
| DocIOE 两领域合计 | 80篇文档 | 800 | 2,058 |

BenchIE 的 Gold 比单独的 Transportation 更多，但输入粒度是单句。比较抽取能力时，应同时说明句子级与文档级任务差异及评分方法。
