# Agentic Engineer

[![CI](https://github.com/SiriusYou/AgentLab/actions/workflows/agentic-engineer-test.yml/badge.svg)](https://github.com/SiriusYou/AgentLab/actions/workflows/agentic-engineer-test.yml)

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
│   └── test_scorecard_parser.py # 单元测试（63 个）
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

运行测试：
```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tools/ -v
```

---

## Pre-push Hook

`scripts/pre-push-check.sh` runs `check_workflow_consistency.py` before every push that touches `agentic-engineer/` files. It's called by the monorepo root pre-push hook.

### Installation

The monorepo root hook (`/Users/youjia/dev/.git/hooks/pre-push`) is a symlink. To verify it's set up:

```bash
# Check symlink target
readlink .git/hooks/pre-push

# The target script should contain the agentic-engineer block:
grep -q "agentic-engineer" "$(readlink .git/hooks/pre-push)" && echo "Hook configured" || echo "Hook needs update"
```

If the hook doesn't include the agentic-engineer block, the target script needs the following inserted **before** the `.py`-only early exit:

```bash
# Detect agentic-engineer changes and run consistency check
HAS_AGENTIC_ENGINEER_CHANGES=$(echo "$CHANGED_ALL_FILES" | grep -c "^agentic-engineer/" || true)
if [ "$HAS_AGENTIC_ENGINEER_CHANGES" -gt 0 ]; then
    if ! "$PROJECT_ROOT/agentic-engineer/scripts/pre-push-check.sh"; then
        exit 1
    fi
fi
```

---

## 补充流程

- **变更请求（CR）：** `spec_final.md` 锁定后需修改时的流程，详见 `plan/quick_reference.md`
- **项目复盘（Phase 0）：** 项目完成后使用 `plan/template_00_postmortem.md` 记录耗时和改进数据
