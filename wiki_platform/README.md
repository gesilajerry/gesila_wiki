# Jerry 知识维基平台

本地知识库维基，基于 Flask + D3.js 构建，支持私有化部署。

**在线预览（需本地运行）：** `http://localhost:5001`

---

## 🧠 核心功能

| 功能 | 说明 |
|------|------|
| 📄 **知识卡片浏览** | 按分类（概念卡/方法论/案例库/项目复盘/输入层/输出层）浏览所有知识卡片 |
| 🗺️ **知识图谱** | D3.js 力导向图，可视化三层架构（输入层→结构层→输出层）的关联关系 |
| 🔍 **全文搜索** | 输入关键词实时搜索所有卡片标题和正文 |
| 🏷️ **标签云** | 按标签聚合卡片，点击标签进入筛选结果 |
| 📱 **响应式 UI** | 适配手机竖屏、横屏和桌面端 |
| 🌐 **公网访问** | Ngrok 内网穿透，随时生成公网 URL |

---

## 🏗️ 三层架构

知识库按「输入→结构→输出」三层设计：

```
📥 输入层（01_Inbox）
  └─ 原始素材、日报、输入记录

🧱 结构层（概念卡 / 方法论 / 案例库 / 项目复盘）
  └─ 提炼后的结构化知识

📤 输出层（03_Output）
  └─ 小红书文章、对外发布内容
```

图谱中：
- **节点大小**：按层级（输入层最小/输出层最大）
- **节点颜色**：紫色=输入层，蓝色=结构层，黄色=输出层
- **连接关系**：通过共享标签、H2 主题重叠、内容引用建立

---

## 🚀 快速启动

```bash
# 进入目录
cd /Volumes/256G/gesila_wiki/wiki_platform

# 启动（自动监听 5001 端口）
./start.sh

# 或直接运行
python3 app.py
```

启动后访问：**http://localhost:5001**

---

## 🌐 配置公网访问（Ngrok）

```bash
# 1. 获取 Token：https://dashboard.ngrok.com/get-started/your-authtoken
# 2. 写入 Token 文件
echo 'YOUR_TOKEN_HERE' > ngrok_token.txt

# 3. 重启即可
./start.sh
# 日志中输出公网 URL
```

---

## 📁 项目结构

```
wiki_platform/
├── app.py              # Flask 主应用（4小时自动缓存刷新）
├── templates/          # HTML 模板
│   ├── home.html      # 首页（最新卡片 + 统计）
│   ├── card.html      # 知识卡片详情页
│   ├── graph.html     # 知识图谱（D3.js 力导向）
│   ├── search.html    # 搜索结果页
│   ├── tags.html      # 标签云页
│   └── category.html  # 分类浏览页
├── static/
│   └── d3.min.js     # D3.js v7
├── ngrok_token.txt    # Ngrok token
├── start.sh           # 启动脚本
└── README.md          # 本文件
```

---

## 🔧 数据来源

知识卡片路径：`/Volumes/256G/gesila_wiki/`

| 子目录 | 对应分类 | 层级 |
|--------|----------|------|
| `01_Inbox/` | 原始素材 | 输入层 |
| `02_Knowledge/概念卡/` | 概念卡 | 结构层 |
| `02_Knowledge/方法论/` | 方法论 | 结构层 |
| `02_Knowledge/案例库/` | 案例库 | 结构层 |
| `02_Knowledge/项目复盘/` | 项目复盘 | 结构层 |
| `03_Output/` | 输出内容 | 输出层 |

新增 `.md` 文件后重启服务即可自动出现在平台上。

---

## 📦 技术栈

- **后端**：Flask（Python）
- **前端**：原生 HTML/CSS/JS + D3.js v7
- **部署**：本地运行 + Ngrok 内网穿透
- **依赖**：仅 Python 3 + Flask + markdown2

---

## 👤 作者

Jerry · 知识管理系统 · 2026
