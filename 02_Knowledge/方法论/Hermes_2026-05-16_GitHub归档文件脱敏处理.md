# GitHub 归档文件脱敏处理

**背景**
Hermes cron 任务将所有执行记录归档到 `Hermes_YYYY-MM-DD_推送日报.md`，文件中包含完整的 Prompt 内容（包含调用的 SKILL.md 全文）。如果 SKILL.md 中含有 GitHub Token 说明文本，GitHub 的 secret scanning 会自动检测并拦截 push。

**核心洞察**

GitHub secret scanning 能够检测归档文件中嵌入的 token 字符串并自动拦截 push，导致 `git push` 失败。解决方法是将 token 全文替换为 `[GITHUB_TOKEN_REDACTED]` 或其他占位符。

需要脱敏的内容不仅包括实际的 token 值（如 `ghp_xxx`），也包括技能文档中对 token 的说明文本——因为说明文本中通常会包含 token 格式的描述，可能触发正则匹配。

具体操作：在归档文件写入前或写入后，将所有出现 token 的地方统一替换为 `[GITHUB_TOKEN_REDACTED]`。

**对Jerry的意义**
在所有包含敏感凭证的技能文档被加载到 cron 任务 Prompt 中的场景下，归档操作必须先完成脱敏检查。建议在归档脚本中加入自动脱敏步骤：在写入 `Hermes_YYYY-MM-DD_推送日报.md` 之前，用 Python 将所有 skill 内容中可能包含的 token 字符串替换为占位符，再写入归档文件。

这解决了两个问题：(1) 防止 push 被拦截；(2) 防止归档文件中残留敏感信息。

**延伸思考**
这个问题暴露了 Hermes cron 任务设计的一个结构性矛盾：Skill 文档需要包含凭证信息才能指导执行，但 Skill 内容会完整嵌入 Prompt，而 Prompt 又会完整归档留存。

更好的做法是：凭证信息通过环境变量传递（Skill 文档中只引用变量名），而非明文写入 Skill 内容。或者，在归档前增加一个脱敏步骤，从归档文件中扫描并替换常见的敏感模式（如 `ghp_`、`ghs_`、GitHub token 格式等）。

**标签**：Hermes × GitHub × 安全 × 凭证管理 × 归档
