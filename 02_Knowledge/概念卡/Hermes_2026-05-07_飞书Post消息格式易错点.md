# 飞书Post消息格式易错点

**背景**
飞书开放平台IM API的post消息类型，content字段格式极易配置错误，导致230001 invalid message content报错，新手容易在此卡住数小时。

**核心洞察**
飞书post消息的content是**数组的数组** `[[{...}], [{...}], ...]`，不是扁平数组 `[{...}]`——这是最常见的错误。

正确格式示例：
```python
import requests, json

content = [
    [{"tag": "text", "text": "第一行内容"}],
    [{"tag": "text", "text": "第二行内容"}],
]

post_content = {
    "zh_cn": {
        "title": "标题",
        "content": content  # 直接放数组对象，不要再json.dumps
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

**对Jerry的意义**
- 调试飞书消息时，230001错误首先检查content格式
- 先用text类型消息验证chat_id和token是否正确，再用post类型
- Python 3.9的urllib对飞书部分POST会返回500，统一用requests

**延伸思考**
- 飞书post的content结构：外层数组=多个段落，每个内层数组=一个段落的行
- `verify=False` 在测试环境使用，生产环境建议配置证书
- title和content都是zh_cn下的字段，不支持其他语言时仍需保留该结构

**标签**：飞书API × 消息格式 × 踩坑记录