# 飞书Post消息格式陷阱与正确格式

**背景**
在 Hermes cron 任务中，通过飞书 IM API 发送富文本消息（post 类型）是核心交付方式。在多次调试中，230001 错误（invalid message content）是最频繁的报错，根源在于对飞书 post 消息 content 字段结构的误解。

**核心洞察**

飞书 post 消息的 content 字段格式要求极为特殊，是**数组的数组**结构 `[[{...}], [{...}], ...]`，而非扁平数组 `[{...}]`。每个内层数组代表一个段落（paragraph），外层数组包含所有段落。

**错误格式（导致230001）：**
```python
# 错误1：扁平数组
content = [{"tag": "text", "text": "第一行"}, {"tag": "text", "text": "第二行"}]

# 错误2：content 直接放 JSON 字符串
payload = {
    "content": json.dumps({"zh_cn": {"content": [[...]]}})  # 双重序列化
}
```

**正确格式：**
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

**230001 错误排查顺序：**
1. 确认 content 是 `[[{...}]]` 结构而非 `[{...}]`
2. 确认 content 字段本身是对象（直接放数组），外层 payload.content 才是 json.dumps 后的字符串
3. 先用 text 类型消息测试 chat_id 和 token 是否正确（排除认证问题）
4. 检查 Content-Type 是否为 `application/json; charset=utf-8`

**对Jerry的意义**
飞书是 Hermes 日报的核心推送渠道。掌握正确的 post 消息格式，可以避免每次调试浪费10-30分钟。牢记 `[[{...}]]` 这个结构，即使用对了。

**延伸思考**
如果需要发送带链接的文本，可以使用 `at` 标签 mention 某人，或 `a` 标签添加超链接。表格在飞书 post 中不支持，需转换为文本或使用消息卡片（card）类型。

**标签**：Hermes × 飞书API × 230001错误 × 消息格式
