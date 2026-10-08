# KARMA 项目聊天交接说明

请将本文作为新对话的背景，不需要复述全文。后续使用中文回答；遇到重复概念仍请耐心解释，并指出该概念此前在哪个问题中出现过。

## 项目背景

- 本地项目：`E:\huawei after\KARMA`
- 项目目标：使用 KARMA 从长文档中抽取知识三元组，并寻找合适、可靠的评估数据集。
- 三元组格式：`(head, relation, tail)`。
- 需要严格区分：
  1. 输出 JSON schema，例如固定使用 `head/relation/tail`；
  2. 关系 schema，即是否预先限定只能使用某些关系类型。
- “开放式三元组抽取”允许固定输出格式，但不预先封闭实体类型和关系类型；关系应根据原文产生，并保留否定、情态和条件。

## 已确认的 DocOIE 情况

- 正式名称是 **DocOIE**；本地目录 `data/DocIOE` 是命名拼写问题。
- 官方 transportation evaluation 数据有 40 篇文档、400 个句子、1202 条 Gold。
- 官方 Gold 中有 65 条三元组存在空字段；本地清理后剩余 1137 条。
- 本地 `data/DocIOE/transport/0.json` 到 `39.json` 与官方非空 Gold 逐条、顺序完全一致，所以扁平化过程没有引入内容错误。
- 官方 Gold 本身存在明显噪声，例如：
  - `validation` 被写成 `vlidation`；
  - `blink duration` 更新关系重复，漏掉 `blink frequency`；
  - 并列成分错误组合；
  - 不完整或自指三元组。
- 因此 DocOIE 的评估分数只能解释为“与该参考标注的一致程度”，不能直接等同于事实正确率。
- 官方仓库：https://github.com/daviddongkc/DocOIE

## 已讨论的 CUAD

- 510 份英文商业合同、41 类条款、约 13,000 条专家标注。
- Gold 是条款类别、证据片段和派生答案，不是开放三元组。
- 适合法律条款识别与证据定位，不适合直接替换 DocOIE 评估开放三元组。
- 官方页面：https://www.atticusprojectai.org/cuad/

## 已讨论的 Kleister-NDA

- 540 份 NDA、3229 页、2160 个 Gold 值。
- 固定抽取四类字段：`effective_date`、`jurisdiction`、`party`、`term`。
- Gold 位于官方仓库：
  - `train/expected.tsv`
  - `dev-0/expected.tsv`
  - `test-A` 的正式测试答案隐藏。
- Gold 是文档级规范化 `key=value`，没有为绝大多数文档提供证据跨度。
- 它可转换为固定关系三元组，例如 `(contract, jurisdiction, New York)`，但只能测试固定字段抽取，不能证明开放关系抽取能力。
- 官方仓库：https://github.com/applicaai/kleister-nda

## 当前尚未决定的问题

需要继续判断应该选择哪种评估路线：

1. 保留 DocOIE，用人工审校后的 Gold 评估开放式抽取；
2. 选择其他真正的 OpenIE/关系抽取数据集；
3. 增加 Kleister-NDA，作为固定 schema、长文档字段抽取的补充实验；
4. 分别评估“开放事实发现”和“固定字段抽取”，避免用一个分数混合不同任务。

后续回答应优先围绕用户当前问题推进，不要自动改代码或下载数据；如果需要检查具体文件，请先让用户上传相应文件，因为网页端不能直接访问上述本地工作区。
