# xhs-cli puppeteer-core 模块损坏修复

**背景**
小红书BHR（自动化发布）依赖xhs-cli工具，而xhs-cli依赖puppeteer-core模块。2026年5月18日运行xhs-vangogh系列任务时，遭遇puppeteer-core模块加载失败导致BHR自动化发布全部失败。根本原因是npm全局包的嵌套目录损坏。

**核心洞察**
xhs-cli的puppeteer-core模块通过npm全局安装，正常路径为：`~/.npm-global/lib/node_modules/xhs-cli/node_modules/puppeteer-core`。但当全局包目录结构出现嵌套损坏（错误的嵌套目录）时，Node.js无法正确加载该模块。

**错误现象**：
```
Error: Cannot find module '/Users/mac/.npm-global/lib/node_modules/xhs-cli/node_modules/puppeteer-core'
```

**修复步骤**：
1. 诊断问题：确认是嵌套目录结构损坏，不是puppeteer-core本身缺失
2. 删除错误的嵌套目录
3. 重建正确的全局模块软链接
4. 验证：重新运行BHR自动化发布

**对Jerry的意义**
xhs-cli是每日小红书图文发布的自动化核心工具，puppeteer-core的加载失败会导致整个梵高融合风图文流水线中断。遇到BHR发布失败时，应首先检查：
- `ls ~/.npm-global/lib/node_modules/xhs-cli/node_modules/` 目录结构是否正常
- puppeteer-core是否存在且路径正确
- 软链接是否指向正确的全局包位置

**延伸思考**
npm全局包的嵌套损坏通常发生在多次install/uninstall或版本切换后。维护自动化工具时，定期检查关键全局包的目录结构完整性可以预防这类隐性故障。建议在cron任务日志中增加npm包完整性检查步骤。

**标签**：Hermes × xhs-cli × BHR自动化 × puppeteer-core × 小红书
