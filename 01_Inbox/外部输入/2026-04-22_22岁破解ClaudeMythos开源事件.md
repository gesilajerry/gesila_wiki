# 原始素材：22岁创业者破解Claude Mythos架构并开源

## 来源
36氪/新智元（2026-04-22）

## 核心事件
22岁创业者Kye Gomez（Swarms创始人，前Agora Labs负责人）仅用公开论文和第一性原理，成功逆向工程Anthropic闭源模型Claude Mythos的核心架构，以"OpenMythos"为名在GitHub上全开源，代码仅需几行即可运行。

## 关键人物
- 姓名：Kye Gomez
- 年龄：22岁
- 身份：Swarms创始人，前Agora Labs负责人
- 学历：高中毕业后即创业，未接受过正规大学教育
- 经历：2021-2024年同时担任三家公司联创/CEO，覆盖AI深科技、媒体、食品科技等领域

## 核心技术发现（OpenMythos）
- GitHub: github.com/kyegomez/OpenMythos
- 假设：Claude Mythos采用"循环深度Transformer"（Recurrent Deep Transformers）架构
- 核心逻辑：同一套权重一次前向传播循环跑16次（Same weights, one forward pass, looped 16 times）
- Scaling新法则：未来最强模型不是参数最多，而是"想得最多次"（Thinking Tokens）

## Dario Amodei回应
- 中国将在12个月内完全复刻出具备Claude Mythos级别能力的大模型
- "彩虹没有尽头，只有彩虹本身"——目前完全看不到技术放缓的迹象

## 行业意义
- 闭源实验室的架构优势正在以肉眼可见的速度消失
- 护城河不再是架构，而是数据和生态