# gesila-compile Git同步故障排查（src refspec问题）

**背景**
2026-05-28，gesila-compile增量蒸馏执行完成后，Git本地提交成功，但推送失败，错误信息：
```
error: src refspec master does not match any
```

**核心洞察**
- **根因**：远端仓库使用 `main` 分支（GitHub默认），但本地推送时引用了不存在的 `master` 分支
- **常见场景**：旧版GitHub仓库从master迁移到main后，本地仍有master残留；或首次初始化时分支名不一致
- **正确做法**：
  1. 确认本地分支名：`git branch`
  2. 检查远端分支：`git ls-remote --heads origin`
  3. 如本地是master、远端是main，统一推送到main：`git push origin master:main`
  4. 或直接设置默认推送分支：`git config push.default matching` 或 `git config push.default current`

**对Jerry的意义**
- gesila_compile的distill.py内置git_sync()，cron自动运行
- 此错误为非阻塞（本地记录正常），但会导致增量内容未同步到GitHub
- 需修复后下次cron触发才能正常推送
- 当前凭证配置：netrc方式（不嵌token在URL），配置正确后此问题与凭证无关

**延伸思考**
- git remote URL中嵌token → 进程列表暴露token → 触发安全扫描 → Push Protection拦截，**必须用netrc方式**
- netrc权限必须是600，否则git不读取
- cron环境变量中写明文token也会触发安全扫描 → 用Python脚本读取token

**标签**：Hermes × gesila-compile × Git同步 × 故障排查 × OpenClaw
