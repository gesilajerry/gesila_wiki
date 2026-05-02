# 飞书post消息格式避坑：content扁平数组 vs 嵌套数组

**背景**
飞书开放平台 post 消息类型的 content 格式极易报 230001 错误（invalid message content），这个错误在 Hermes cron 任务的多次执行中反复出现，核心原因是 content 结构理解有误。

**核心洞察**

飞书 post 消息的 content 是**扁平数组**，每行是一个 paragraph 对象：`[{tag: "text", text: "..."}]`

错误格式是把 content 嵌套成数组的数组：`[[{...}], [{...}]]`

**正确格式（Python示例）**：

```python
import json, urllib.request

# content 是扁平数组，每行一个 paragraph
content = [
    {"tag": "text", "text": "第一行内容"},
    {"tag": "text", "text": "第二行内容"},
    {"tag": "text", "text": "第三行内容"},
]

post_content = {
    "zh_cn": {
        "title": "简报标题",
        "content": content  # 直接放数组对象，不要再 json.dumps
    }
}

payload = {
    "receive_id": chat_id,
    "msg_type": "post",
    "content": json.dumps(post_content, ensure_ascii=False)
}

# 用 urllib 发送
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
```

**三个常见错误**：

1. **content 嵌套成数组的数组**：以为需要按段落嵌套，实际上飞书 post 的 content 是所有段落平铺的数组
2. **把 content 做了 json.dumps**：content 字段本身应该是对象，不是字符串；只有外层 payload.content 才需要 json.dumps
3. **用 subprocess shell 执行 curl**：容易遇到 Unicode surrogate 编码问题，推荐用 urllib.request 代替

**报错 230001 的正确排查顺序**：先确认 chat_id 和 token 是否正确（先用 text 类型消息测试）→ 再检查 content 结构是否是扁平数组 → 最后检查 JSON 是否合法

**对Jerry的意义**
Hermes 的财经新闻推送、AI热点推送、MLCC晨报等所有飞书通知功能都依赖这个格式。这个坑踩一次就会记住，但如果没有显式记录，同一坑会在不同任务中反复出现。现在这个知识已经结构化到知识库中，未来任何飞书post消息开发都可以直接引用。

**延伸思考**
飞书文档中提到的"content 是对象不是字符串"这个设计逻辑其实很清晰——外层 payload 是"消息信封"，里层 post_content.zh_cn.content 才是"消息正文"。理解了这种嵌套语义，就不会再犯格式错误。

**标签**：Hermes × 飞书API × 开发避坑 × 消息格式
