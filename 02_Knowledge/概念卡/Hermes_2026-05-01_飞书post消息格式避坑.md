# 飞书post消息格式避坑：content数组的数组

**背景**
飞书开放平台 post 消息类型的 content 格式极易报 230001 错误（invalid message content），这个错误在 Hermes cron 任务的多次执行中反复出现。2026-05-02 在发送结构层简报时，最终确认了正确的 content 格式。

**核心洞察**

飞书 post 消息的 content 格式是**数组的数组** `[[{...}]]`，每个段落是一个内层数组，外层数组包含所有段落。

**错误认知**：以为 content 是扁平数组 `[{...}]`——这是导致 230001 的根本原因。

**正确格式（Python示例）**：

```python
import requests, json

# content 是 [[{...}], [{...}], ...] 数组的数组
# 每个内层数组 = 一个段落（paragraph）
content = [
    [{"tag": "text", "text": "第一行内容"}],
    [{"tag": "text", "text": "第二行内容"}],
    [{"tag": "text", "text": "第三行内容"}],
]

post_content = {
    "zh_cn": {
        "title": "简报标题",
        "content": content
    }
}

# 外层 payload.content 才是 JSON 字符串
payload = {
    "receive_id": chat_id,
    "msg_type": "post",
    "content": json.dumps(post_content, ensure_ascii=False)
}

# 用 requests 而非 urllib
r = requests.post(
    "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    },
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    verify=False
)
```

**五个常见错误**：

1. **content 做成扁平数组**：`[{...}, {...}]` 而不是 `[[{...}], [{...}]]`——这是导致 230001 的根本原因，飞书的 content 每个段落都必须是一个内层数组
2. **把 content 做了 json.dumps**：post_content 本身是对象，不需要 json.dumps；只有外层 payload.content 才需要 json.dumps
3. **用 urllib 而非 requests**：Python 3.9 urllib 上传文件持续返回 500，改用 requests.post 的 data= 参数即可解决
4. **用 subprocess shell 执行 curl**：容易遇到 Unicode surrogate 编码问题，推荐用 requests 代替
5. **msg_type 用 "file" 发视频**：飞书视频消息必须用 `msg_type: "media"`，不能用 "file"

**报错 230001 的正确排查顺序**：先确认 chat_id 和 token 是否正确（先用 text 类型消息测试）→ 再检查 content 结构是否是 `[[{...}]]` 而不是 `[{...}]` → 最后检查 JSON 是否合法

**对Jerry的意义**
Hermes 的财经新闻推送、AI热点推送、MLCC晨报、小红书执行报告等所有飞书通知功能都依赖这个格式。错误格式在测试时就会返回 230001，不会静默失败——但如果不知道正确格式，调试方向会完全错误。

**延伸思考**
飞书文档中 content 格式的描述比较隐晦。关键理解：post 消息的 content 本身是一个「段落的数组」，每个段落可以包含多个 inline 对象（text、a、img 等），所以段落本身也是数组。外层 content 数组把所有段落汇成一个完整的消息正文。

**标签**：Hermes × 飞书API × 开发避坑 × 消息格式 × requests
