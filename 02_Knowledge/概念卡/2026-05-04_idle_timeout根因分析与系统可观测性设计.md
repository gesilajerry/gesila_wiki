# 概念卡 | idle timeout 根因分析与系统可观测性设计

## 背景

2026年5月3日窗口的Cron执行出现了9次最终失败，其中5次为idle timeout（模型输出被截断）。问题集中在结构层提炼、MLCC产业链晨报、AI热点推送等长时任务上。这不是偶发故障，而是系统性配置失配的显性表现。

## 核心洞察

**根因：timeoutSeconds配置与任务实际执行时长不匹配。**

当前 minimax provider 的 `timeoutSeconds` 设置无法覆盖长时任务的完整执行路径。以结构层提炼为例：读取多个日志文件→分析内容→提炼概念→撰写5-8张300-800字卡片→Git操作→飞书推送，全流程Token输出量巨大，300s的timeout会在输出中途强制截断，导致任务状态变为error但实际已在后台部分完成。

**idle timeout的特殊性：** 不是模型本身问题（模型正常输出），而是输出管道在规定时间内无法完成传输。这是流式输出的固有问题——模型生成快，但Token经网络传回被idle计时器截断。

**系统性影响评估：**
- 5次idle timeout → 3次成功重试 → 净损失2次完整执行
- 结构层提炼任务被idle timeout打断 → 卡片文件可能已写入但Git未push → 数据一致性问题
- 长期影响：cron调度器对"失败"任务的重复触发消耗额外算力

## 对Jerry的意义

**直接可用：** 立即将 `models.providers.minimax.timeoutSeconds` 调高至900s，并为长时cron任务配置 `idleTimeoutSeconds=0`。这是成本最低、效果最快的SRE行动。

**架构层面：** idle timeout本质上是"可观测性不足"——任务执行了但无法被准确监控。长期而言需要为cron任务引入执行状态持久层（将session status写入文件而非依赖summary字段），解决"NO_REPLY静默失败"问题。

## 延伸思考

Memory Dreaming Promotion连续4次NO_REPLY与idle timeout是同类问题——任务正常执行但输出未被正确捕获。区别在于：idle timeout是配置问题（可修复），NO_REPLY可能是任务设计问题（输出`delivery: not-requested`但summary字段为空）。建议专项排查Memory Dreaming的任务模板，确认是设计静默还是异常遗漏。

> 标签：#系统健康 #SRE #Cron调度 #可观测性
> 来源：2026-05-03会话复盘总结
> 归档时间：2026-05-04 09:30