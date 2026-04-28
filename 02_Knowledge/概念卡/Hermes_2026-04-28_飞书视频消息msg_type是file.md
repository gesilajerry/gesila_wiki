# 飞书视频消息：msg_type是file不是media

**背景**
2026-04-28 20:00任务修复了视频msg_type错误：之前传`media`报错，改为`file`后成功发送。

**核心洞察**
飞书IM视频消息的正确格式：
- **上传接口**：`POST /im/v1/files`（multipart，file_type=mp4）
- **发送接口**：`POST /im/v1/messages`
- **msg_type**：`file`（不是`media`！）
- **content**：`{"file_key": "file_v3_xxx"}`（只传file_key，不传video_id/image_key）

```python
payload = {
    "receive_id": CHAT_ID,
    "msg_type": "file",
    "content": json.dumps({"file_key": file_key})
}
```

**对Jerry的意义**
视频上传和发送是两套独立接口。视频先通过`/im/v1/files`上传获取file_key，再以`file`类型消息发送。封面图(image_key)是可选字段，不传不影响发送。

**延伸思考**
与图片消息对比：图片用`/im/v1/images`上传+`msg_type=image`，视频用`/im/v1/files`上传+`msg_type=file`。两套体系不要混淆。

**标签**：Hermes × 飞书API × 视频消息 × 接口规范
