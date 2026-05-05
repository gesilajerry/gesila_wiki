# 飞书 Post 消息 content 格式的 `[[{...}]]` 嵌套结构

**背景**

飞书开放平台发送 post 类型消息时，content 字段的格式极易报错 230001（invalid message content），导致大量调试时间浪费在此坑上。这个问题在 mmx search、blog publisher、财经简报等所有飞书推送任务中反复出现。

**核心洞察**

飞书 post 消息的 content 结构是**数组的数组**，即 `[[{...}], [{...}], ...]`，而非扁平的 `[{...}]`。每一层嵌套数组代表一个段落（paragraph）。

正确格式如下：

```python
import requests, json

# content 是 [[{...}]] —— 数组的数组，每个内层数组 = 一个段落
content = [
    [{"tag": "text", "text": "第一行内容"}],
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

**三个关键点：**

1. **content 是 `[[{...}]]`（数组的数组）**：外层数组包含所有段落，内层每个数组是单个段落。扁平数组 `[{...}]` 会报 230001。

2. **content 字段本身是对象**：直接放数组引用，不是 json.dumps 后的字符串。外层 payload.content 才是 json.dumps 序列化的字符串。

3. **用 `requests` 而非 `urllib.request`**：Python 3.9 的 urllib 对飞书文件上传和部分 POST 会持续返回 500，改用 requests 解决。

**排查流程：** 报错 230001 → 先用 text 类型消息测试 chat_id 和 token 是否正确 → 确认无误后检查 content 格式是否为 `[[{...}]]`。

**对Jerry的意义**

Jerry 的所有 cron 简报任务（财经、AI、MLCC、半导体）都依赖飞书推送。每次格式错误都导致任务"成功执行"但飞书发送失败，表面上看不出问题。掌握这个格式后，所有推送任务的稳定性都有保障。

**延伸思考**

飞书 post 消息还支持富文本标签（bold、link、image 等），但核心还是嵌套数组结构。可以用 `requests` 替代 `urllib.request` 的经验也可以迁移到其他 HTTP POST 场景。

**标签**：飞书 × API × 踩坑 × 自动化推送
