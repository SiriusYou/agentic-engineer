# Tracks Registry

| Status | Track ID | Title | Created | Updated |
| ------ | -------- | ----- | ------- | ------- |
| completed | TRACK-001 | 首次真实项目闭环验证 | 2026-03-02 | 2026-03-02 |

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
