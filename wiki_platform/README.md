# Jerry 知识维基平台

本地知识库维基百科，基于 Flask + D3.js 构建。

## 功能

- 📄 **传统浏览**：按分类浏览所有知识卡片
- 🔗 **内部链接**：文档间关键词自动互链
- 🗺️ **知识图谱**：D3.js 力导向图，可视化知识点关联（节点按标签/H2/提及关系互联）
- 🔍 **搜索**：全文搜索所有卡片
- 🏷️ **标签云**：按标签聚合知识
- 📱 **响应式**：适配手机竖屏/横屏/桌面

## 快速启动

```bash
cd /Volumes/256G/gesila_wiki/wiki_platform
./start.sh
```

本地访问：**http://localhost:5001**
公网访问：启动后日志中输出 Ngrok URL

## Ngrok 公网访问

1. 获取 Authtoken：https://dashboard.ngrok.com/get-started/your-authtoken
2. 写入 token：
   ```bash
   echo 'YOUR_TOKEN_HERE' > ngrok_token.txt
   ```
3. 重启：`./start.sh`
4. 日志中会输出公网 URL

## 目录结构

```
wiki_platform/
  app.py              # Flask 主应用（含自动缓存刷新）
  templates/          # HTML 模板（首页/卡片/图谱/分类/搜索/标签）
  static/
    d3.min.js        # D3.js 力导向图库
  ngrok_token.txt     # Ngrok token（留空，启动后自动启用公网）
  start.sh            # 启动脚本
  wiki.log            # 运行日志
```

## 知识库源路径

数据来源：`/Volumes/256G/gesila_wiki/`
- `02_Knowledge/概念卡/`
- `02_Knowledge/方法论/`
- `02_Knowledge/案例库/`
- `02_Knowledge/项目复盘/`
- `03_Output/`
- `01_Inbox/`

新增 .md 文件后，**每4小时自动刷新**加载新卡片（也可重启服务立即生效）。

## 依赖

```
Flask
markdown2
pyngrok (可选，用于 Ngrok 公网访问)
```

安装：`pip3 install flask markdown2 pyngrok --break-system-packages`

## 知识图谱说明

- **节点颜色**：蓝=概念卡，绿=方法论，橙=案例库，红=项目复盘，紫=其他
- **连接关系**：共享标签 / H2章节标题交叉引用 / 文档正文提及
- **交互**：点击节点显示摘要，点击"查看详情"跳转卡片页；拖拽移动节点；滚轮缩放
- **搜索**：右上角搜索框，输入关键词高亮匹配节点
