# Tracks Registry

| Status | Track ID | Title | Created | Updated |
| ------ | -------- | ----- | ------- | ------- |
| completed | TRACK-001 | 首次真实项目闭环验证 | 2026-03-02 | 2026-03-02 |
| completed | TRACK-002 | 工程护栏 + 工具链增强 | 2026-03-02 | 2026-03-03 |
| active | TRACK-003 | 方法论迭代 + 二次闭环 | 2026-03-03 | 2026-03-03 |

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

**状态：** active — 方法论迭代 + 二次闭环验证进行中
