# Agentic Engineer

[![CI](https://github.com/SiriusYou/agentic-engineer/actions/workflows/test.yml/badge.svg)](https://github.com/SiriusYou/agentic-engineer/actions/workflows/test.yml)

Spec-Driven Development 方法论框架：通过结构化的规划→压测→执行流程，将模糊想法转化为可靠的软件实现。

---

## 核心理念

传统开发中 60% 的返工来自规划不足。本框架将精力分配为 **60% 规划 / 40% 执行**，通过对抗性压力测试在编码前发现设计漏洞。

---

## 5 步流程

灵感捕获 → SDD 生成 → 压力测试 → 反馈修正（循环）→ 锁定执行

**快速参考（含流程图、文件命名、收敛阈值）：** `plan/quick_reference.md`
**阶段详细说明：** `skills/planning-workflow.md`

---

## 项目结构

```
agentic-engineer/
├── plan/                        # 模板和参考文档
│   ├── quick_reference.md       # 快速参考卡（每次启动看这一页）
│   ├── template_01_inspiration.md   # Step 1 灵感捕获模板
│   ├── template_02_sdd_gen.md       # Step 2 SDD 生成 Prompt
│   ├── template_03_stress_test.md   # Step 3 压力测试 Prompt
│   ├── template_04_iteration.md     # Step 4 反馈修正 Prompt
│   └── template_00_postmortem.md    # Phase 0 项目复盘模板
├── skills/                      # Claude Code 执行技能
│   ├── SKILL.md                 # Spec-driven 执行 Skill（Step 5）
│   ├── planning-workflow.md     # 规划阶段流程文档（Step 1-4）
│   ├── sdd-template.md          # SDD 文档模板
│   └── stress-test-prompts.md   # 压力测试 Prompt 库
├── tools/                       # CLI 工具
│   ├── scorecard_parser.py      # Scorecard JSON → 漏洞报告
│   ├── test_scorecard_parser.py # scorecard 测试（78 个）
│   ├── check_workflow_consistency.py  # 文档一致性检查器
│   └── test_check_workflow_consistency.py  # 一致性检查器测试（53 个）
├── scripts/                     # 自动化脚本
│   └── pre-push-check.sh       # pre-push hook 入口
└── conductor/                   # 项目管理
    ├── tracks.md                # 活跃开发轨道
    └── tech-stack.md            # 技术栈约束
```

---

## 快速开始

### 1. 首次使用：阅读快速参考

```
cat plan/quick_reference.md
```

这一页包含完整的 5 步流程、文件命名规范和常见卡点处理。

### 2. 开始新项目

按 Step 1-4 走规划流程，产出 `spec_final.md`：

1. 用 `plan/template_01_inspiration.md` 引导灵感捕获
2. 用 `plan/template_02_sdd_gen.md` 生成 SDD
3. 用 `plan/template_03_stress_test.md` 执行压力测试
4. 如有漏洞，用 `plan/template_04_iteration.md` 迭代修正
5. 收敛后锁定为 `spec_final.md`

### 3. 执行

将 `spec_final.md` 交给 Claude Code：

```
请按照 spec-driven-dev 执行规范，实现 spec/spec_final.md 中定义的系统。
原子化提交，严格对应 Spec 章节，发现歧义立即停下来报告。
```

---

## 工具

### scorecard_parser — 压力测试评分解析器

将 Step 3 产出的 JSON scorecard 转换为可读的漏洞报告。

```bash
# Markdown 输出（默认）
python3 tools/scorecard_parser.py spec/scorecard_v1.json

# JSON 结构化输出
python3 tools/scorecard_parser.py spec/scorecard_v1.json --format json

# 写入文件
python3 tools/scorecard_parser.py spec/scorecard_v1.json --format json --output report.json
```

输出包括：通过/未通过统计、严重度分布、收敛判断、具体漏洞详情。

### spec_lint — SDD 规范检查器

验证 SDD 文档结构完整性，包括：章节存在性、TBD 标记检测、Markdown 格式、模式定义约束等。

```bash
# 检查单个 spec 文件
python3 tools/spec_lint.py spec/spec_final.md

# JSON 结构化输出
python3 tools/spec_lint.py spec/spec_final.md --format json

# 仅运行指定检查器
python3 tools/spec_lint.py spec/spec_final.md --check section_presence,tbd_marker
```

常见问题排查：
- **TBD 误报**：行内代码中的 `TBD` 不会触发告警（已排除 backtick 包裹的内容）
- **章节缺失**：确认使用 `## N. 标题` 格式，编号与标题之间需有 `. `
- **模式定义缺失**：如果工具不含正则/模式匹配，该检查项可忽略（info 级别）

### check_workflow_consistency — 文档一致性检查器

验证 conductor/tracks.md、README 和其他文档之间的交叉引用一致性。

```bash
python3 tools/check_workflow_consistency.py --root . --format summary
```

运行测试：
```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tools/ -v
```

---

## Pre-push Hook

`scripts/pre-push-check.sh` runs consistency checks and spec-lint smoke tests before every push.

### Installation

```bash
# Option 1: Symlink (recommended)
ln -sf ../../scripts/pre-push-check.sh .git/hooks/pre-push

# Option 2: Direct call in existing hook
# Add this line to your .git/hooks/pre-push:
./scripts/pre-push-check.sh || exit 1
```

### Verify

```bash
bash scripts/pre-push-check.sh
# Should output: N passed, 0 failed, 0 warnings
```

---

## 补充流程

- **变更请求（CR）：** `spec_final.md` 锁定后需修改时的流程，详见 `plan/quick_reference.md`
- **项目复盘（Phase 0）：** 项目完成后使用 `plan/template_00_postmortem.md` 记录耗时和改进数据
