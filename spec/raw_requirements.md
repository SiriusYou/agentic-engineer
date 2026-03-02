# check_workflow_consistency.py — 原始需求

---

## 1. 核心目标

自动检测 agentic-engineer 框架内文档之间的一致性问题，在人工审查之前发现引用断裂、数值偏移、命名偏差等静默错误，防止方法论文档随迭代逐渐失去内部一致性。

---

## 2. 目标用户

- 框架维护者（当前 = 我自己）：每次修改文档后运行，确认没有引入不一致
- 未来贡献者：clone 项目后运行，验证本地文档状态健康
- CI 系统（未来）：作为 pre-commit 或 GitHub Actions 检查步骤

---

## 3. 核心功能列表

### 3.1 文件路径引用检查
- 用户可以扫描所有 Markdown 文件中的相对路径引用（如 `plan/quick_reference.md`、`skills/SKILL.md`）
- 用户可以看到哪些引用指向不存在的文件
- 检查范围：plan/、skills/、conductor/、README.md、spec/README.md

### 3.2 收敛阈值一致性检查
- 用户可以验证"0 高 + ≤3 中"这个收敛阈值在所有出现位置的数值一致
- 已知出现位置：
  - `plan/quick_reference.md`（文字描述）
  - `skills/planning-workflow.md`（退出标准）
  - `skills/stress-test-prompts.md`（收敛判断模板）
  - `tools/scorecard_parser.py`（MEDIUM_CONVERGENCE_THRESHOLD 常量）

### 3.3 步骤编号和名称一致性检查
- 用户可以验证 Step 1-5 和 Phase 0 在所有文档中的编号和名称一致
- 检查步骤名称映射：
  - Step 1 = 灵感捕获
  - Step 2 = SDD 生成
  - Step 3 = 压力测试
  - Step 4 = 反馈修正 / 迭代修正
  - Step 5 = 锁定执行 / 执行
  - Phase 0 = 复盘 / 项目复盘

### 3.4 spec/ 文件命名规范检查
- 用户可以验证 spec/ 目录下的文件是否符合接口契约命名规范
- 合法文件名：raw_requirements.md, spec_v*.md, scorecard_v*.json, stress_test_v*.md, spec_final.md, spec_final_v*.md, postmortem_v*.md, README.md
- 非法文件名应被报告为警告

### 3.5 tracks.md 状态语义检查
- 用户可以验证 tracks.md 中每条 track 的状态字段使用单一值
- 合法状态：pending, active, completed
- 检查：表格中 Status 列与详情中 **状态：** 行是否一致

### 3.6 压力测试题号完整性检查
- 用户可以验证 stress-test-prompts.md 中的题号序列完整（U1-U10, W1-W5, D1-D5）
- 检查题号映射表中新旧对照是否完整

### 3.7 汇总报告输出
- 用户可以看到一份结构化的检查报告，包含：
  - 通过的检查项数量
  - 失败的检查项数量和具体位置
  - 警告项数量和具体内容
- 退出码：0 = 全部通过，1 = 有失败项，2 = 有文件读取错误

---

## 4. 已知约束

### 技术约束
- Python 3.8+，仅使用标准库（与 scorecard_parser.py 一致）
- 不依赖任何第三方包（pathlib, re, json, argparse, sys 即可）
- 项目根目录 = agentic-engineer/（工具在 tools/ 下运行）

### 设计约束
- CLI I/O 契约与 scorecard_parser 一致：检查报告输出到 stdout，警告输出到 stderr
- 退出码语义与 scorecard_parser 一致：0 = SUCCESS, 1 = VALIDATION_ERROR, 2 = FILE_ERROR
- 单文件实现（tools/check_workflow_consistency.py），配套测试文件（tools/test_check_workflow_consistency.py）

### 时间约束
- TRACK-001 时间盒内完成（5 天总预算，实现在 Day 4）

---

## 5. 已知风险

- Markdown 中的路径引用格式不统一（有的在代码块内、有的在行内 backtick 中、有的在纯文本中），正则匹配可能遗漏或误报
- 收敛阈值的文字表述可能有多种写法（"0 高 + ≤3 中"、"0 high + at most 3 medium"、数字常量 3），需要覆盖多种模式
- 文档中可能存在注释掉的引用或示例路径，需要区分"真实引用"和"示例/模板引用"
- spec/ 目录在不同项目中可能为空或不存在，工具应优雅处理

---

## 6. 明确不做的事

- **不做** Markdown 语法检查（已有 markdownlint 等工具）
- **不做** 拼写检查（超出范围）
- **不做** SDD 内容质量评估（那是压力测试的工作）
- **不做** 自动修复（只报告，不改写文件）
- **不做** Git 历史分析（只检查当前工作目录状态）
- **不做** 跨项目检查（只检查 agentic-engineer/ 内的文件）
