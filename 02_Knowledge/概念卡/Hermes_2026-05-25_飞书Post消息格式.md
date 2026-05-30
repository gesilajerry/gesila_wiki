# 飞书 Post 消息 content 格式规范

**背景**
飞书 IM API 发送 Post 消息时，极易遭遇 230001 错误（invalid message content）。排查时容易误判为 token 问题或 JSON 字符串问题，实际根因是 content 字段的结构不符合规范。

**核心洞察**
飞书 post 消息的 content 是 `[[{...}]]` 格式（数组的数组），不是 `[{...}]`（扁平数组）。

正确结构：
```python
content = [
    [{"tag": "text", "text": "第一行内容"}],  # 每个内层数组 = 一个段落
    [{"tag": "text", "text": "第二行内容"}],
    [{"tag": "text", "text": "第三行内容"}],
]

post_content = {
    "zh_cn": {
        "title": "标题",
        "content": content  # 直接放数组对象，不要 json.dumps
    }
}

payload = {
    "receive_id": chat_id,
    "msg_type": "post",
    "content": json.dumps(post_content, ensure_ascii=False)
}
```

关键点：
- `content` 是 `[[{...}]]`（数组的数组）—— 外层数组每个元素是一个段落
- `post_content` 对象直接放进 content 字段，不做额外 json.dumps
- 最外层 `payload.content` 才需要 `json.dumps()` 转为字符串

**常见错误**
1. `content: [{...}]`（扁平数组）→ 230001
2. `content: json.dumps({...})`（字符串）→ 230001
3. 用 `urllib.request` 而非 `requests` → 部分 POST 返回 500

**对Jerry的意义**
飞书是 Hermes 与 Jerry 的核心通讯渠道，Post 消息格式错误会导致所有定时简报发送失败。掌握正确的 content 格式后，自动化发送可靠性大幅提升。

**延伸思考**
调试时先用 text 类型消息验证 chat_id 和 token 是否正确，再用 post 类型。报错 230001 时 90% 是 content 格式问题，10% 是 chat_id 错误。

**标签**：Hermes × 飞书 × API × Post消息 × 格式规范