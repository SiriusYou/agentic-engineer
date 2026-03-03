# spec-lint — 软件设计文档 (SDD)
版本: v1.1
状态: Final
最后更新: 2026-03-03

---

## 1. 项目概述

### 1.1 目标
对单个 SDD 文档（spec_final.md）进行结构化格式检查，验证其是否满足 SDD 模板的必填要求。

### 1.2 核心用户场景
- 作为方法论使用者，我希望在锁定 spec 前运行 `spec-lint spec/spec_final.md`，确认文档完整
- 作为 CI pipeline，我希望自动检查 SDD 文档完整性，保证质量门禁
- 作为压力测试审查者，我希望验证模式定义章节的正反例完整性

### 1.3 系统边界
**不在范围内：**
- 语义质量判断（"SDD 设计得好不好"）
- 跨文件引用检查（已由 check_workflow_consistency 覆盖）
- SDD 生成或自动修复

---

## 2. 技术栈

| 层次 | 技术选型 | 版本 | 选择理由 |
|------|---------|------|---------|
| 语言 | Python | 3.8+ | stdlib 覆盖所有需求，与现有工具一致 |
| 测试 | pytest | 任意 | parametrize 简化多场景测试 |
| 格式化 | Black | 任意 | 项目标准 |

**环境变量清单：**
无（纯 CLI 工具，所有配置通过命令行参数传入）

---

## 3. 系统架构

### 3.1 组件总览

```
spec-lint
├── CLI 入口 (argparse)
├── DocumentParser — 解析 Markdown 文档结构
├── Checkers[] — 可插拔检查器数组
│   ├── SectionPresenceChecker — 必填章节存在性
│   ├── HeaderFormatChecker — 文档头部格式
│   ├── TBDMarkerChecker — 残留 TBD/待定标记
│   ├── ExitCodeTableChecker — CLI 接口 exit code 表
│   └── PatternExampleChecker — 正则正反例完整性
├── LintReport — 检查结果聚合
└── ReportFormatter — 输出格式化（summary/json/markdown）
```

### 3.2 组件详情

#### DocumentParser
- **职责**：将 Markdown 文本解析为结构化的章节树
- **输入**：Markdown 文本（字符串）
- **输出**：`Document` 数据结构
- **依赖**：无
- **不负责**：验证章节内容的语义正确性

#### SectionPresenceChecker
- **职责**：验证必填章节（1-6）全部存在
- **输入**：`Document`
- **输出**：`list[LintResult]`

#### HeaderFormatChecker
- **职责**：验证文档头部包含版本、状态、日期字段
- **输入**：`Document` 的前 10 行
- **输出**：`list[LintResult]`

#### TBDMarkerChecker
- **职责**：检测文档中残留的待定标记
- **输入**：`Document` 全文
- **输出**：`list[LintResult]`

#### ExitCodeTableChecker
- **职责**：当 CLI 接口变体（4.B）存在时，验证 exit code 表完整
- **输入**：`Document` 的章节 4 内容
- **输出**：`list[LintResult]`
- **触发条件**：文档包含 `4.B` 相关标题

#### PatternExampleChecker
- **职责**：验证章节 8 的每个检查器有 3 正例 + 3 反例
- **输入**：`Document` 的章节 8 内容
- **输出**：`list[LintResult]`
- **触发条件**：文档包含章节 8

---

## 4. 接口定义

> 本项目为无状态 CLI 工具，使用变体 4.B。

### 4.B.1 命令行参数

```
用法: spec_lint.py [选项] <spec_file>

位置参数:
  spec_file             SDD 文档路径（.md 文件）

选项:
  --format FORMAT       输出格式: summary（默认）/ json / markdown
  --strict              将 warning 升级为 error
  --check CHECKERS      仅运行指定检查器（逗号分隔）
  --verbose             显示所有检查结果（含通过项）
```

### 4.B.2 stdin/stdout/stderr 契约

| 通道 | 用途 | 格式 |
|------|------|------|
| stdin | 不使用 | — |
| stdout | 检查报告 | summary/json/markdown（由 --format 控制） |
| stderr | 诊断信息、逐项 PASS/FAIL/WARN | `LEVEL [checker] file:line: message` |

### 4.B.3 Exit Code 语义

| 退出码 | 含义 | 触发条件 |
|--------|------|---------|
| 0 | 成功 | 所有检查通过（或仅有 warning 且未启用 --strict） |
| 1 | 验证失败 | 至少一项 FAIL（或 --strict 模式下至少一项 WARNING） |
| 2 | 使用错误 | 文件不存在、参数缺失、文件编码错误 |

### 4.B.4 POSIX 组合性

- `spec_lint.py spec.md | grep FAIL` — 筛选失败项
- `spec_lint.py spec.md --format json > report.json` — JSON 输出重定向
- stderr 不干扰管道下游

### 4.C 内部接口/函数签名

```python
def parse_document(text: str) -> Document
    # 将 Markdown 文本解析为 Document 结构
    # 返回: Document(sections=[Section(title, level, line_num, lines)])

def run_lints(doc: Document, checker_names: list[str] | None = None) -> LintReport
    # 运行所有（或指定）检查器
    # 返回: LintReport(results=[LintResult(...)])

def format_report(report: LintReport, fmt: str = "summary") -> str
    # 将 LintReport 格式化为字符串输出
```

---

## 5. 数据模型

```
Dataclass: Document
字段:
  - title: str — 文档一级标题
  - header_lines: list[str] — 文档头部（前 10 行）
  - sections: list[Section] — 二级章节列表
  - raw_lines: list[str] — 原始文本行

Dataclass: Section
字段:
  - title: str — 章节标题文本
  - level: int — 标题层级（2 = ##, 3 = ###）
  - number: str — 章节编号（"1", "2", ..., 或 ""）
  - line_num: int — 起始行号
  - lines: list[str] — 章节内容行（不含标题行）

Dataclass: LintResult
字段:
  - checker: str — 检查器名称
  - severity: Severity — pass/warning/fail
  - line_number: int — 问题行号（0 表示全局）
  - message: str — 描述信息

Dataclass: LintReport
字段:
  - results: list[LintResult]
  - file_path: str — 被检查的文件路径
  - timestamp: str — ISO 日期
```

---

## 6. 错误处理策略

| 错误类型 | 处理方式 | Exit Code | stderr 输出 |
|---------|---------|-----------|------------|
| 文件不存在 | 立即退出 | 2 | `Error: file not found: <path>` |
| 编码错误 | 立即退出 | 2 | `Error: cannot read file (encoding): <path>` |
| 空文件 | 报告 WARNING | 0 或 1 | `WARN: file is empty` |
| 无必填章节 | 报告 FAIL | 1 | `FAIL [section_presence]: missing section N` |
| 未知检查器名 | 立即退出 | 2 | `Error: unknown checker: <name>` |

---

## 8. 模式定义约束

### SectionPresenceChecker

检查器: SectionPresenceChecker
匹配模式: `^##\s+(\d+)\.\s+`
标志: 无

正例（应匹配）:
  1. `## 1. 项目概述` → 捕获组 "1"
  2. `## 3. 系统架构 [Required]` → 捕获组 "3"
  3. `## 6. 错误处理策略` → 捕获组 "6"

反例（不应匹配）:
  1. `### 1.1 目标` → 三级标题，非章节定义
  2. `# 1. 项目概述` → 一级标题
  3. `## A. 附录` → 非数字编号

已知边界:
  - 仅检查二级标题（##），不检测更深层级的子章节编号

### HeaderFormatChecker — 版本字段

检查器: HeaderFormatChecker (version)
匹配模式: `^版本:\s*v\d+\.\d+`
标志: 无

正例（应匹配）:
  1. `版本: v1.0` → 标准格式
  2. `版本: v2.1` → 多位版本号
  3. `版本:v1.0` → 冒号后无空格

反例（不应匹配）:
  1. `Version: v1.0` → 英文标签
  2. `版本: 1.0` → 缺少 v 前缀
  3. `版本: draft` → 非版本号格式

已知边界:
  - 仅检查前 10 行

### TBDMarkerChecker

检查器: TBDMarkerChecker
匹配模式: `(?:^|[^a-zA-Z])(TBD|TODO)(?:[^a-zA-Z]|$)|待定|待补充|未决定`
标志: re.IGNORECASE（仅英文部分）

> **v1.1 变更（修复 C2 漏洞）**：中文关键词不再依赖 `\b` 词界，改为直接子串匹配。英文关键词改用非字母字符边界 `[^a-zA-Z]`，避免匹配类名中的 TBD（如 `TBDMarkerChecker`）。

正例（应匹配）:
  1. `数据库选型: TBD` → 英文标记，TBD 前后为非字母字符
  2. `认证方式待定` → 中文标记，直接子串匹配
  3. `TODO: 补充错误码` → TODO 行首

反例（不应匹配）:
  1. 代码块内的 `TBDMarkerChecker` → 代码块跳过
  2. `completed` → 无关词汇
  3. `table_definition` → 不含目标子串

已知边界:
  - 代码块（```...```）内的内容不检查
  - 中文关键词使用子串匹配，`"未决定论"` 中的 `"未决定"` 会误报 — 可接受（SDD 中极少出现哲学术语）

### ExitCodeTableChecker

检查器: ExitCodeTableChecker
匹配模式: `\|\s*(\d+)\s*\|`
标志: 无

正例（应匹配）:
  1. `| 0 | 成功 |` → 提取 code 0
  2. `| 1 | 验证失败 |` → 提取 code 1
  3. `| 2 | 使用错误 |` → 提取 code 2

反例（不应匹配）:
  1. `exit code 为 0` → 非表格格式
  2. `| code | 含义 |` → 表头（非数字）
  3. `| --- | --- |` → 分隔行

已知边界:
  - 仅在检测到 4.B 相关标题时激活
