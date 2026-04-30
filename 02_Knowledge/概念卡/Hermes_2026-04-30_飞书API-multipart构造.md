# 飞书 API multipart/form-data 构造规范

**背景**
飞书开放平台 API 在上传图片/文件时要求 multipart/form-data 格式。构造方式不对会报 234001/400 错误，导致上传失败。根本原因是用 `requests_toolbelt.MultipartEncoder` 把非文件字段（如 `image_type`、`file_type`）和文件字段混在一个 `fields` 字典里一起编码——飞书服务端不认这种构造。

**核心洞察**
正确做法：**用 Python requests 的 `files` 和 `data` 参数分离传参**，而非 MultipartEncoder 一次性构造。

图片上传：
```python
files = {"image": (fname, f, "image/jpeg")}
data = {"image_type": "message"}
r = requests.post(url, headers={"Authorization": f"Bearer {token}"}, files=files, data=data, timeout=30)
```

视频上传（正确组合）：
```python
# Step 1：file_type 必须是 "stream"，不是 "mp4"
files = {"file": (fname, f, "video/mp4")}
data = {"file_type": "stream"}
r = requests.post("https://open.feishu.cn/open-apis/im/v1/files",
    headers={"Authorization": f"Bearer {token}"},
    files=files, data=data, timeout=120)
file_key = r.json()["data"]["file_key"]

# Step 2：msg_type 必须是 "file"，不是 "media" 或 "video"
payload = {
    "receive_id": CHAT_ID,
    "msg_type": "file",
    "content": json.dumps({"file_key": file_key})
}
# 注意：content 里只有 file_key，不要加 video_id 等多余字段
```

错误对照表：
| 错误码 | 原因 | 解决 |
|--------|------|------|
| 234001 | 非文件字段（image_type/file_type）放进了 MultipartEncoder | 用 files+data 分离 |
| 400 | multipart 字段名错（如 filename=） | 非文件字段不加 filename= |
| 230055 | file_type=mp4 + msg_type=file | file_type 换成 stream |
| 230001 | msg_type=media/video | 用 msg_type=file |
| 230001 | content 里有 video_id 等多余字段 | 只留 {"file_key": "..."} |

**对 Jerry 的意义**
所有飞书文件发送（图片、视频、文件）都必须用 files+data 分离方式。2026-04-30 日志证明此方式已验证可行，MultipartEncoder 方式已踩坑排除。

**延伸思考**
核心原则：HTTP multipart/form-data 中，文件字段用 `files=` 参数（元组形式），元数据字段用 `data=` 参数。两者永远不要合并进同一个编码器。

**标签**：Hermes × 飞书API × multipart × 上传 × 错误排查
