# TRACK-001 Postmortem — check_workflow_consistency.py

---

## 复盘数据表

### 基本信息
| 字段 | 值 |
|------|---|
| 项目名 | check_workflow_consistency.py |
| 完成日期 | 2026-03-02 |
| Spec 最终版本 | v2 |
| 总耗时（壁钟时间） | ~80 分钟（单次会话内连续执行） |

### 各阶段耗时
| 阶段 | 耗时 | 迭代次数 | 摩擦点 |
|------|------|---------|--------|
| Step 0 提交未跟踪文件 | ~2 min | 1 | 无 |
| Step 1 灵感捕获 | ~10 min | 1 | 需要读 8 个文件来充分理解一致性需求 |
| Step 2 SDD 生成 | ~15 min | 1 | SDD 章节 4（接口定义）需适配 CLI 而非 Web API |
| Step 3 压力测试 | ~15 min | 1 | CLI 工具项目中 U1-U7 全部不适用，有效题目仅 3/10 |
| Step 4 反馈修正 | ~10 min | 1 | 修复 5 个漏洞后一次通过收敛 |
| Step 5 实现 | ~25 min | 1 | StepNamingChecker 正则过于宽泛，需要两轮调试 |

### 收敛数据
| 指标 | 值 |
|------|---|
| 压力测试总轮数 | 2 |
| 首轮高严重度问题数 | 1 |
| 首轮中严重度问题数 | 4 |
| 最终轮高严重度问题数 | 0 |
| 最终轮中严重度问题数 | 0 |
| 变更请求次数（CR） | 0 |
| 执行中歧义暂停次数 | 0 |

### 收敛速度（每轮严重度趋势）
| 轮次 | 高严重度 | 中严重度 | 低严重度 |
|------|---------|---------|---------|
| Round 1 | 1 | 4 | 2 |
| Round 2 | 0 | 0 | 0 |

---

## Start / Stop / Continue 反馈

### Start（应该开始做的事）
| 建议 | 原因 |
|------|------|
| 为 CLI 工具项目类型提供精简压测题集 | 通用层 10 题中 U1-U7 对无状态 CLI 全部不适用，浪费 70% 的压测时间。应有 CLI 专用的 5 题子集聚焦在路径处理、正则鲁棒性、空输入处理等 |
| 压测时增加自定义补充题 | 标准题集无法覆盖项目特有风险（如正则误报、Markdown 解析边界），本次 C1-C3 自定义题发现了真正的设计漏洞 |
| 在 Step 5 执行前先运行工具验证目标项目 | 本次实现完成后立即运行工具发现了 2 个真实断裂引用 + 17 个 StepNamingChecker 误报，如果先有冒烟测试会更早发现正则问题 |

### Stop（应该停止做的事）
| 建议 | 原因 |
|------|------|
| 停止在 SDD 中使用"或等价表述"这类模糊措辞 | spec_v1 中 ConvergenceChecker 的匹配策略用了"或等价表述"，直接导致压测 C2 漏洞。spec 应该给出精确的正则模式 |
| 停止尝试从代码块中提取可执行引用 | spec_v1 的 FileRefChecker 设计试图解析目录树代码块，无法区分真实路径和示例路径，是 C1 高严重度漏洞的根源 |

### Continue（应该继续做的事）
| 建议 | 原因 |
|------|------|
| 压测使用全新隔离上下文 | 本次压测确实发现了 SDD 设计者的盲点（代码块路径处理、模糊匹配策略），隔离上下文有效 |
| scorecard_parser 自动生成报告 | JSON → Markdown 自动化流程顺畅，避免手动填表错误 |
| 收敛阈值机制有效 | Round 1 未收敛（1H+4M）驱动了有意义的 spec 修订，Round 2 一次通过，阈值设定合理 |
| 接口契约统一（stdout/stderr/exit code） | 新工具与 scorecard_parser 接口一致，降低学习成本 |

---

## 开放式反馈

### 1. 哪个步骤的模板设计最有帮助？为什么？

**Template 03（压力测试）最有帮助。** 它强制使用全新对话并要求 JSON 格式化输出，结构化的 scorecard 让收敛判断可自动化。自定义补充题（C1-C3）发现了标准题集遗漏的真实设计缺陷。

### 2. 哪个步骤的模板设计有问题？怎么改？

**Template 03 的项目类型匹配表过于粗糙。** CLI 工具被归入"CLI 工具/纯逻辑库"使用 10 道通用题，但 U1-U7 对无状态 CLI 全部不适用。建议：
- 增加"无状态 CLI lint 工具"子类型
- 提供 CLI 专用压测题：输入边界、正则鲁棒性、空目录处理、路径解析歧义、输出格式正确性

**SDD 模板（sdd-template.md）偏向 Web/API 项目。** 章节 4 "接口定义"要求 HTTP 端点格式，CLI 工具需要改写为"命令行接口"。建议在模板中提供 CLI 变体。

### 3. AI 输出质量如何？哪些步骤需要较多人工修正？

- Step 1（需求）：质量高，结构化程度好
- Step 2（SDD）：质量中等，需要手动适配 CLI 接口格式
- Step 3（压测）：质量高，JSON scorecard 格式化准确
- Step 5（实现）：质量高，但 StepNamingChecker 正则需要两轮调试

### 4. 如果重新来过，会调整什么？

1. **先写 3 个核心测试用例再写 SDD** — 测试用例比 SDD 更能暴露接口歧义
2. **SDD 中为每个正则给出 3 个正例和 3 个反例** — 防止实现时正则过宽或过窄
3. **压测时先跳过明显不适用的题目** — 标记 N/A 而非强行回答"无风险"

### 5. 对工具链有什么改进建议？

- scorecard_parser 应支持 `--output` 标志直接写文件（当前仅 stdout）
- 新增 `--format json` 输出选项，方便程序化处理
- check_workflow_consistency 未来应集成到 pre-push hook 中

---

## 行动项

| 编号 | 行动项 | 来源 | 优先级 | 状态 |
|------|--------|------|--------|------|
| 1 | 为 Template 03 增加 CLI 工具专用压测题子集（5 题） | Start #1 | P1 | ✅ TRACK-003 完成 |
| 2 | SDD 模板增加 CLI 变体（章节 4 命令行接口格式） | 反馈 #2 | P1 | ✅ TRACK-003 完成 |
| 3 | ConvergenceChecker 等检查器的正则模式加入 SDD 模板作为必填项 | Stop #1 | P2 | ✅ TRACK-003 完成 |
| 4 | scorecard_parser 增加 --output 和 --format json | 反馈 #5 | P1 (原 L1) | ✅ TRACK-002 完成 |
| 5 | check_workflow_consistency 集成到 pre-push hook | 反馈 #5 | P1 | ✅ TRACK-002 完成 |
| 6 | CI 最小闭环（GitHub Actions 运行两个工具的测试） | 原计划 #14 | P1 | ✅ TRACK-002 完成 |
| 7 | tech-stack.md 增加决策标准（何时选 Python vs TS） | 原计划 M6 | P2 | ✅ TRACK-003 完成 |

### 演进记录

| 指标 | TRACK-001 完成时 | TRACK-002 完成后 |
|------|-----------------|-----------------|
| 测试数量 | 108 | 131 |
| 一致性检查项 | 54 | 55 |
| CI 状态 | 无 | Python 3.8 + 3.12 绿色 |
| pre-push hook | 无 | `scripts/pre-push-check.sh` |
| scorecard 输出 | stdout only | `--format json --output` |
| 仓库结构 | AgentLab monorepo 子目录 | 独立仓库 `SiriusYou/agentic-engineer` |

---

## P1 优先级排序（基于 postmortem 数据）

根据实际痛点排序：

1. **CI 最小闭环**（行动项 #6）— 两个工具共 108 个测试，应自动化运行
2. **check_workflow_consistency 集成 pre-push hook**（行动项 #5）— 实现即时反馈
3. **scorecard_parser --output/--format**（行动项 #4）— 消除手动复制步骤
4. **Template 03 CLI 压测子集**（行动项 #1）— 提高压测效率
5. **SDD 模板 CLI 变体**（行动项 #2）— 降低非 Web 项目适配成本

---

## TRACK-001 验收

| 验收标准 | 结果 |
|---------|------|
| 完整链路一次成功 | ✅ Step 1→5 + Phase 0 一次完成 |
| 记录每步耗时和迭代轮次 | ✅ 见各阶段耗时表 |
| 复盘报告包含可执行的改进建议 | ✅ 7 个行动项 + 5 项 P1 排序 |
| spec/ 包含 raw_requirements → spec_final → postmortem 完整链 | ✅ 10 个文件 |
| 工具对 spec/ 中的 JSON 正常工作 | ✅ scorecard_parser 正确解析 |
