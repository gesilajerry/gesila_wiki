# 飞书 Post 消息 content 格式规范

**背景**
飞书开放平台 IM API 的 post 消息类型是富文本消息，content 字段的格式稍有不慎就会报 230001 错误（invalid message content）。这是一个高频踩坑点，错误信息不清晰，容易被误判为 token 问题或 JSON 字符串问题。

**核心洞察**
飞书 post 消息的 content 是「数组的数组」——外层数组的每个元素是一个段落（paragraph），每个段落本身又是一个只包含一个对象的数组：`[[{tag:"text", text:"第一行"}], [{tag:"text", text:"第二行"}], ...]`。

完整嵌套结构：
```
payload = {
    "receive_id": chat_id,
    "msg_type": "post",
    "content": json.dumps({
        "zh_cn": {
            "title": "标题",
            "content": [          # ← 外层：段落数组
                [{"tag": "text", "text": "第一段内容"}],   # ← 内层：段落
                [{"tag": "text", "text": "第二段内容"}],
            ]
        }
    }, ensure_ascii=False)
}
```

三个最常见的错误：
1. 写成 `[{...}]`（扁平数组）而非 `[[{...}]]`（数组的数组）——报 230001
2. 在 content 字段上又套了一层 `json.dumps()` ——content 应该是直接的对象，不是字符串
3. 先把内层对象 `json.dumps` 再包数组——内层应该是对象引用，不是序列化后的字符串

排查顺序：先用 text 类型消息验证 token 和 chat_id 是否正确，再用 post 类型时严格按照 `[[{...}]]` 格式。

**对Jerry的意义**
这个格式错误是飞书消息类任务（如AI热点推送、财经新闻推送）最高频的失败原因。每次写飞书发送代码时，这套格式规范应当作为模板刻入肌肉记忆，避免重复调试。

**延伸思考**
飞书文档（wiki-platform-ops 文档本身）的 post 消息如果需要程序化发送，也要遵循同一套格式。不同消息类型的 content 格式差异很大：text 类型直接是字符串，post 类型是对象，file 类型是 `{"file_key": "xxx"}`，卡片消息又是另一种格式。混用格式是另一个常见踩坑点。

**标签**：Hermes × 飞书API × 踩坑总结