# mmx CLI 输出路径行为与并发限制

**背景**
mmx CLI 是 MiniMax 的命令行工具，用于图片生成、音乐生成和 TTS 配音。其 `--output` 参数行为与直觉不符，导致文件找不到或路径错误。图片生成还有严格的并发限制，误用并发会导致全部失败。

**核心洞察**

### 1. `--output` 实际上是目录，不是完整路径
```bash
# ❌ 错误：文件实际保存到 CWD，文件名为自动生成的时间戳名
mmx speech synthesize "text" --output /tmp/my_tts.mp3
# 返回 {"saved": "speech_2026-04-26-02-10-10.mp3"}
# 实际位置：./speech_2026-04-26-02-10-10.mp3（当前工作目录）

# ✅ 正确：用 --output . 然后手动 copy
cmd = 'mmx speech synthesize "text" --voice male-qn-jingying --output .'
r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
saved = json.loads(r.stdout)['saved']
shutil.copy(saved, "/tmp/my_tts.mp3")
```

### 2. 输出文件名自动加 `_001` 后缀
```bash
# 请求 --out-prefix foo.jpg
# 实际输出：foo_001.jpg（不是 foo.jpg）
# 解决：生成后重命名
for f in *_001.jpg; do mv "$f" "${f%_001.jpg}.jpg"; done
```

### 3. 图片生成禁止并发（严格限制）
```bash
# ❌ 错误：并发全部失败，额度瞬间耗尽
mmx image generate "scene 1" --out-prefix img_1 &
mmx image generate "scene 2" --out-prefix img_2 &
wait  # 此时往往全部失败

# ✅ 正确：串行逐张，间隔5秒
for i in $(seq -f "%02g" 1 24); do
  [ -f "img_$i.jpg" ] && continue
  mmx image generate "prompt" --model image-01 --aspect-ratio 9:16 \
    --out-dir /Volumes/256G/mywork --out-prefix img_$i
  sleep 5
done
```
mmx 图片 API 有速率限制，严格单请求。并发生成会导致全部报 "usage limit exceeded"，浪费整批额度。音乐生成可批量，图片不行。

**对 Jerry 的意义**
小红书内容生成流水线（文案→TTS→N张AI图→视频拼接）必须严格串行执行图片生成，每张间隔≥5秒。这是已验证的生产级约束，不能绕过。

**延伸思考**
图片串行 + 间隔5秒的策略可以配合文件存在检查实现断点续传：已存在的图片跳过，只生成缺失的。配合计数器文件，可以实现可靠的每日增量生成。

**标签**：Hermes × mmxCLI × 图片生成 × TTS × 并发限制
