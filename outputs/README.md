# 示例结果说明

当前 Git 保留的是第一篇文档的可复核示例，不是前 5 篇批量实验的结果。

| 目录 | 内容 |
|---|---|
| [baselines/first_document_20261009_60671500](baselines/first_document_20261009_60671500) | 第一轮结果、固定基线包及过程记录 |
| [revisions/first_document_20261009_60671500](revisions/first_document_20261009_60671500) | 在同一基线上的第二部分结果；修订记录已补充 before/after |
| [evaluation_20261010/baseline](evaluation_20261010/baseline) | 第一轮严格/宽松评估 |
| [evaluation_20261010/revision](evaluation_20261010/revision) | 两轮严格/宽松评估与匹配 CSV |
| [第一篇结果对照](first_document_20261009_60671500/第一篇结果对照.md) | 人工整理的原文和修改前后示例 |

示例使用 API 模式 1、模型 gpt-5.5。读取清单里的模型和代码哈希了解生成时的配置；不能把历史示例当成当前源码重跑的结果。

运行自己的 5 篇实验时使用新的输出目录，保留模型、基线哈希、输入/Gold 版本和修改说明。不要覆盖已有示例，也不要因为这里已经有 baseline 就误以为 `outputs/current_baselines.txt` 已生成；该文件要由成功运行 `run_baseline.sh` 后写出，或在 revision 脚本中显式指定基线。

旧文献/研究计划的渲染输出、旧运行与旧评估示例已从 Git 当前树移除，本地保留。根目录的 [同事上手说明](../同事上手说明.md) 介绍具体运行和阅读步骤。
