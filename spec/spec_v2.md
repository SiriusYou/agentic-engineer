# check_workflow_consistency — 软件设计文档 (SDD)
版本: v2.0
状态: Draft
最后更新: 2026-03-02

---

## 1. 项目概述

### 1.1 目标

自动扫描 agentic-engineer 框架的文档集，检测文件引用断裂、数值不一致、命名偏差和规范违反，输出结构化检查报告。

### 1.2 核心用户场景

1. 作为框架维护者，我希望在每次修改文档后运行一条命令，从而立即发现是否引入了引用断裂或数值不一致
2. 作为新贡献者，我希望 clone 项目后运行检查工具，从而验证本地文档状态健康
3. 作为 CI 系统，我希望在 pre-commit 或 push 时自动运行检查，从而阻止不一致的文档被合并
4. 作为框架维护者，我希望看到明确的通过/失败/警告分类报告，从而快速定位需要修复的文件和行号

### 1.3 系统边界

**不在本次实现范围内：**
- Markdown 语法校验（已有 markdownlint）
- 拼写检查
- SDD 内容质量评估（压力测试的职责）
- 自动修复功能（只报告，不改写文件）
- Git 历史分析（只检查当前工作目录快照）
- 跨项目检查（只检查 agentic-engineer/ 内的文件）

---

## 2. 技术栈

| 层次 | 技术选型 | 版本 | 选择理由 |
|------|---------|------|---------|
| 语言 | Python | 3.8+ | 与 scorecard_parser.py 一致，框架已有 Python 工具链 |
| 依赖 | 仅标准库 | — | pathlib, re, json, argparse, sys, enum, dataclasses；无第三方依赖，降低维护成本 |
| 测试 | unittest | 标准库 | 与 test_scorecard_parser.py 一致 |
| 输出 | Markdown to stdout | — | 与 scorecard_parser 的 I/O 契约一致 |

**环境变量清单：** 无。工具通过 CLI 参数接受输入。

---

## 3. 系统架构

### 3.1 组件总览

```
CLI 入口 (main)
    │
    ├── PathResolver         解析项目根目录
    │
    ├── CheckRunner          编排所有检查器，汇总结果
    │   │
    │   ├── FileRefChecker         检查 1: 文件路径引用
    │   ├── ConvergenceChecker     检查 2: 收敛阈值一致性
    │   ├── StepNamingChecker      检查 3: 步骤编号/名称
    │   ├── SpecNamingChecker      检查 4: spec/ 文件命名
    │   ├── TrackStatusChecker     检查 5: tracks.md 状态语义
    │   └── QuestionIdChecker      检查 6: 压测题号完整性
    │
    └── ReportFormatter      格式化输出 Markdown 报告
```

### 3.2 组件详情

#### PathResolver
- **职责**：确定项目根目录（agentic-engineer/），验证目录结构存在
- **输入**：可选的 `--root` CLI 参数，默认为自动检测
- **输出**：`Path` 对象指向项目根目录
- **依赖**：无
- **不负责**：不验证每个子目录的完整性

**自动检测算法：**
1. 从当前工作目录开始，向上逐级搜索
2. 检测条件：目录中同时包含 `plan/` 和 `skills/` 子目录
3. 搜索上限：最多向上 5 级（防止遍历到根目录）
4. 多个匹配时：使用最近的（最深的）匹配
5. 无匹配时：打印错误到 stderr，exit code 2

#### CheckRunner
- **职责**：依次运行所有注册的检查器，收集检查结果
- **输入**：项目根目录 `Path`，可选的检查器过滤列表
- **输出**：`CheckReport`（所有检查结果的聚合）
- **依赖**：所有 Checker 组件
- **不负责**：不决定输出格式

#### FileRefChecker
- **职责**：扫描 Markdown 文件中的相对路径引用，验证引用目标存在
- **输入**：项目根目录，待扫描的文件列表
- **输出**：`list[CheckResult]`
- **依赖**：PathResolver
- **不负责**：不检查 URL 链接（http/https），不检查模板路径

**扫描范围：**
- `README.md`
- `plan/*.md`
- `skills/*.md`
- `conductor/*.md`
- `spec/README.md`

**路径提取规则：**

1. **Markdown 链接路径**：匹配 `[text](path/to/file)` 中的路径
2. **行内代码引用**：匹配独立的 `` `path/to/file.ext` `` 格式（必须包含 `/` 和文件扩展名）
3. **排除规则（不检查以下路径）：**
   - HTTP/HTTPS URL（以 `http://` 或 `https://` 开头）
   - 锚点链接（以 `#` 开头）
   - 含方括号占位符的模板路径（包含 `[` 和 `]`）
   - 位于代码块（` ``` ` 围栏）内部的路径（v2 修订：代码块内路径全部跳过）
   - 命令行示例中的路径（行以 `$`、`>`、`python`、`cat`、`bash` 等命令开头）

**v2 修订说明（修复 C1）：**
原 v1 设计试图从代码块中的目录树提取路径，但无法区分"项目结构描述"和"预期输出描述"。v2 决策：**代码块内所有路径一律跳过**，只检查正文中的 Markdown 链接和行内代码引用。理由：
- 代码块中的目录树是文档性质的，不是可执行引用
- README.md 的正文部分已包含所有关键路径的 Markdown 链接引用
- 消除误报优先于提高覆盖率

#### ConvergenceChecker
- **职责**：验证收敛阈值在所有出现位置数值一致
- **输入**：项目根目录
- **输出**：`list[CheckResult]`
- **依赖**：PathResolver
- **不负责**：不判断阈值是否合理

**检查位置和提取方式：**

| 文件 | 提取方法 | 预期提取结果 |
|------|---------|-------------|
| `tools/scorecard_parser.py` | 正则 `MEDIUM_CONVERGENCE_THRESHOLD\s*=\s*(\d+)` | 基准值（如 `3`） |
| `plan/quick_reference.md` | 正则 `(\d+)\s*高.*?(\d+)\s*中` | 高=0, 中=基准值 |
| `skills/planning-workflow.md` | 正则 `(\d+)\s*高严重度.*?(\d+)\s*中严重度` | 高=0, 中=基准值 |
| `skills/stress-test-prompts.md` | 正则 `(\d+)\s*高.*?(\d+)\s*中` | 高=0, 中=基准值 |

**v2 修订说明（修复 C2）：**
- 每个文件给出具体正则表达式，不使用模糊匹配
- 仅匹配阿拉伯数字，不处理文字数字（"零"、"三"）
- 匹配失败时：记录 WARNING（"无法从 {file}:{line} 提取阈值"），不算 FAIL
- 同一行出现多个数字时：按位置分配（第一个=高阈值，第二个=中阈值）

**无数据场景：** 文件不存在 → 记录 FAIL（"收敛阈值真相来源文件缺失"）

#### StepNamingChecker
- **职责**：验证 Step 1-5 和 Phase 0 的编号和名称在文档中一致
- **输入**：项目根目录
- **输出**：`list[CheckResult]`
- **依赖**：PathResolver
- **不负责**：不检查步骤内容是否正确

**规范名称映射（基准，硬编码在工具中）：**

| 编号 | 规范名称 | 允许的别名 |
|------|---------|-----------|
| Step 1 | 灵感捕获 | 灵感整理 |
| Step 2 | SDD 生成 | SDD生成, AI 结构化 |
| Step 3 | 压力测试 | 对抗性压测, 压测 |
| Step 4 | 反馈修正 | 迭代修正, 修订 |
| Step 5 | 锁定执行 | 执行, 移交执行 |
| Phase 0 | 复盘 | 项目复盘, postmortem |

**检查逻辑：**
- 在文档中搜索 `Step\s+[1-5]` 模式
- 提取步骤编号后到行尾或下一个标点（`，。：、│|`）之间的文本作为步骤名称
- 去除前后空白后与规范名称和别名列表比对
- 不匹配任何已知名称 → FAIL
- 位于代码块内的匹配 → 跳过

**无数据场景：** 文件不存在 → WARNING（非关键检查）

#### SpecNamingChecker
- **职责**：验证 `spec/` 目录下的文件命名符合接口契约
- **输入**：项目根目录
- **输出**：`list[CheckResult]`
- **依赖**：PathResolver
- **不负责**：不检查文件内容

**合法文件名模式（正则）：**
```
raw_requirements\.md
spec_v\d+\.md
scorecard_v\d+\.json
stress_test_v\d+\.md
spec_final\.md
spec_final_v\d+\.md
scorecard_final_v\d+\.json
stress_test_final_v\d+\.md
postmortem_v\d+\.md
README\.md
```

不匹配以上任何模式的文件 → 报告为 WARNING（不阻塞退出码）。

**无数据场景：** spec/ 目录不存在 → 单条 WARNING（"spec/ 目录不存在"），返回。spec/ 为空 → 单条 PASS（"spec/ 目录为空，无文件需检查"），返回。

#### TrackStatusChecker
- **职责**：验证 `conductor/tracks.md` 中每条 track 的状态语义一致
- **输入**：项目根目录
- **输出**：`list[CheckResult]`
- **依赖**：PathResolver
- **不负责**：不验证 track 内容质量

**v2 修订说明（修复 C3）：**

**表格解析策略：**
1. 定位表格头行：匹配包含 `|` 分隔符的行，查找包含 `Status` 文本的列
2. 按列标题定位（不按列位置），找到 `Status` 所在的列索引
3. 对每个数据行，按 `|` 分割后取对应列索引的值
4. 值清理：strip() 去除前后空格
5. 表格不存在 → FAIL（"tracks.md 中未找到 track 注册表"）
6. 表格存在但无数据行 → PASS（"无已注册 track"）

**状态值验证：**
- 合法状态：`pending`、`active`、`completed`（大小写不敏感）
- 非法状态值 → FAIL

**表格-详情一致性：**
- 对每条 track，在详情部分搜索 `**状态：**` 或 `**状态:**` 后的文本
- 提取状态值（取到行尾或下一个标点），与表格中的状态比较
- 不一致 → FAIL（报告两个值）
- 详情中找不到状态行 → WARNING

**无数据场景：** tracks.md 不存在 → FAIL（"conductor/tracks.md 文件缺失"）

#### QuestionIdChecker
- **职责**：验证 `skills/stress-test-prompts.md` 中题号序列完整
- **输入**：项目根目录
- **输出**：`list[CheckResult]`
- **依赖**：PathResolver
- **不负责**：不验证题目内容质量

**检查逻辑：**
1. 提取所有 `**[ID]. ` 格式的题号（正则：`\*\*([A-Z]\d+)\.\s`）
2. 验证序列完整：U1-U10、W1-W5、D1-D5
3. 缺失题号 → FAIL，多余题号 → WARNING
4. 验证题号映射表行数与题目数一致（20 条）

**无数据场景：** 文件不存在 → WARNING（"stress-test-prompts.md 缺失，跳过题号检查"）

#### ReportFormatter
- **职责**：将 CheckReport 格式化为 Markdown 输出
- **输入**：`CheckReport`
- **输出**：Markdown 字符串
- **依赖**：无
- **不负责**：不决定退出码

**输出格式：**
```markdown
## 文档一致性检查报告
日期: YYYY-MM-DD

### 汇总
- 检查项: X 个
- 通过: X 个
- 失败: X 个
- 警告: X 个

### 失败项
| 检查器 | 文件 | 行号 | 描述 |
|--------|------|------|------|
| ... | ... | ... | ... |

### 警告项
| 检查器 | 文件 | 描述 |
|--------|------|------|
| ... | ... | ... |
```

---

## 4. 接口定义

### 4.1 CLI 接口（外部接口）

```
python3 tools/check_workflow_consistency.py [OPTIONS]

位置参数: 无

可选参数:
  --root PATH        项目根目录路径（默认: 自动检测）
  --check NAMES      只运行指定检查器，逗号分隔
                     可选值: file_ref, convergence, step_naming,
                             spec_naming, track_status, question_id
  --format FORMAT    输出格式（默认: markdown）
                     可选值: markdown, summary
  --verbose          显示所有检查项（包括通过的）
  --help             显示帮助信息

输出:
  stdout  检查报告（Markdown 格式）
  stderr  警告信息和错误信息

退出码:
  0  所有检查通过（可能有 WARNING）
  1  有 FAIL 项
  2  文件读取错误（项目根目录不存在、关键文件缺失等）
```

### 4.2 内部接口

```python
# --- 数据类型 ---

class Severity(Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"

@dataclass
class CheckResult:
    checker: str        # 检查器名称
    severity: Severity  # 结果严重度
    file_path: str      # 相关文件路径（相对于项目根目录）
    line_number: int    # 行号（0 表示无特定行）
    message: str        # 人类可读描述，FAIL 结果必须包含 expected/actual 值

# v2 修订（修复 U10）：message 字段格式约定
# - PASS:    "{检查描述} 通过"
# - WARNING: "{检查描述}: {具体情况}"
# - FAIL:    "{检查描述}: expected {期望值}, found {实际值} in {位置}"
# 示例: "收敛阈值一致性: expected 3, found 5 in plan/quick_reference.md:16"

@dataclass
class CheckReport:
    results: list[CheckResult]
    timestamp: str      # ISO 8601 日期

# --- 检查器接口 ---

class BaseChecker:
    name: str           # 检查器名称（用于 --check 过滤和报告显示）

    def run(self, root: Path) -> list[CheckResult]:
        """执行检查，返回结果列表。

        无数据场景规则（v2 修订，修复 U8）：
        - 关键文件缺失（该检查器的核心依赖）→ 返回单条 FAIL
        - 非关键文件缺失 → 返回单条 WARNING
        - 目标数据为空（如 spec/ 无文件）→ 返回单条 PASS（说明无需检查）
        - 不应返回空列表（每个检查器至少返回一条结果）
        """
        ...

# --- 核心函数 ---

def resolve_root(cli_root: str | None) -> Path:
    """解析项目根目录。

    算法：
    1. 如果 cli_root 提供，验证路径存在且包含 plan/ 和 skills/
    2. 否则从 cwd 向上搜索（最多 5 级），找包含 plan/ + skills/ 的目录
    3. 找不到时打印 stderr 错误，sys.exit(2)
    """

def run_checks(root: Path, checkers: list[BaseChecker]) -> CheckReport:
    """运行所有检查器，汇总结果。"""

def format_report(report: CheckReport, fmt: str, verbose: bool) -> str:
    """格式化检查报告。

    fmt="markdown": 完整 Markdown 表格报告
    fmt="summary": 仅一行汇总 "X passed, X failed, X warnings"
    """
```

---

## 5. 数据模型

本工具无持久化存储。运行时数据结构如下：

### CheckResult
| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| checker | str | 非空 | 产生此结果的检查器名称 |
| severity | Severity | enum | PASS / WARNING / FAIL |
| file_path | str | 相对路径 | 检查涉及的文件 |
| line_number | int | ≥ 0 | 具体行号，0 表示文件级别 |
| message | str | 非空，FAIL 必须含 expected/actual | 人类可读的检查结果描述 |

### CheckReport
| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| results | list[CheckResult] | 非空列表 | 所有检查结果（每个检查器至少返回一条） |
| timestamp | str | ISO 8601 | 报告生成时间 |

---

## 6. 错误处理策略

| 错误类型 | 处理方式 | 用户提示（stderr） |
|---------|---------|-------------------|
| 项目根目录不存在 | 立即退出，exit code 2 | `Error: project root not found: {path}` |
| 关键文件缺失（如 scorecard_parser.py） | 记录为 FAIL 结果，继续运行其他检查 | `Warning: {path} not found, recording as FAIL` |
| 非关键文件缺失（如 spec/ 为空） | 记录为 WARNING 或 PASS，继续运行 | `Warning: {path} not found, skipping {checker}` |
| 正则匹配失败（文件格式异常） | 记录为 WARNING，跳过该检查项 | `Warning: unexpected format in {file}:{line}, skipping` |
| 编码错误（非 UTF-8 文件） | 记录为 WARNING，跳过该文件 | `Warning: cannot read {file}: {error}` |

**核心原则：** 单个文件或检查的失败不应阻止其他检查运行。工具应尽可能完成所有可执行的检查。每个检查器至少返回一条结果（不允许静默跳过）。

---

## 附录 A: 与 scorecard_parser 的接口对比

| 维度 | scorecard_parser | check_workflow_consistency |
|------|-----------------|---------------------------|
| 输入 | JSON 文件路径 | 项目根目录路径 |
| stdout | Markdown 报告 | Markdown 报告 |
| stderr | 警告信息 | 警告 + 错误信息 |
| exit 0 | 解析成功 | 所有检查通过 |
| exit 1 | 验证错误 | 有 FAIL 项 |
| exit 2 | 文件错误 | 文件读取错误 |
| 第三方依赖 | 无 | 无 |

---

## 附录 B: v1 → v2 修订记录

| 漏洞 ID | 严重度 | 修订内容 |
|---------|--------|---------|
| C1 | HIGH | FileRefChecker: 代码块内路径全部跳过，只检查正文中的 Markdown 链接和行内代码引用 |
| U8 | MEDIUM | 所有检查器: 定义无数据场景返回值，禁止返回空列表 |
| U10 | MEDIUM | CheckResult.message: FAIL 结果必须包含 expected/actual 值 |
| C2 | MEDIUM | ConvergenceChecker: 每个文件给出具体正则表达式 |
| C3 | MEDIUM | TrackStatusChecker: 按列标题匹配，定义具体解析和清理逻辑 |
