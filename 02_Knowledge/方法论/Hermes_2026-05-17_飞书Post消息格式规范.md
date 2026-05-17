# 飞书Post消息content格式规范

**背景**
飞书开放平台 IM API 的 post 消息类型，content 字段格式极易报 230001 错误（invalid message content），困扰多个脚本。经过多次踩坑，总结出正确格式规范。

**核心洞察**

飞书 post 消息的 content 是「数组的数组」结构：`[[{...}], [{...}], ...]`

- **外层数组**：包含多个段落（paragraph），每个段落是一个内层数组
- **内层数组**：该段落内的多个元素（text、at、image等标签），通常只有一个元素
- **正确示例**：
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
  ```

**最容易犯的错误**
1. 扁平数组 `[{"tag": "text", "text": "..."}]` 而非 `[[{"tag": "text", "text": "..."}]]`，导致 230001
2. content 字段先 `json.dumps()` 了，导致双重序列化
3. 报错 230001 后以为是 token 问题，实际是 content 格式不对

**对Jerry的意义**
- 多个 cron 任务（AI简报、财经简报）依赖飞书发送，必须确保格式正确
- 复用此模板可以避免反复调试

**延伸思考**
- 用 `requests` 而非 `urllib.request`——Python 3.9 urllib 对飞书文件上传和部分 POST 持续返回 500
- 先用 text 类型消息测试 chat_id 和 token 是否正确，再用 post 格式

**标签**：Hermes × 飞书API × Post消息格式
