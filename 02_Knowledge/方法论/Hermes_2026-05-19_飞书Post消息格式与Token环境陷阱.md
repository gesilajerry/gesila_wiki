# 飞书Post消息格式与Token环境陷阱

**背景**
Hermes在每日向飞书推送行业简报时，遇到过两种典型失败场景：①消息发送API返回230001错误（invalid message content）；②cron沙箱环境中token不可用导致消息无法发送。这两个问题的根因截然不同，但都指向同一个结论：飞书消息发送不是"调一次HTTP POST"那么简单。

**核心洞察**

**飞书Post消息content格式（导致230001错误的根因）**

飞书post消息的content字段必须是一个"数组的数组"：
```python
# ✅ 正确格式：content 是 [[{...}], [{...}], ...]
content = [
    [{"tag": "text", "text": "第一行内容"}],
    [{"tag": "text", "text": "第二行内容"}],
    [{"tag": "text", "text": "第三行内容"}],
]

post_content = {
    "zh_cn": {
        "title": "标题",
        "content": content  # 直接放数组对象，不要再 json.dumps
    }
}

payload = {
    "receive_id": chat_id,
    "msg_type": "post",
    "content": json.dumps(post_content, ensure_ascii=False)
}
```

**常见错误**：把content写成扁平数组 `[{...}, {...}]` 而非 `[[{...}], [{...}], ...]`——错误格式直接触发230001。

**第二个陷阱：cron沙箱中的Token不可用**

在cron job的Python脚本中，如果直接调用飞书API发送消息，会遇到"Token不可用"的问题。这是因为cron环境的执行上下文与用户会话不同，没有继承已登录的飞书认证状态。

**解决方案**：不要在cron脚本中直接发飞书消息。正确做法是在cron job配置中声明 `deliver: platform:chat_id:thread_id`，由Hermes系统在job完成后自动投递到指定飞书会话。这意味着cron脚本只需要负责生成内容本身，不需要包含发送逻辑。

**对Jerry的意义**
如果cron job的飞书自动投递失败（如日志中常见的"飞书Token在此cron环境不可用"提示），需要检查两件事：①cron job配置是否正确声明了 deliver 参数；②飞书会话ID（chat_id）是否正确。当cron执行成功但飞书没收到消息时，问题通常不在内容生成端，而在投递配置端。

**延伸思考**
这一模式（生成端与投递端分离）是合理的架构设计：内容生成逻辑与分发渠道解耦，同一套内容可以同时推送到Koala博客、飞书、甚至小红书。Hermes的日报系统已经实现了这一架构——cron job生成Markdown简报，系统根据配置自动分发到多个平台。理解这一点对于设计新的自动化流水线非常重要：不要在生成脚本里硬编码发送逻辑。

**标签**：Hermes × 飞书API × 自动化运维 × 消息格式 × Cron陷阱
