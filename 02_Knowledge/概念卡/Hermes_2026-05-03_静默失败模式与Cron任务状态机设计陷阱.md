# Cron任务静默失败模式与状态机设计陷阱

**背景**
Memory Dreaming Promotion任务连续3次执行返回`status: ok` + `summary: "NO_REPLY"` + `delivered: false`，没有任何有效输出，但状态显示"成功"。这与idle timeout（有明确错误信息+自动重试）形成鲜明对比——静默失败比显式失败危险得多。

**核心洞察**

Cron任务有四种状态组合，代表不同的危险等级：

| 状态组合 | 含义 | 危险等级 |
|---------|------|---------|
| status:error + delivered:true | 显式失败，已通知 | ⚠️ 低（可见） |
| status:ok + summary:"NO_REPLY" + delivered:false | 静默失败，未通知 | 🔴 高（隐藏） |
| status:ok + summary:有效内容 + delivered:true | 完全成功 | ✅ 安全 |
| status:error + delivered:false | 显式失败，未通知 | 🔴 高（但罕见） |

NO_REPLY模式最危险：状态机认为"任务执行成功（ok）"，但实际没有任何业务产出，且不会触发任何告警。如果cron任务没有额外的业务结果校验（如推送数量>0），这种失败会永久潜伏。

**根因分析**
NO_REPLY可能的三种成因：
1. Prompt为空或极短，模型直接返回空响应
2. 任务逻辑触发模型直接结束对话（无tool call，无输出）
3. 输入token极少时模型跳过推理直接返回空

第二种最为典型——当任务设计假设模型会调用工具，但模型认为无需调用时，就会直接返回空。

**幂等性设计原则**
 Cron任务的"静默失败"陷阱揭示了一个设计原则：业务结果的幂等性校验比任务状态的幂等性更重要。

错误设计：依赖`status:ok`判断成功
正确设计：同时检查`status:ok` + `delivered:true` + `summary长度>N`

**对Jerry的意义**
当前Cron任务配置中，Memory Dreaming Promotion是唯一持续NO_REPLY的任务，说明任务prompt设计有问题而非系统问题。这个任务已经连续3次静默失败，如果不做修复，会永久消耗cron调度资源却零产出。建议立即检查该任务的prompt设计或暂停调度。

**延伸思考**
所有Cron任务的业务结果监控应该加入"最低有效输出"校验：
- 财经/AI推送：条数≥5
- 结构层提炼：卡片数≥1
- 归档任务：文件行数>100

这比单纯依赖任务状态更可靠。

**标签**：Hermes × Cron运维 × 静默失败 × 状态机设计
