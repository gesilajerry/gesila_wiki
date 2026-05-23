# 飞书Post消息content格式的致命陷阱：数组的数组

**背景**
在本次归档的多个飞书消息发送任务中，skill文档反复嵌入同一个飞书Post消息格式踩坑记录。这一格式错误（230001 invalid message content）频繁出现在所有简报任务的prompt里，说明它是一个反复绊倒工作流的经典错误。

**核心洞察**

飞书Post消息的content格式，99%的人第一次写都会踩坑。错误根源是对"数组的数组"这个结构的误解。

**错误写法（扁平数组）**：
```python
# ❌ 错误：扁平数组
content = [
    {"tag": "text", "text": "第一行内容"},
    {"tag": "text", "text": "第二行内容"},
]
```
报错：230001 invalid message content

**正确写法（数组的数组）**：
```python
# ✅ 正确：数组的数组，每个内层数组 = 一个段落
content = [
    [{"tag": "text", "text": "第一行内容"}],
    [{"tag": "text", "text": "第二行内容"}],
]
```

每个段落是独立的内层数组，外层数组包含所有段落。payload结构如下：
```python
post_content = {
    "zh_cn": {
        "title": "标题",
        "content": content  # 直接放数组对象，不要json.dumps
    }
}

payload = {
    "receive_id": chat_id,
    "msg_type": "post",
    "content": json.dumps(post_content, ensure_ascii=False)
}
```

**三个必须记住的关键点**：
1. content字段本身是对象（直接放数组），不是字符串；外层payload.content才是json.dumps后的字符串
2. 报错230001通常是content格式不对，不是token问题——不要先去查token
3. 用`requests`而非`urllib.request`——Python 3.9 urllib对飞书部分POST持续返回500，改用requests解决

**对Jerry的意义**

这一格式错误会导致所有飞书消息发送任务（AI简报、半导体晚报、财经新闻、MLCC日报等）全部失败。由于所有简报任务都依赖飞书发送推送，一旦这个格式出错，全天的行业简报都无法送达。这是一个高风险的单点故障，需要在skill文档中固化正确写法，并添加格式校验逻辑。

**延伸思考**

解决230001报错的标准排查顺序：第一查content格式是否为`[[{...}]]`而非`[{...}]`，第二查是否用了requests而非urllib，第三再查token和chat_id。多数情况下只需要修正格式就够了，不需要折腾token重置。

**标签**：Hermes × 飞书API × Post消息 × 230001错误 × 踩坑总结
