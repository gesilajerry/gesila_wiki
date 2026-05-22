# 飞书 post 消息格式陷阱与正确写法

**背景**
在使用飞书开放平台 IM API 发送富文本消息（post 消息）时，内容格式极其容易报 230001 错误（invalid message content），导致发送失败。根本原因是对飞书 post 消息 content 嵌套层级理解错误。

**核心洞察**

飞书 post 消息的 content 字段必须是一个**数组的数组**，即 `[[{...}], [{...}], ...]`，而不是扁平的 `[{...}]`。

外层数组的每个元素是一个段落（paragraph），每个段落本身也是一个数组（包含一个或多个 tag 对象）。正确的结构如下：

```python
content = [
    [{"tag": "text", "text": "第一行内容"}],      # 段落1
    [{"tag": "text", "text": "第二行内容"}],      # 段落2
    [{"tag": "text", "text": "第三行内容"}],      # 段落3
]
```

然后在构造 payload 时，直接把这个 Python 数组对象放进 `post_content["zh_cn"]["content"]`，**不要再 json.dumps**。外层 payload.content 才需要 json.dumps：

```python
post_content = {
    "zh_cn": {
        "title": "标题",
        "content": content  # 直接放数组对象，不是字符串
    }
}

payload = {
    "receive_id": chat_id,
    "msg_type": "post",
    "content": json.dumps(post_content, ensure_ascii=False)  # 这里才 dumps
}
```

**对Jerry的意义**
在所有 Hermes cron 任务中，只要涉及飞书 post 消息发送（AI简报、财经简报、半导体简报等），都必须遵循这个格式。一旦格式错误，任务看似执行但飞书用户实际收不到消息，会导致信息链路中断。养成习惯：飞书 post = `[[{...}]]` 结构。

**延伸思考**
- 报错 230001 通常是 content 格式不对，不是 JSON 字符串或 token 问题。优先检查嵌套层级。
- 扁平的 `[{...}]` 结构不会报错，但飞书会拒绝渲染，直接报 230001。
- Python 的 `requests` 库比 `urllib.request` 更可靠——Python 3.9 urllib 对飞书文件上传和部分 POST 会持续返回 500，改用 requests 解决。
- 另外注意 Koala 博客发布也有坑：标题含 `$`、`×` 等字符会导致 JSON 解析失败，需要提前替换。

**标签**：Hermes × 飞书API × 踩坑 × 230001错误
