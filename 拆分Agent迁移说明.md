# 拆分 Agent 与常规反馈

## 运行流程

```bash
bash run_revision.sh
```

第二部分固定执行：固定 R1 → 拆分 Agent → 文本重建 → 文本比较 → 实体修订
→ 常规关系反馈 → 原有冲突处理 → 原有评分过滤 → 最终 R2。

不设置两种修订模式。脚本继续使用 BASELINE_FILES 或 outputs/current_baselines.txt；
运行前确认指向固定 run1，不需要重跑 baseline。基线保持不变，输出另存到新目录。
原先被跳过的 Agent 不启用。baseline 阶段不执行拆分；full 阶段在第一轮后执行上述流程。

## 输入输出

拆分 Agent 输入源文本和第一轮最终三元组；发送给 LLM 的三元组字段为
index、head、relation、tail，不包含候选实体、文本差异或 Gold。
每篇正常调用一次 LLM，沿用原模型、API 模式和 temperature=0.0，网络重试策略不变。
LLM 返回 add/remove/replace 操作，程序校验、应用并去重后返回完整集合。
拆分失败时保留输入集合，继续常规反馈。

文本重建接收拆分后集合；文本比较对照源文本与新的重建文本。
实体修订输入源文本、原候选实体、拆分后集合和新差异。
关系反馈输入源文本、重新编号的拆分后集合、修订后的候选实体和新差异。
反馈操作的 index 指向拆分后集合，不指向原始 R1。

## Prompt 与对照范围

拆分 Prompt 原样迁入 karma/agents/triple_splitting/agent.py，包括并列和
长短语/从句检查。关系反馈的用户和系统 Prompt 恢复为 Git 9850fd0 的常规版本，
保留 FACT_RULES、SCORE_RULES、操作定义和输出格式。第一轮抽取不变。

固定响应测试验证拆分 Agent 本身与迁移前的 Prompt、操作处理和输出一致。
为兼容历史结果，拆分新增三元组的 source 标签仍为 relationship_revision，
实际执行 Agent 在独立审计中注明。
后续常规反馈可能继续新增、删除或替换事实，因此最终 R2 不保证与此前仅拆分时一致。
当前拆分 Prompt 含后来增加的长短语检查，也不能保证复现更早 v5.1 的分数。

## 输出与评估

- details/_dump_docN_splitting.json：拆分输入、操作审计和输出。
- details/_dump_docN_revision_result.json：原始基线、拆分结果、常规反馈输入、
  反馈审计、冲突处理和最终结果。
- details/_run_manifest.json：R1/R2 保留原定义；stages.after_split 保存拆分检查点。

```bash
python evaluate_lenient.py <结果目录> data/DocIOE/transport --compare-strict
python evaluate_lenient.py <结果目录> data/DocIOE/transport --compare-strict --comparison baseline-split
python evaluate_lenient.py <结果目录> data/DocIOE/transport --compare-strict --comparison split-final
```

分别比较基线与最终结果、基线与拆分结果、拆分结果与最终结果；匹配计分规则不变。
后两种比较默认保存到 lexical_evaluation/<比较名称>/。
CSV 为兼容格式保留 R1/R2 列标签，JSON 的 input.round_stages 和终端输出标注真实阶段。

## 离线验证

```bash
python -m unittest discover -s tests -q
```

覆盖拆分迁移等价性、完整反馈衔接、基线不变、反馈索引、失败回退、
检查点保存和评估兼容性。测试使用模拟响应，不调用真实模型。
