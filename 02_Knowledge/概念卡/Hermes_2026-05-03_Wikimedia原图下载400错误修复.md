# Wikimedia原图下载400错误修复

**背景**
小红书预生成流水线中，使用 Wikimedia Commons 原始图片 URL（如 `https://upload.wikimedia.org/wikipedia/commons/{path}/{filename}`）会返回 HTTP 400 错误，导致名画原图下载失败，视频素材缺失。

**核心洞察**
Wikimedia 的原始图片上传路径对请求头、Referer 等有验证。正确做法是使用**缩略图路径**（thumb），格式为：
```
https://upload.wikimedia.org/wikipedia/commons/thumb/{id}/{filename}/800px-{filename}
```
其中：
- `id` 是图片的目录哈希（如 `a/a7`）
- `filename` 是完整的文件名（如 `The_Scream.jpg`）
- `800px-{filename}` 表示缩放到 800 像素宽度（足够用于小红书配图，且绕过原图路径的验证）

**对Jerry的意义**
- 2026-05-03 下午批次中，维米尔《戴珍珠耳环的少女》原图下载 400 错误就是这个原因
- 修复后不需要改图片 ID，只需把 URL 替换为 `/thumb/{id}/{filename}/800px-{filename}` 形式
- thumb 路径对所有 Wikimedia Commons 图片有效，不依赖文件是否存在原图

**延伸思考**
Wikimedia 的 thumb 路径实际上是实时生成的（CDN），不需要服务器端预先生成缩略图。若需要更高分辨率，可在 `/thumb/` 后指定更大数值（如 1200px）。

**标签**：Hermes × 小红书 × Wikimedia × 图片下载 × 400错误
