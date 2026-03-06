# Tracks Registry

| Status | Track ID | Title | Created | Updated |
| ------ | -------- | ----- | ------- | ------- |
| completed | TRACK-001 | 首次真实项目闭环验证 | 2026-03-02 | 2026-03-02 |
| completed | TRACK-002 | 工程护栏 + 工具链增强 | 2026-03-02 | 2026-03-03 |
| completed | TRACK-003 | 方法论迭代 + 二次闭环 | 2026-03-03 | 2026-03-04 |
| completed | TRACK-004 | spec-lint 工程化收口 | 2026-03-04 | 2026-03-04 |
| completed | TRACK-005 | 泛化验证 — 全栈项目闭环 (gpt-researcher) | 2026-03-04 | 2026-03-05 |
| completed | TRACK-006 | 模板迭代 — TRACK-005 postmortem 行动项落实 | 2026-03-05 | 2026-03-05 |
| completed | TRACK-007 | 外部项目 Step 5 编码验证 (gpt-researcher) | 2026-03-05 | 2026-03-05 |
| completed | TRACK-008 | 方法论产品化 — spec-driven-dev Claude Code Skill | 2026-03-05 | 2026-03-05 |

<!-- Tracks registered by /conductor:new-track -->

---

## TRACK-001: 首次真实项目闭环验证

**目标：** 用本方法论框架完成一个真实项目的 Step 1-5 全流程，验证流程可执行性。

**产出目录：** `spec/`

**预期产物：**
- `spec/raw_requirements.md` — Step 1 灵感捕获
- `spec/spec_v1.md` — Step 2 SDD
- `spec/scorecard_v1.json` — Step 3 评分卡
- `spec/stress_test_v1.md` — Step 3 漏洞记录表
- `spec/spec_final.md` — 收敛锁定版本
- `spec/postmortem_v1.md` — Phase 0 复盘

**验收标准：**
- 完整链路一次成功
- 记录每步耗时和迭代轮次
- 复盘报告包含可执行的改进建议

**状态：** completed — check_workflow_consistency.py 全流程闭环完成

---

## TRACK-002: 工程护栏 + 工具链增强

**目标：** 为方法论工具链添加工程护栏，提高开发效率和质量保障。

**交付物：**
- GitHub Actions CI workflow（Python 3.8 + 3.12 矩阵）
- `scripts/pre-push-check.sh` — 推送前一致性检查
- `scorecard_parser.py --format json --output` — 结构化输出支持
- 独立仓库拆分（从 AgentLab monorepo → `SiriusYou/agentic-engineer`）

**验收标准：**
- CI 绿色（131 测试通过）
- 一致性检查 55/55 通过
- pre-push hook 可阻断不一致推送

**状态：** completed — CI + pre-push hook + scorecard 增强 + 独立仓库拆分

---

## TRACK-003: 方法论迭代 + 二次闭环

**目标：** 用 TRACK-001 复盘数据改进模板，然后用新模板做第二次闭环验证改进效果。

**产出目录：** `spec/spec-lint/`

**预期产物：**
- 模板升级：CLI 专用压测子集、SDD CLI 变体、正则必填、tech-stack 决策标准
- spec/spec-lint/ 下完整产物链：raw_requirements → spec_v1 → spec_final → scorecard → stress_test → postmortem（含与 TRACK-001 对比表）

**验收标准：**
- 模板升级后一致性检查保持 0 failed
- 完整产物链落盘 `spec/spec-lint/`
- Postmortem 含量化对比（收敛轮次、有效题比例 vs TRACK-001）

**状态：** completed — spec-lint 工具实现完成，方法论二次闭环验证通过

---

## TRACK-004: spec-lint 工程化收口

**目标：** 将 spec-lint 从"已实现"升级为"CI 门控 + 团队可复用"状态。

**交付物：**
- Pre-push hook 增加 spec-lint 烟雾测试（两个 spec 文件）
- CI 独立 dogfood 步骤（含 JSON 输出验证）
- README 文档化 spec-lint 用法和排障指南
- SDD 模板 §8 标准化"已知误报/漏报边界"要求
- Postmortem 行动项 #2 闭合

**验收标准：**
- pre-push hook 通过（含 spec-lint 烟雾测试）
- CI 有独立 dogfood job（与 pytest 分离）
- README 包含 spec-lint 文档
- postmortem_v1.md 行动项 #2 标记 ✅
- 工作树干净，所有测试绿色

**状态：** completed — pre-push + CI dogfood + README + SDD 模板标准化 + postmortem 闭合

---

## TRACK-005: 泛化验证 — 全栈项目闭环 (gpt-researcher)

**目标：** 在完全不同域的全栈项目上运行完整 SDD 5-step cycle，验证方法论泛化能力。

**Pilot 项目：** gpt-researcher (`~/dev/gpt-researcher`) — Python + FastAPI + Next.js 全栈 AI 研究 agent 应用
- 多 agent 系统 (LangGraph)、WebSocket 实时通信、20+ 搜索引擎集成
- 与 agentic-engineer 自身 CLI 工具完全不同域，验证泛化能力

**Feature (MVP)：** 输出与 prompt 对齐评分 + 不满足时自动重试
- 评估研究输出是否匹配输入 prompt 要求，不满足阈值时自动迭代改进
- 后续再扩展 hooks/skills/脚本等完整机制

**产出目录：** `spec/gpt-researcher/`

**预期产物：**
- `spec/gpt-researcher/` 完整产物链（raw_requirements → spec → scorecard → stress_test → spec_final → postmortem）
- 量化指标：收敛轮次、有效问题发现率、SDD 耗时 vs 编码耗时
- 与 TRACK-001/003 的对比表
- 模板变更提案（不直接改模板）

**验收标准：**
- Quality gates all green on pilot spec
- 完整 5-step cycle completed with postmortem
- 清晰的量化对比（与前几轮 track 对比）

**失败信号：**
- 模板需要 >50% 重写以适配全栈上下文
- SDD 耗时超过编码耗时
- 步骤被持续跳过

**状态：** completed — 5-step cycle 全流程闭环，方法论泛化验证通过

---

## TRACK-006: 模板迭代 — TRACK-005 postmortem 行动项落实

**目标：** 落实 TRACK-005 postmortem 的 5 个行动项，提升方法论模板和工具的易用性。

**交付物：**
- template_01 增加"代码库探索"输入模式
- template_02 增加"继承目标项目栈"选项 + spec_lint 速查链接
- template_03 增加"功能级 MVP"压测子集指引 + n/a severity
- scorecard_parser 增加 n/a severity 支持
- sdd-template.md 追加 spec_lint 格式速查表
- pre-push + CI 补齐 gpt-researcher spec-lint smoke

**验收标准：**
- 192 tests passing（含 n/a 新增测试）
- 一致性检查 0 failed
- pre-push hook 通过
- postmortem 行动项全部勾选

**状态：** completed — 5 个行动项全部落实，192 tests + 76 consistency checks 全绿

---

## TRACK-007: 外部项目 Step 5 编码验证 (gpt-researcher)

**目标：** 在外部仓按 `spec/gpt-researcher/spec_final.md` 完成真实实现，验证 spec→code 转化质量。

**背景：** 规划链路（Step 1-4）已在 TRACK-001/003/005 中充分验证，但 Step 5 编码阶段此前仅在本仓内执行（check_workflow_consistency、spec_lint）。在外部项目上的 spec→code 转化效果是方法论核心价值的最大未验证缺口。

**Pilot 项目：** gpt-researcher (`~/dev/gpt-researcher`) — 复用 TRACK-005 产出的 spec_final.md

**范围：**
- 实现 spec 定义的 Alignment Scoring + Auto-Retry（后端逻辑 + 测试）
- 不做前端 UI（MVP scope）
- 不在 TRACK-007 引入新自动化工具

**交付物：**
1. 外部仓代码提交与测试结果
2. `spec/gpt-researcher/behavior_inventory.md` — 冻结的行为清单（偏差率分母）
3. postmortem_v2.md（执行阶段复盘，含量化指标，落盘 spec/gpt-researcher/）
4. `conductor/tracks.md` 闭合 TRACK-007

**验收标准：**
1. 外部仓目标功能可运行并通过测试
2. 所有 spec 偏差有显式记录（偏差原因 + 处理方式）
3. 量化数据：编码耗时、歧义暂停次数、spec 偏差率（附偏差数，基于 behavior inventory）
4. agentic-engineer 现有门禁保持全绿
5. 可审计证据：外部仓 commit hash、测试命令及结果快照记录在 postmortem 中

**失败信号（两级，基于 TRACK-005 数据设计）：**

- 编码耗时 / SDD 耗时 — Warning: > 5x (~5h), Fail: > 8x (~8h)
- 歧义暂停次数 — Warning: > 3 次, Fail: > 5 次
- spec 偏差率 — Warning: > 20%, Fail: > 30%

SDD 耗时基准 ~60min，编码预估 4-8h，warning 线在预估中位，fail 线在预估上限。

**测量协议：**
- **编码耗时**：从开始读 spec_final 到功能通过测试的壁钟时间，不含环境搭建
- **歧义暂停**：编码中因 spec 不清/矛盾/缺失而停下做设计决策的次数。每次记录触发位置（spec 章节号）、歧义描述、决策结果
- **spec 偏差**：最终实现与 spec 不一致的接口/行为数 / behavior inventory 总数。每次偏差记录偏差内容、原因分类（spec 过时 / spec 不可行 / 发现更优方案）
- **behavior inventory**：冻结清单见 `spec/gpt-researcher/behavior_inventory.md`

**假设：**
- 继续以 gpt-researcher 为验证对象
- 保持当前 pre-push 不引入 pytest（CI 保障）
- 成功判定以"外部项目可运行 + 指标闭环 + postmortem 可复现"为准
- 若触发选项 D（紧急新项目），仍需在本仓 `spec/[项目名]/postmortem_vN.md` 记录执行证据

**状态：** completed — 39/39 behavior items 实现，28 tests passing，spec 偏差率 5.1%，编码耗时 0.75x SDD

---

## TRACK-008: 方法论产品化 — spec-driven-dev Claude Code Skill

**目标：** 将 7 轮验证的 SDD 方法论打包为 Claude Code skill，让任何用户可安装使用。

**交付物：**
- Skill 核心入口 SKILL.md（英文，<500 lines）
- templates/ × 5 — 英文化 prompt 模板（Step 0-4）
- references/ × 5 — 英文化参考文档（workflow, SDD template, stress test, execution, quick ref）
- scripts/ × 3 — 独立工具（scorecard_parser, spec_lint, check_consistency），纯 stdlib
- README.md — 新增 skill 安装章节

**验收标准：**
1. Skill 发现：新 session 输入 "spec driven dev" → skill 被匹配
2. 脚本可执行：`python3 scripts/scorecard_parser.py --help` 正常输出
3. 脚本可执行：`python3 scripts/spec_lint.py --help` 正常输出
4. 主仓门禁：pre-push + CI 保持全绿

**状态：** completed — 14 files delivered (1 SKILL.md + 5 templates + 5 references + 3 scripts), pre-push gate 86/0/0, SKILL.md 280 lines

---

## Backlog

- Behavior inventory template standardization (TRACK-007 postmortem #2, Medium priority)
- "Recommended implementation path" SDD template hint (TRACK-007 postmortem #1, Low)
- README English translation for consistency with English skill (Low)
