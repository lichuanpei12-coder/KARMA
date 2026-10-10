# 数据目录：当前使用与候选参考

## 当前实验

- 输入：[DocOIE_transportation_gold_input.json](DocIOE/DocOIE_transportation_gold_input.json)。40 篇文档记录，每篇 10 个目标句；当前脚本选前 5 篇。
- Gold：[DocIOE/transport/](DocIOE/transport/)，`0.json` 对应第 1 篇，以此类推，共 1137 条三元组。
- `DocIOE` 中的 `eval_gold` 和 `eval_sent` 保留给逐句核查和理解上下文使用。完整上下文不是全部都有 Gold 的抽取目标。

正式抽取不读取 Gold。查看基线和第二轮运行结果时，先用文档 ID 和 `source_index` 确认配对，不能只看文件名猜样本。

## 供审查和后续扩展的参考

- [dataset_versions/版本目录说明.md](dataset_versions/版本目录说明.md)：保留原始快照、派生候选、审查状态和变更证据，尚未自动切换为默认数据。
- [docoie_recheck_20260915/复查结果.md](docoie_recheck_20260915/复查结果.md)：覆盖缺口和候选补充；并非全部已经写入 Gold。
- [gold_review_pilot_20260915/试处理结果.md](gold_review_pilot_20260915/试处理结果.md)：少量样本处理记录和争议。
- `BenchIE_FL_KARMA_Starter/`：活动目录为 267 句、623 条的历史严格筛选版，存在误删问题；保留用于追溯与适配参考，不要直接当作正式新实验 Gold。完整原版和其他候选见 `dataset_versions/`。
- [dataset_samples/](dataset_samples/)：候选样例与原结构说明，不代表全量检查或正式接入。旧材料中的本机绝对路径仅用于追溯。

## 未接入的下载数据

完整下载包仅本地保留，不随当前 Git 树分发。这里只保留来源，后续确需接入时重新核对版本和标注规则。

| 候选 | 下载来源（历史记录） | 当时查看的内容 |
|---|---|---|
| SpanSAOKE | [MGD-GNN 仓库](https://github.com/Lvzhh/MGD-GNN) | `data/train.json`、`dev.json`、`test.json`；存在特殊符号表达，未正式接入 |
| APRCOIE | [APRCOIE_v1 仓库](https://github.com/jialin666/APRCOIE_v1/tree/V_I) | `data_regular.json`、`data_att.json`；可还原三元组，完整性和评估仍需适配 |
| DuEE | 原电脑的 `DuEE1.0/` 下载材料 | 事件抽取结构，不能直接当开放三元组 Gold |

不能仅因数据有 subject/relation/object 字段就认定适用；还要检查关系开放性、原文依据、粒度、覆盖范围和评估适配。候选数据的讨论不改变当前 DocOIE 的运行配置。
