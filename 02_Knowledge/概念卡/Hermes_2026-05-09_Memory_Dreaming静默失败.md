# Memory Dreaming 静默失败：NO_REPLY 的识别与排查

**背景**
2026-05-09归档窗口内，Memory Dreaming 任务被触发9次，全部返回 `NO_REPLY`——Cron正常运行，进程存在，但模型没有任何输出。这不是idle timeout（模型快速响应但内容为空），而是模型层面的静默失败。已持续多日，非偶发现象。

**核心洞察**

## NO_REPLY vs idle timeout：两种失败模式对比

| 特征 | NO_REPLY | idle timeout |
|------|----------|-------------|
| 模型响应速度 | 快速（秒级） | 极慢或无响应 |
| 模型输出 | 空（无任何内容） | 无或超时中断 |
| 进程状态 | 运行中 | 运行中或假死 |
| 可能根因 | prompt配置错误/模型拒绝/触发逻辑缺陷 | 资源配置不足/网络问题 |

**关键判断：** NO_REPLY 说明模型成功接收并处理了任务，但处理结果为空。这通常指向任务描述（prompt）本身的问题，而非系统性能问题。

## 排查清单

1. **检查 cron 任务描述配置**
   - 查看 `~/.hermes/cron/jobs.json` 中 Memory Dreaming 的 prompt
   - 确认 prompt 是否包含完整的系统指令和用户指令

2. **查看原始运行日志**
   ```bash
   cat ~/.hermes/cron/runs/<job_id>.jsonl
   ```
   确认模型实际输出内容（即使是空的也要看日志）

3. **手动复现**
   - 在同一时间窗口手动触发同一 prompt
   - 观察模型是否正常输出

4. **检查触发逻辑**
   - Memory Dreaming 的触发条件是什么？
   - 是否存在"触发条件满足但内容为空"的逻辑缺陷？

**对Jerry的意义**
9次连续 NO_REPLY 意味着 Memory Dreaming 功能实际上已经下线了——虽然 Cron 在跑，但没有任何记忆被记录或生成。这个问题需要专项排查，不能依赖日常归档发现。建立一个"任务有产出才算成功"的验证机制更重要。

**延伸思考**
NO_REPLY 和 idle timeout 的处理路径完全不同：NO_REPLY 需要检查 prompt 和模型逻辑，idle timeout 需要调整资源或调度。混淆两者会导致排查方向错误。建议在归档中对失败类型做自动分类，而不是全部标记为"超时"。

**标签**：Hermes × Cron运维 × 静默失败 × Memory Dreaming
