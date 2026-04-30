# 后台 Python 进程 stdout 缓冲问题与解法

**背景**
在 Hermes 环境中使用 `terminal(background=true)` 启动长时 Python 脚本时，print 输出不显示或很久才出现。脚本明明在跑（有 PID），但日志文件一直是空的。调试时容易误判为进程卡死。

**核心洞察**
Python stdout 默认是**全缓冲**（full buffering），在非交互环境（background=true / subprocess）中不会实时刷新。输出堆积在内存缓冲区，直到缓冲区满或进程结束才一次性吐出。

两处都要改：
1. Python 脚本内：`print()` 加 `flush=True`
2. 启动命令：加 `-u` 参数（unbuffered mode）

```python
# ✅ 正确：print 加 flush=True
print("开始生成图片...", flush=True)
print(f"进度: {i}/{total}", flush=True)

# ✅ 正确：启动时加 -u 参数
terminal(background=true,
    command='/path/to/.venv/bin/python -u /tmp/gen_video.py > /tmp/gen.log 2>&1')
```

调试技巧：先用 `timeout 45` 前台跑一次确认脚本能跑通，再放后台长跑。前台模式天然逐字符刷新，能及时发现脚本逻辑错误。

**对 Jerry 的意义**
在视频生成流水线（图片串行生成、ffmpeg 拼接、混音压缩）等长时任务中，必须用 `-u` + `flush=True` 组合才能实时监控进度。纯后台运行时无输出，容易误判为挂死而 kill 掉正在正常运行的进程。

**延伸思考**
另一个常见误解：用 `.venv/bin/activate && python script.py` 启动后台进程会挂住。原因是 venv activation 在 login shell（`-l -i -c`）里等待终端输入。正确做法是直接调 python 解释器：
```python
# ❌ 错误
terminal(background=true, command='source /path/to/.venv/bin/activate && python script.py')

# ✅ 正确
terminal(background=true,
    command='/path/to/.venv/bin/python /tmp/gen_video.py > /tmp/gen.log 2>&1')
```

**标签**：Hermes × Python × 后台进程 × stdout缓冲 × 调试
