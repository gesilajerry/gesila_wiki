# 飞书Post消息content格式陷阱

**背景**
飞书开放平台发送 Post 富文本消息时，content 字段格式错误是报 230001（invalid message content）的最常见原因。出错时开发者容易怀疑 token 或 chat_id，实际问题往往在 content 结构本身。

**核心洞察**
飞书 Post 消息的 content 必须是**数组的数组**格式：`[[{paragraph}], [{paragraph}], ...]`
- 外层数组 = 所有段落的容器
- 每个内层数组 = 一个段落（paragraph）
- 错误做法：扁平数组 `[{...}, {...}]`（直接报 230001）

正确结构示例：
```python
content = [
    [{"tag": "text", "text": "第一行内容"}],
    [{"tag": "text", "text": "第二行内容"}],
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

**对Jerry的意义**
- 排查 230001 错误时，优先检查 content 是否为 `[[{...}]]`，而不是先查 token
- 用 text 类型消息测试 chat_id 和 token，再用 post 类型测试 content 格式
- Python `requests` 库比 `urllib.request` 更稳定（Python 3.9 urllib 对部分飞书 POST 返回 500）

**延伸思考**
飞书文档强调"数组的数组"，但开发者文档示例不清晰，容易误导。230001 还有一种情况是 `content` 字段本身被 `json.dumps` 了两遍（先 dump post_content，再 dump payload 时又把 content 字符串 dump 了一次）。

**标签**：Hermes × 飞书API × 230001错误 × Post消息
