# 中英文Prompt对照修改包

核查日期：2026年10月8日。已经确定采用中文Prompt。本地主目录已完成未提交的Prompt位置整理，实际措辞保持不变；规则修改草案尚未应用。

先打开 [中英文Prompt逐项对照与修改稿_合并后.md](<E:/huawei after/KARMA/GPT执行/中文Prompt审查_20261008/中英文Prompt对照修改包/中英文Prompt逐项对照与修改稿_合并后.md>)。其中16个修改项、61段源码摘录逐项配对，中文位置按实际AST重新定位，旧英文行号不变。原同名未带“合并后”的Markdown保留，避免覆盖此前草稿。

需要完整上下文时打开 [核心Prompt完整模板参考_合并后.md](<E:/huawei after/KARMA/GPT执行/中文Prompt审查_20261008/中英文Prompt对照修改包/核心Prompt完整模板参考_合并后.md>)。常量从实体/关系agent的AST读取，两轮共用规则已展开，动态输入保留占位；旧版没有文本重建和比较模块，不补造英文原文。

## 已核实的Git版本

| 本地目录 | 分支 | 当前提交 | 线上关系 |
|---|---|---|---|
| [E:\huawei after\KARMA](<E:/huawei after/KARMA>) | main | 127f1a1 | HEAD与最近核查的远程main一致；工作树已有未提交的位置整理 |
| [E:\huawei after\临时\KARMA](<E:/huawei after/临时/KARMA>) | codex/feedback-comparison-entity | 9d6883e | 与远程更新分支一致，领先main两个提交 |

线上仓库：[lichuanpei12-coder/KARMA](https://github.com/lichuanpei12-coder/KARMA)。更新分支最新提交：[9d6883e，评估：保留部分拒绝文档并单列无异常子集](https://github.com/lichuanpei12-coder/KARMA/commit/9d6883e2e56a008ecf70bb5ca695fead32a1abea)，北京时间2026年9月11日11:06:48。

更新分支只新增反馈对比实验文件及Evaluator的结果保存目录参数，没有修改核心Prompt。历史“8文件SHA256全部相同”记录保留，表示整理前的状态。当前主目录将ENTITY_RULES移回实体agent，将FACT_RULES/SCORE_RULES移回关系agent，两份difference_context各自保留；extraction_support仅保留工具。临时目录保持原版、本次未修改，因此这三个文件现在字节不同，当前实体/关系行号不适用于临时目录；其余五个已比较文件仍相同。

[合并验证结果.json](<E:/huawei after/KARMA/GPT执行/中文Prompt审查_20261008/Prompt合并整理/合并验证结果.json>)记录8个实际组装请求的system/user/parameters逐字一致、无网络调用。这证明位置整理未改Prompt，不代表草案已应用或真实模型效果已验证。

本次没有切换、拉取、合并或推送分支。主目录数据等存在本地变化；更新目录工作区是否干净没有在此作结论。

## 关于.git文件夹的9月21日修改时间

实查 `E:\huawei after\KARMA\.git` 的LastWriteTime为2026年9月21日00:20:48，但本地HEAD及其最新reflog提交记录仍为9月9日的127f1a1。目录修改时间表示管理目录发生变化，不能据此推断源代码提交或上传日期，也不能证明目录包含仓库所有分支的最新提交。

版本判断依据是当前分支及HEAD、线上分支提交号和二者差异；本次通过GitHub连接器直接核查线上分支，并与本地提交号比较。

## 附带文件

- [Git线上核查记录.json](<E:/huawei after/KARMA/GPT执行/中文Prompt审查_20261008/中英文Prompt对照修改包/Git线上核查记录.json>)：原线上及8文件相同记录保留；新增位置整理说明和当前逐文件equal比较。
- [摘录定位与校验_合并后.json](<E:/huawei after/KARMA/GPT执行/中文Prompt审查_20261008/中英文Prompt对照修改包/摘录定位与校验_合并后.json>)：61段当前摘录的绝对路径、行号、哈希和AST锚点；原摘录JSON保留。
- [提取Prompt对照.py](<E:/huawei after/KARMA/GPT执行/中文Prompt审查_20261008/中英文Prompt对照修改包/提取Prompt对照.py>)：只读取源码，不导入代理或调用模型；从未改动的临时副本取得历史摘录锚点，按AST定位当前源码，原文不匹配时明确报错。重跑生成带“合并后”的两份Markdown与JSON，不覆盖原稿。直接编辑新版草稿后，重跑前应另存编辑内容。
