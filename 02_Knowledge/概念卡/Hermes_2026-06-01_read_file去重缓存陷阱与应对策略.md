# read_file 工具去重缓存陷阱与应对策略

**背景**
Hermes 的 `read_file` 工具内置 deduplication 缓存机制：在同一进程中，对同一文件路径的第二次及后续调用会返回 `status: unchanged`，实际内容读不到。在 cron 任务（处理大批量文件）和超大文件（300KB+推送日报）场景下极易踩坑。

**核心洞察**

## 1. 缓存生效条件
- 同一进程中，对相同路径的第二次调用起
- 文件越大（如推送日报 300KB+），越容易触发 deduplication
- cron 输出文件带时间戳但在同一 job_id 目录 → 路径相同，触发缓存

## 2. 症状
- 调用 `read_file` 两次读同一文件，第二次返回空内容
- cron 任务读取归档日志时，大量内容块读不到
- 代码中明明有内容但解析结果为空

## 3. 应对策略
### 策略A：Python原生文件读取（推荐）
```python
from pathlib import Path
content = Path("/path/to/file.md").read_text(encoding='utf-8', errors='replace')
```
不依赖 read_file 工具，绕过 deduplication 缓存。唯一缺点是读取路径受工具沙箱限制。

### 策略B：terminal cat 命令
```python
result = terminal("cat /path/to/file.md")
content = result['output']
```
terminal 沙箱与 read_file 沙箱独立，cat 命令不走 read_file 缓存。

### 策略C：分块读取
对于超大型文件（如推送日报 513KB），先 split 按 `## 来源任务` 拆分成 blocks，再对每个 block 单独处理。每次 split 操作会触发一次 read_file 读取，但后续提取 job 名、内容时用 re.search 直接从内存中的 content 字符串处理，不再调用 read_file。

## 4. 实战模式
```
# 推送日报处理标准流程
1. read_file 一次性读全文（第一次调用，走缓存）
2. 按 "## 来源任务" split 成 list
3. 对每个 block 做 re.search 提取
   — 不再调用 read_file，走内存字符串
4. 对特定 job 内容，用 Python open() 读（若需要二次读取）
```
这样既利用 read_file 一次性加载全文，又避免在同一路径上重复调用。

**对Jerry的意义**
维基平台运维中所有 cron 归档任务都依赖读取大文件日志，正确应对 read_file 缓存是任务稳定性的基础。GESILA compile 增量蒸馏和结构层提炼均需读取大型归档日志，必须掌握此模式。

**延伸思考**
read_file 的 deduplication 缓存设计对减少重复 I/O 有正面作用，但在需要多次读取同一文件的场景下是反直觉的。理解其机制后，可以"主动设计读取顺序"来规避——先 read_file 全局内容，再 split 分块，最后在内存中处理所有子块。

**标签**：Hermes × 工具陷阱 × 去重缓存 × cron × 知识管理