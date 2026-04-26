# 飞书 IM API 发送媒体内容最佳实践

**背景**
2026-04-26全天的cron任务都依赖飞书API发送消息。从当天的日志中可以看到多个关键发现：图片超过5MB会导致code 234006错误、视频发送格式与图片完全不同、curl在此环境对飞书不稳定。这些问题在多个任务中被反复验证和解决。

**核心洞察**

**1. 图片发送：message_image类型 + 5MB上限**
```
上传 → POST https://open.feishu.cn/open-apis/im/v1/images
       Content-Type: multipart/form-data
       字段: image_type=message, image=二进制

发送 → POST https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id
       payload: {"receive_id": "oc_xxx", "msg_type": "image", "content": "{\"image_key\":\"...\"}"}
```
**压缩方法（macOS内置）**：
```bash
sips -s formatOptions 70 /tmp/original.jpg --out /tmp/compressed.jpg
# 11.3MB → 4.5MB，约70%质量
```
超过5MB的文件上传返回 `code 234006`。

**2. 视频发送：msg_type=media，content只需file_key**
```
上传 → POST https://open.feishu.cn/open-apis/im/v1/files
       Content-Type: multipart/form-data (MultipartEncoder)
       字段: file_type=mp4, file_name, file_size, file=二进制

发送 → payload: {"receive_id": "oc_xxx", "msg_type": "media", "content": "{\"file_key\":\"...\"}"}
```
**注意**：`msg_type=media` 而非 `file`，`content` 只需 `{"file_key": "file_v3_xxx"}`，不要加 `video_id` 等多余字段。

**3. 文本消息：必须用json=参数，不要用data=**
```python
# 正确
requests.post(url, headers=headers, json={"text": "内容"})

# 错误（会导致code 230001）
requests.post(url, headers=headers, data=json.dumps({"text": "内容"}))
```

**4. receive_id_type必须是chat_id**
报错 `99992361 cross app` 即为类型选错。必须是 `receive_id_type=chat_id`。

**5. tenant_access_token有效期2小时，每次发送前重新获取**
```
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
Body: {"app_id": "...", "app_secret": "..."}
```

**6. curl不稳定，Python requests更可靠**
日志明确记录："统一使用 Python requests（curl 在此环境中对 Feishu 不稳定）"。

**7. 发送顺序：先图后文**
当天小红书运营任务的发送顺序：原图 → AI图1 → AI图2 → AI图3 → 文案全文。

**对Jerry的意义**
飞书IM API是Hermes每日推送的核心通道。掌握图片压缩、视频msg_type=media、json=data区别这三个关键点，可以避免大多数推送失败。这些坑分散在多个cron任务中，今天是首次系统性总结。

**延伸思考**
飞书API的问题排查路径：先查官方文档（https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/im-v1/message/create_json），比试错快得多。文档中 `msg_type=media` 的content格式是 `{"file_key": "..."}` 而非 `{"video_id"}`。

**标签**：Hermes × 飞书API × 媒体发送 × API调试 × 图片压缩
