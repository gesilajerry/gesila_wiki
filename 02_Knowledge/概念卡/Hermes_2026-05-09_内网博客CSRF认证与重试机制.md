# 内网博客发布：CSRF认证与重试机制

**背景**
Hermes 将每日AI热点简报自动发布到内网博客（192.168.30.198:8443）。在实测中，500错误是最主要的失败原因，涉及CSRF Token复用、标题特殊字符、服务端限速等多个独立因素，需要系统性应对。

**核心洞察**

**CSRF Token 必须每次单独获取，不能跨请求复用。** Bearer Token 有时效（数小时），但 CSRF Token 是一次性的，每次 POST 请求前必须重新从 `/api/csrf` 获取。

```python
def publish_one(title, content_html, group_ids, attempt=1):
    try:
        # 每次单独获取 CSRF
        csrf_req = urllib.request.Request(
            'https://192.168.30.198:8443/api/csrf',
            headers={'Authorization': f'Bearer {TOKEN}'})
        csrf = json.loads(
            urllib.request.urlopen(csrf_req, context=ctx, timeout=10).read()
        )['data']

        payload = json.dumps({
            "forum_id": FORUM_ID,
            "title": title,
            "content": content_html,
            "group_ids": group_ids,
            "type": "blog"
        }, ensure_ascii=False).encode('utf-8')

        req = urllib.request.Request(
            'https://192.168.30.198:8443/api/discussion',
            data=payload,
            headers={
                'Authorization': f'Bearer {TOKEN}',
                'X-CSRF-Token': csrf,
                'Content-Type': 'application/json; charset=utf-8',
            },
            method='POST')
        return json.loads(urllib.request.urlopen(req, context=ctx, timeout=15).read())

    except urllib.error.HTTPError as e:
        if e.code == 500 and attempt < 3:
            time.sleep(3)
            return publish_one(title, content_html, group_ids, attempt + 1)
        return {'success': False, 'error': f'HTTP {e.code}'}
```

**500错误的多种根因：**
1. **CSRF Token 复用** — 同一 token 发两次请求，第二次必500
2. **标题含特殊字符** — `×`(U+00D7) 和 `$` 会导致 JSON 解析失败，需替换为 `x` 和 `美元`
3. **服务端限速** — 请求过于频繁触发 ratelimit，批量发布间隔需≥10秒
4. **随机波动** — 加3次重试（间隔3秒）可解决大部分随机500

**Python 3.14 emoji正则bug：** 禁止用 emoji 过滤函数，Python 3.14 的 `\\U00002600-\\U000026FF` 范围会误删 CJK 中文字符，导致 HTML 乱码。中文内容原样传即可。

**对Jerry的意义**
每日AI简报自动发布到内网博客是 Hermes 的核心输出之一。掌握这套发布函数后，可以在 wiki 中直接调用，不再每次手动发布。CSRF 单独获取 + 3次重试 + 特殊字符替换是三个缺一不可的保险。

**延伸思考**
如果发布成功但列表查不到，可能是 group_ids 权限问题——确认账号有该分类权限。Bearer Token 过期时，`GET /api/user` 会返回 401，此时重新获取 token 即可。注册状态显示"等待管理员审批"不代表账号不可用，只要 token 有效就能正常发布。

**标签**：Hermes × 内网博客 × CSRF × 重试机制 × 500错误
