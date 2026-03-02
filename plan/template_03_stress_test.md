# Template 03 — 对抗性压力测试
# 用途：用分层攻击性问题（10-20 题，按项目类型组装）找出 SDD 的设计漏洞
# 使用对话：Gemini（必须全新对话，和写 SDD 的对话完全隔离）
# 新建对话：必须，这是硬性要求

---

## 为什么必须新建对话

写 SDD 的 AI 对自己的设计有"感情"，会倾向于为漏洞辩护。
新对话的 AI 没有包袱，能更客观地发现问题。

---

## 使用步骤

1. **新建** Gemini 对话（关掉之前的窗口）
2. 根据项目类型确定问题集（见 `skills/stress-test-prompts.md` 中的项目类型选择表）
3. 先粘贴"上下文设定 Prompt"
4. 逐一粘贴对应层级的攻击问题（可以批量粘贴，也可以逐个）
5. 收集结构化 Scorecard，生成漏洞记录表（见第三步：默认手动填写，自动化可选）

---

## 第一步：上下文设定 Prompt

```
我有一份软件设计文档（SDD），需要你对它进行严格的对抗性审查。
你的角色是"挑剔的架构师"，目标是找出设计漏洞、隐患和未考虑的场景。
不需要客气，不需要肯定优点，只需要找问题。

以下是 SDD 全文：

[粘贴 spec_v1.md 全文]

---

文档已读取完毕。我将逐一向你提问，请针对这份具体的设计文档回答。

回答格式要求：
1. 先用自然语言详细分析问题（保留你的推理过程）
2. 最后必须输出一个 JSON 格式的结构化评判，格式如下：

```json
{"question_id": "U1", "passed": true, "severity": "none", "vulnerability": "无"}
```

- passed: true 表示设计已充分覆盖，false 表示存在漏洞
- severity: "none"（通过）/ "low" / "medium" / "high"
- vulnerability: 一句话描述发现的问题（通过时填"无"）

请严格遵循此格式，每个回答最后都要有这个 JSON 行。
```

---

## 第二步：按项目类型提问

从 `skills/stress-test-prompts.md` 中选取对应层级的问题，逐一提问。

### 项目类型速查

| 项目类型 | 问题集 | 题数 |
|---------|--------|------|
| CLI 工具 / 纯逻辑库 | U1-U10 | 10 |
| Web 应用 / API 服务 | U1-U10 + W1-W5 | 15 |
| 数据密集型系统 | U1-U10 + D1-D5 | 15 |
| 全栈 Web + 数据系统 | U1-U10 + W1-W5 + D1-D5 | 20 |

完整问题列表见 `skills/stress-test-prompts.md`。

> **提示**: 每个问题中的 `[方括号占位符]` 需替换为你项目中的具体实体名称。

---

## 第三步：收集结构化 Scorecard

从 AI 每个回答末尾提取 JSON 行，汇总为 scorecard 数组：

```json
[
  {"question_id": "U1", "passed": true, "severity": "none", "vulnerability": "无"},
  {"question_id": "U2", "passed": false, "severity": "high", "vulnerability": "无并发控制机制，两人同时修改会产生数据覆盖"},
  {"question_id": "W1", "passed": false, "severity": "medium", "vulnerability": "数据库连接池未配置上限，峰值时可能耗尽连接"},
  ...
]
```

保存为 `spec/scorecard_v1.json`。

### 默认路径：手动生成漏洞记录表

根据 scorecard 数据手动填写以下记录表：

### 可选路径：自动化解析（需 tools/scorecard_parser.py）

> 当 `tools/scorecard_parser.py` 就绪后，可切换为自动化路径：
>
> ```bash
> python tools/scorecard_parser.py spec/scorecard_v1.json
> ```
>
> 工具会输出：
> 1. **漏洞记录表**（Markdown 格式，可直接保存为 `stress_test_v1.md`）
> 2. **收敛判断**（基于阈值：0 高严重度 + ≤3 中严重度 = 收敛）

---

## 手动记录表

```markdown
## 压力测试漏洞记录
日期:
Spec 版本: v1.0

| 题号 | 通过 | 问题描述 | 严重程度 |
|-----|------|---------|---------|
| U1  | ✅ / ⚠️ | | none/low/medium/high |
| U2  | | | |
| ...  | | | |
| [最后一题] | | | |

高严重度问题数: X
中严重度问题数: X

收敛判断:
□ 收敛（0 高 + ≤3 中）→ 锁定 spec，进入 Step 5
□ 未收敛 → 进入 Template 04 修订
```

---

## 输出保存

```
项目目录/
└── spec/
    ├── raw_requirements.md
    ├── spec_v1.md
    ├── scorecard_v1.json      （本步骤输出：结构化评判数据）
    └── stress_test_v1.md      （由 scorecard 生成：漏洞记录表 + 收敛判断）
```
