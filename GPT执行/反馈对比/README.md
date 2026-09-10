# 实体与关系反馈对比实验

仅用于这份临时副本。原 `main.py`、`pipeline.py`、正式提示词保持不变。
运行入口为本目录的 `compare_feedback.py`。已有另一台电脑上的关系-only实验无需搬过来。

## 输入与流程

从输入JSON的原始键顺序取得文档编号。默认取0、8、16、24、32、39，`--docs all`可选全部。
每篇统一执行一次：原文规范化 → E1 → 关系抽取与相同后处理 → T1 → 文本B → diff。
第一轮diff固定为空，不复用其他文档的反馈。

第二轮分别执行：

- 重新抽取：源文本+diff → **新调用实体Agent得到E2-R** → 源文本+E2-R+diff → 完整T2。
- 增量抽取：源文本+E1+T1+diff → **新调用实体审校Agent得到E2-I** → 源文本+E2-I+T1+diff → 操作 → 完整T2。

E2不是实验输入。两条路径的E2可以不同。实体审校仍输出完整列表，关系增量输出add/remove/replace。
重新抽取复用当前副本的公共抽取规则，并非逐字恢复历史版本的全部提示词。
这是两套实体+关系反馈策略的比较，不能单独归因于关系操作格式或模型“锚定”。

共用当前事实规则、去重、冲突处理、Evaluator阈值0。Schema仍停用。
文档独立处理，冲突处理的既有图为空，两分支不会受到对方或其他文章输出影响。
Reader没有执行：当前默认流程中抽取用normalized_content，未使用Reader的输出。
默认关闭Summarizer，显式加`--use-summarizer`才开启，不读取KARMA_USE_SUMMARIZER开关。
这两点在每次manifest里记录；不是声称完整复刻历史运行。

## 命令（在临时副本根目录执行）

```powershell
python "GPT执行/反馈对比/compare_feedback.py" --dry-run
python "GPT执行/反馈对比/test_comparison.py"
python "GPT执行/反馈对比/compare_feedback.py" --run
```

`--dry-run`只核对数据、保存输入与Gold/code快照，不调用API；也不会假造尚未生成的E1/T1/E2请求。
`--run`才真正调用。关闭Summarizer且没有空结果或失败时，每篇通常8次逻辑调用，6篇约48次；重试增加HTTP请求数。
API模式默认读取本副本main.py的API_MODE常量，支持0/1；也可用`--api-mode 0`或`--api-mode 1`覆盖。
认证/代理从本副本加载的环境配置读取，沿用已有环境变量优先规则；不写回.env。
每个模型请求为独立会话。完整回复与每次重试持久化；401/403停止整批。解析失败/截断/回退不会标为成功。
默认每个请求最多重试2次，超时600秒，重试配置保存在manifest中。

## 集中保存的比较材料

每次输出一个`runs/run_时间戳/`目录，模拟检查输出使用临时目录，不能当作真实实验。

```text
manifest.json                 配置、范围、编号映射、实际运行状态、逻辑/HTTP调用数
code_snapshot/                本次代码、提示词来源、evaluate.py冻结副本（不含.env）
code_hashes.json               代码SHA256
gold/doc_008.json              原编号Gold快照，保留原样，不额外清理或去重
stage_statuses.json            各阶段解析、拒绝、回退状态及关联调用编号
documents/doc_008/
  input.json                  文档名、原编号、原始句子与原文
  source.json                 规范化文本、summaries、实际源文本
  shared/baseline.json         完整E1、T1、文本B、diff及共享输入哈希
  shared/{各阶段}/call_*.json  system/user实际输入、完整HTTP回复、重试、模型名、用量
  shared/postprocess.json      第一轮去重/冲突处理/筛选前后内容
  reextract/                  重新抽取第二轮
    input.json                此路径实际辅助输入及共享基准哈希
    entity/                   第二轮实体完整请求/回复/解析审计
    relationship/             第二轮关系完整请求/回复/解析审计
    E2.json / T2.json          本路径实体与最终三元组
    postprocess.json          后处理前后内容
    changes.json              相对T1的逐字变化及索引（不等于语义改善）
    entity_changes.json       实体名逐字变化（不等于语义改善）
  incremental/                同样结构，关系stage审计含操作接受/拒绝原因
  summary.json                本篇两条路径状态、数量、文件位置
```

所有Gold只用于保存/评估，不进入模型提示词。共享基准深拷贝后才传给分支，并校验未被修改。
接口返回模型名缺失、token用量缺失记录null，不能把未返回的值认作实际值。
完整HTTP响应保存在各次attempt的response_body，内容不截取前若干字符；不保存Authorization或代理凭据。

## 后续评估

正式抽取后执行（会调用embedding API，与抽取分开）：

```powershell
python "GPT执行/反馈对比/compare_feedback.py" --evaluate-run "GPT执行/反馈对比/runs/run_实际时间戳"
```

使用本次冻结的evaluate.py规则，T1、重新抽取T2、增量抽取T2一次共用embedding缓存。
通过manifest中的**原doc_id**取Gold，doc8不会被误当成doc1。
仅在共同第一轮与两条第二轮各阶段均成功的文档上做成对主比较；剔除文档列表与原运行失败记录保留，不能隐去运行可靠性。
合法空数组仅代表成功解析，不代表原文没有事实。程序成功不代表语义正确。
完整匹配矩阵与全部达标配对存入evaluation/时间戳/，便于区分最佳配对和实际覆盖。
分数只能反映当前Gold与自动匹配规则；具体补漏、误删、情态修改仍需结合源文和实际反馈分析。
Gold带空tail或语义可疑项本实验不会自动改动。

## 对主程序的影响

新增内容集中在本目录；副本仅给EvaluatorAgent增加可选dump_dir参数，把实验中间dump导向本次实验目录。
不传该参数时保持原有路径行为。原项目`E:/huawei after/KARMA`不改动。
本地原项目代码哈希记录在original_code_hashes.json，便于复核；该机器验证记录及运行结果不上传GitHub。
