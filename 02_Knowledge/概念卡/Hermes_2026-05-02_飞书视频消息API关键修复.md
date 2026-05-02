# 飞书视频消息API三个关键修复

**背景**
在调试小红书视频生成流水线飞书发送功能时，遭遇三个不同层面的API坑，跨越文件上传类型参数、HTTP客户端选择、消息类型字段等多个维度。流水线的video_final.mp4必须通过飞书发送，错误会直接导致每日视频发布失败。

**核心洞察**

**Bug1：msg_type类型错误导致230055**

飞书发送视频时，最初使用 `msg_type: "file"` 配合 `file_type: "mp4"` 上传，但飞书返回错误码 230055。

根因：飞书对不同文件类型有严格的msg_type对应关系。视频文件的正确组合是：
- `msg_type: "media"`（而非"file"）
- `file_type: "mp4"`（上传时）
- `msg_type: "media"` + `file_key`（发送时）

教训：飞书文件消息的API设计与文本不同，视频/音频/图片都走media类型，只有普通文档才走file类型。

**Bug2：urllib上传视频持续500**

Python 3.9环境下，用 `urllib.request.urlopen()` 上传视频文件到飞书持续返回 500 Internal Server Error，无论如何调整header或boundary都无法解决。

修复方案：完全放弃urllib，改用 `requests.post()` 的 `files=` 参数上传。requests库对multipart/form-data的处理更完善，能够正确处理文件编码和边界问题。

教训：在飞书文件上传场景，requests的兼容性显著优于urllib，不能迷信标准库。

**Bug3：file_type与msg_type必须严格匹配**

飞书视频消息API要求上传时的 `file_type` 和发送时的 `msg_type` 形成正确对应：
- 上传：POST /open-apis/im/v1/medias，file_type决定文件类型
- 发送：POST /open-apis/im/v1/messages，msg_type决定消息类型

两者不匹配（如上传用mp4/发送用file）就会触发230055。

**飞书视频发送完整正确流程**：
1. 用 requests.post + files= 上传文件到 GET /open-apis/im/v1/medias?type=image 获取 file_key
2. 用 file_key 发送消息，msg_type="image"，content包含file_key

**对Jerry的意义**

这三个修复是飞书视频消息发送的完整避坑指南。Jerry的小红书视频流水线已经完全依赖这套方案，video_final.mp4通过这套方案稳定发送到飞书。每次cron执行后都会记录msg_type是否正确，已成为流水线的标准组件。

**延伸思考**

这套修复方案也可以推广到其他文件类型（PDF、图片等）。核心原则：
1. 先用requests上传获取file_key
2. 发送时msg_type必须与file_type对应
3. 不要试图用urllib替代requests

230055错误的自动化检测和报警机制值得加入流水线，当发送失败时自动切换到text描述而非静默失败。

**标签**：Hermes × 飞书API × 视频消息 × Bug修复 × requests
