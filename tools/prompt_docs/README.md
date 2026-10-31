# Agent Prompt 文档维护

在仓库根目录执行：

```powershell
python tools/prompt_docs/export_agent_prompts.py
node tools/prompt_docs/render_agent_docs.mjs
```

导出器在模型调用边界使用模拟返回值捕获当前源码拼接出的提示，不调用网络或真实模型。固定规则、评分、格式和示例完整展开；源文本、三元组等动态输入保留源码表达式。文档写入对应 Agent 目录，另生成总览和角色模板 JSON。

HTML 渲染器需要 `marked`。优先使用 Node 可找到的安装；否则尝试用户目录下的 Codex 内置依赖。没有该依赖时可先安装 `marked`，或按现有 HTML 结构手动同步。

修改 Prompt 后必须核对 Markdown 中实际调用分支、源码行号、变量位置与固定文本。新增 Agent、调用入口、输入标签或条件分支时，应同时扩展导出器；不能认为旧脚本能自动识别所有新结构。`全Agent导出与行号核验.json` 记录导出的源码哈希和来源位置，用于复核。

完整同步要求见仓库根目录的 `AGENTS.md`。
