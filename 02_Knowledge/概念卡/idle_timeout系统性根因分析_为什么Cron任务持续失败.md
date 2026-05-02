# 概念卡：idle timeout系统性根因——为什么Cron任务持续失败

> 归档时间：2026-05-02 | 分类：系统可靠性 × DevOps | 来源：会话复盘总结（05-02）

---

## 背景

2026年5月1-2日的Cron任务执行中，**6次失败中有5次为 model idle timeout**（LLM响应超时被强制中断）。涉及任务包括：
- AI热点推送 04:00/10:00/16:00（3次）
- 半导体热点晚报 23:00（5/1）
- 结构层提炼 20:45（5/1）
- 输入层归档 09:00（5/2）

这是一个系统性问题，而非偶发故障。idle timeout 意味着模型在生成响应过程中被强制中断，说明**任务耗时超过了 LLM provider 的基础超时配置**。

---

## 核心洞察

### idle timeout 的技术本质

**idle timeout 的触发链条：**
```
Cron任务触发
    ↓
Agent接收任务，开始LLM推理
    ↓
LLM推理耗时 > provider配置的 timeoutSeconds
    ↓
Provider强制断开连接
    ↓
模型返回不完整响应（无尾部内容）
    ↓
Agent工具调用失败或内容丢失
```

**本次问题的特殊性：** 上次归档报告（5月1日）称已修复 `idleTimeoutSeconds=0`（禁用idle超时），但5月2日仍然出现6次timeout，说明：
1. `idleTimeoutSeconds=0` 禁用的是 OpenClaw agent 的idle超时，但**provider级别的硬性timeout仍在**
2. 任务耗时本身已超过 provider 配置（如 minimax 的 `timeoutSeconds`）

### 两层超时机制的区别

| 层级 | 配置项 | 作用 | 本次问题 |
|------|--------|------|---------|
| OpenClaw Agent层 | `idleTimeoutSeconds` | 无活动多久后中断推理 | ✅ 上次已禁用 |
| LLM Provider层 | `timeoutSeconds` | 单次API调用的最大等待时间 | ❌ 仍可能是瓶颈 |

### 典型超时场景反推

从失败任务类型分析，**最容易超时的任务特征**：

1. **内容采集型**（AI热点/财经新闻推送）：搜索 → 整理 → 推送，链条长
2. **多工具调用型**：需要调用 Tavily、exec、message 等多个工具，调用次数越多，总耗时越长
3. **结构化输出型**：长文本（>2000字）的生成更容易在中途超时

---

## 对Jerry的意义

1. **系统可靠性**：idle timeout 问题不解决，Cron任务成功率将维持在60-70%，严重影响信息推送的稳定性
2. **排查优先级**：先检查 `models.providers.minimax.timeoutSeconds` 配置（建议≥600秒）
3. **任务设计优化**：对于长链条任务（内容采集+推送），考虑拆分为"采集任务"和"推送任务"两个独立Cron，降低单次任务耗时
4. **监控指标**：将"连续idle timeout次数"纳入Cron任务健康度监控（连续2次timeout应触发告警）

---

## 延伸思考

**根本性解决方案（技术债务）：**
1. **短期（1-2天）**：将 `models.providers.minimax.timeoutSeconds` 设置为 600-900秒
2. **中期（1周）**：为每个Cron任务设计合理的 token 预算（短推送 ≤2000 tokens，长分析 ≤4000 tokens），超出预算时分段处理
3. **长期（1个月）**：引入任务队列机制（采集 → 入库 → 推送解耦），采集任务失败不影响推送任务执行

**当前 workaround：** 对于必须当日完成的结构层提炼，可考虑使用更短 token 预算的 prompt（如"提炼3个核心洞察"而非"提炼5-8个"），降低超时风险。
