# 原始素材：22岁破解Claude Mythos架构并开源（已核实）

## 来源
36氪/新智元 + Hermes调查补充（2026-04-22核实）

## 核心事件
22岁Kye Gomez（Swarms创始人，前Agora Labs负责人）以第一性原理从公开论文和研究成果"逆推"出Claude Mythos核心架构，全量开源为OpenMytho项目（GitHub 4.8k Stars，MIT协议）。

## 关键人物
- 姓名：Kye Gomez，22岁，Swarms创始人
- 履历：2021-2024年同时担任三家公司联创/CEO，建立"APAC"生态体系
- 研究方向：大规模多智能体系统、替代模型架构、多模态模型

## 核心技术
循环深度Transformer（RDT）：
- 同一套权重，一次前向传播中循环跑16次
- 每次循环隐藏状态更新一次
- 架构三段式：Prelude→Recurrent Block→Coda
- 770M参数循环模型≈1.3B参数标准Transformer

## 重要声明
- GitHub明确免责声明：非Anthropic官方，与Claude闭源系统无任何关联
- 这是基于公开研究资料的第一性原理社区重建，非内部泄露

## 参考链接
- GitHub: https://github.com/kyegomez/OpenMythos
- Kye Gomez Twitter: https://x.com/KyeGomezB/status/2045659150340723107