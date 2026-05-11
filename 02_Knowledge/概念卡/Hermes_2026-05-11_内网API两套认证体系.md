# 内网 API 认证体系：Bearer Token vs Tenant Access Token

**背景**
Jerry 的工作环境中同时存在两套独立的消息/内容发布系统：飞书开放平台（IM 消息发送）和内网 Koala 博客系统。两套系统都使用 Bearer Token 认证，但它们是完全独立的认证体系，不能混用或共用。错误地让博客 Bearer Token 去调飞书 API，会得到 99991668 错误。

**核心洞察**
这两套认证体系的关系如下：

| 系统 | 认证方式 | 获取途径 |
|------|---------|---------|
| 飞书 IM 消息 | tenant_access_token | POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal，使用 APP_ID + APP_SECRET 换取，有时效 |
| Koala 博客 | Bearer Token | 长期有效，存在 `~/.netrc` 或直接存储，每次请求带在 Authorization Header |

关键原则：
- 飞书 IM API **只认** tenant_access_token，用博客的 Bearer Token 会报 99991668
- 博客 API **只认** Bearer Token，用飞书的 tenant_access_token 会报 401
- 两套系统需要分别管理各自的 token，不能相互替代

实践中，如果遇到「token 看起来有效但 API 返回权限错误」，首先确认用的是哪套系统的 token。

**对Jerry的意义**
在 cron 任务同时涉及飞书发消息和博客发文章时（如AI热点推送任务），需要分别管理两套 token。blog-publisher 技能里存的是博客 Bearer Token，feishu-text-message 技能里存的是飞书 APP_ID + APP_SECRET（用于动态换取 tenant_access_token）。两者不能合并。

**延伸思考**
这种「同名不同质」的认证体系设计在企业内部很常见。建议在笔记系统里明确标注每个系统的认证方式，而不只是记「有个 token」。更重要的是：当一个 token 工作而另一个不工作时，问题几乎一定是混用了认证体系，而不是 token 本身过期或失效。

**标签**：Hermes × 飞书API × 内网系统 × 认证机制