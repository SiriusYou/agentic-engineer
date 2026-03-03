# Tech Stack

## 语言选择决策标准

基于 TRACK-001 实践经验，使用以下标准选择实现语言。

### 决策表

| 判断维度 | 选 Python | 选 TypeScript |
|---------|----------|--------------|
| 项目类型 | CLI 工具、lint 工具、纯逻辑库、数据处理脚本 | Web 前端、全栈应用、需要浏览器运行的库 |
| I/O 模式 | 文件系统读写、stdin/stdout 管道、无交互式 UI | HTTP 服务、WebSocket、浏览器 DOM 交互 |
| 正则需求 | 复杂正则（lookbehind、VERBOSE 模式、re.MULTILINE） | 简单匹配足够 |
| 依赖要求 | stdlib 足够（pathlib、re、json、argparse） | 需要 npm 生态特定库 |
| 测试生态 | pytest（fixture、parametrize 成熟） | Jest/Vitest（需要前端 DOM 测试时） |
| 部署目标 | 服务器端脚本、CI pipeline、开发者本地工具 | CDN、Vercel、浏览器 |

### 决策树

```
项目需要浏览器运行？
├── 是 → TypeScript
└── 否 → 项目核心是文件处理/文本匹配？
    ├── 是 → Python（stdlib 覆盖 90%+ 需求）
    └── 否 → 项目需要 HTTP 服务？
        ├── 是 → TypeScript（全栈共享类型）或 Python（FastAPI/Django）
        └── 否 → Python（默认选择，启动成本低）
```

### TRACK-001 经验

`check_workflow_consistency.py` 选择 Python 的理由：
- 核心逻辑是 Markdown 文件解析 + 正则匹配 → `re` + `pathlib` 完全覆盖
- 无外部依赖，stdlib 足够
- pytest parametrize 简化了 53 个测试用例的编写
- 正则调试（`re.VERBOSE`、命名捕获组）比 JS 更方便

### 当前技术栈

| 层次 | 选型 | 用途 |
|------|------|------|
| 方法论工具 | Python 3.8+ | check_workflow_consistency, scorecard_parser |
| 测试框架 | pytest | 单元测试 + 参数化测试 |
| CI | GitHub Actions | Python 3.8 + 3.12 矩阵 |
| 格式化 | Black | Python 代码格式化 |
