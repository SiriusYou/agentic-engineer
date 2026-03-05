# Tracks Registry

| Status | Track ID | Title | Created | Updated |
| ------ | -------- | ----- | ------- | ------- |
| completed | TRACK-001 | 首次真实项目闭环验证 | 2026-03-02 | 2026-03-02 |
| completed | TRACK-002 | 工程护栏 + 工具链增强 | 2026-03-02 | 2026-03-03 |
| completed | TRACK-003 | 方法论迭代 + 二次闭环 | 2026-03-03 | 2026-03-04 |
| completed | TRACK-004 | spec-lint 工程化收口 | 2026-03-04 | 2026-03-04 |
| active | TRACK-005 | 泛化验证 — 全栈项目闭环 (gpt-researcher) | 2026-03-04 | 2026-03-04 |

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

**状态：** active
