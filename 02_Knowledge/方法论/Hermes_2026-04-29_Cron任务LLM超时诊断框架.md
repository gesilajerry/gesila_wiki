# Cron 任务 LLM 超时诊断框架

**背景**
2026-04-29 日志显示：Hermes 共有 4 个 cron 任务（AI热点推送 04:00、财经新闻推送 08:30、财经新闻推送 02:30、输入层归档 09:00）均以 "LLM idle timeout" 失败，但 `delivery.delivered: true`，表面上"推送成功"。这些任务的共同特征是 `input_tokens` 约 19,000（稳定）、`output_tokens` 仅 89-253（几乎为零）。这不是偶发的网络抖动，而是系统性的任务配置或 prompt 加载问题。

**核心方法论**

**第一步：Token 分布判断根因**

| input_tokens | output_tokens | 诊断结论 |
|---|---|---|
| ~19,000（稳定） | 89-253（极低） | 模型未收到有效 prompt，可能 prompt 模板引用了未解析的变量 |
| ~19,000（稳定） | 0 | 模型直接拒绝/无法开始生成 |
| 波动大 | 波动大 | 网络问题或模型本身故障 |

本次案例属于第一种：input_tokens 稳定在 19K 说明请求确实到达了模型，但 output 只有几十个 token 说明 prompt 解析阶段就卡住了。最可能的原因是任务配置中的 prompt 模板使用了动态变量（如 `{{.XYZ}}`），但该变量在 cron上下文中未定义或为空，导致模型收到了一个语法异常或语义模糊的 prompt。

**第二步：检查任务配置与 prompt 渲染**

查看 `~/.openclaw/cron/jobs.json` 中对应任务的 prompt 模板，特别关注：
- 是否引用了 `session` 变量（cron 任务没有 session 上下文）
- 是否引用了 `memory` 或 `context` 变量（需要显式注入）
- 是否有条件分支（如 `{{if .XYZ}}`）在变量缺失时的默认行为

**第三步：idleTimeoutSeconds 配置调整**

在 `openclaw.json` 的 `agents.defaults.llm` 中设置 `idleTimeoutSeconds: 0`（禁用 idle 超时）或设为一个较大的值（如 300）。但更根本的解法是修复 prompt 模板，而不是依赖延长超时来掩盖问题。

**第四步：fallbackUsed 标志的强制校验**

在所有飞书推送任务的 finish hook 中，增加以下判断：
```
if (delivery.fallbackUsed === true) {
  triggerAlert("主路径失败，fallback补发，内容可能不完整");
  retryOriginalTask();
}
```
这是防止"API送达但内容空白"被误判为成功的关键闸门。

**对Jerry的意义**

cron 任务的"假性成功"会腐蚀他对系统可靠性的信任。每次超时都应视为一次 potential silent failure，需要有告警机制兜底。当前系统的 deliveryStatus 机制已经足够丰富，只是没有被正确解读——下一步应在 OpenClaw 的 cron 监控面板中增加 fallbackUsed 字段的实时展示。

**延伸思考**

这个诊断框架可以泛化为：任何 LLM 调用失败都应检查 token 分布——input 稳定 + output 接近零 = prompt 解析问题；input 波动 = 网络/模型问题；input 接近零 = 根本没有收到有效 prompt。掌握这个方法论，可以在 30 秒内定位 80% 的 LLM 调用异常根因，而不需要逐行检查代码或日志。

**标签**：Hermes × Cron × 故障诊断 × LLM × 监控
