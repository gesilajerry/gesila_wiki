# API 安全设计：CSRF Token 一次性使用原则

**背景**
在内网 Koala 博客系统的 API 发布流程中，CSRF Token 必须每次请求单独获取，不能跨请求复用。这是一个设计反直觉的地方——通常我们会认为获取一次 token 应该可以复用一段时间，但实际上这个系统的 CSRF token 是「一次一用」的。

**核心洞察**
博客发布的完整认证流程：
1. 从 `GET /api/csrf` 获取 CSRF token（每次都要单独请求）
2. 在 POST `/api/discussion` 的 Header 中带上这个 CSRF：`X-CSRF-Token: <token>`
3. 同时带上 Bearer Token：`Authorization: Bearer <token>`

错误做法：
- 获取一次 CSRF 后在多个请求中复用 → 第二次请求起全部 500 错误
- Bearer Token 有效但 CSRF 过期时，API 返回 401，此时不是 Bearer Token 的问题，是 CSRF 的问题
- 在 CSRF 过期后试图通过重新获取 Bearer Token 来解决 → 方向错误

正确做法：
```python
def publish_one(title, html, group_ids):
    csrf = get_csrf()           # 每次单独获取
    # ... 发送请求 ...
    
# 批量发布时每篇之间都要重新获取 CSRF
for fp in files:
    md = Path(fp).read_text()
    r = publish_one(title, html, [CATEGORY])  # 内部会获取新 CSRF
    time.sleep(10)              # 间隔≥10秒防限速
```

相关踩坑：Bearer Token 有时效（几个小时），失效后需要重新登录获取。但 Bearer Token 失效时 CSRF 也会随之失效，所以要先验证 Bearer Token 有效性，再重新获取 CSRF。

**对Jerry的意义**
这个原则在批量发布时尤其容易出错——当第一篇成功但第二篇开始500时，开发者容易怀疑是请求内容问题或限速问题，而意识不到是 CSRF 复用的根因。按照「每次单独获取」实现，可以避免绝大多数 500 错误。

**延伸思考**
CSRF token 一次性使用通常是服务端为了防止 CSRF 攻击而设计的安全机制。每次表单提交都必须从服务端获取一个新 token，这本身是合理的安全实践。理解了这个设计意图，就不会试图去「优化」成复用 token 了。

**标签**：Hermes × 内网系统 × API设计 × 安全机制