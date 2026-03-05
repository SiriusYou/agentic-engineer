# TRACK-005 Postmortem — 泛化验证：全栈项目闭环 (gpt-researcher)

## 复盘数据表

### 基本信息
| 字段 | 值 |
|------|---|
| 项目名 | gpt-researcher: Output Alignment Scoring + Auto-Retry |
| 完成日期 | 2026-03-05 |
| Spec 最终版本 | v2.0 |
| 总耗时（壁钟时间） | ~60 min |
| 项目类型 | 全栈 Web + 数据密集型系统（Python + FastAPI + Next.js） |

### 各阶段耗时
| 阶段 | 耗时 | 迭代次数 | 摩擦点 |
|------|------|---------|--------|
| Step 1 灵感捕获 | 10 min | 1 | 模板设计用于语音转录，需适配为代码库探索式输入 |
| Step 2 SDD 生成 | 20 min | 1 | 技术栈约束段需要从目标项目继承而非从 conductor 读取 |
| Step 3 压力测试 | 20 min | 1 | 20题中 D1-D5 大部分 N/A（MVP无持久化），填写为"通过"但无实质检验 |
| Step 4 反馈修正 | 8 min | 1 | 修复 4 个 spec_lint 格式问题 + 合并压测修订 |
| Step 5 锁定执行 | 2 min | 1 | spec_lint gate pass + consistency check |

### 收敛数据
| 指标 | 值 |
|------|---|
| 压力测试总轮数 | 1 |
| 首轮高严重度问题数 | 1 |
| 首轮中严重度问题数 | 4 |
| 最终轮高严重度问题数 | 0 |
| 最终轮中严重度问题数 | 0（4 个均在 spec_final 中修复） |
| 变更请求次数（CR） | 0 |
| 执行中歧义暂停次数 | 0 |
| scorecard_parser 收敛阈值 | 0 high + ≤3 medium |

### 收敛速度（每轮严重度趋势）
| 轮次 | 高严重度 | 中严重度 | 低严重度 |
|------|---------|---------|---------|
| Round 1 | 1 | 4 | 3 |
| spec_final (post-fix) | 0 | 0 (all addressed) | 3 (accepted) |

---

## 跨 Track 对比表

| Metric | TRACK-001 | TRACK-003 | TRACK-005 |
|--------|-----------|-----------|-----------|
| Total SDD Time | 80 min | 45 min | ~60 min |
| Question Set | U1-U10 (10) | C1-C5 (5) | U1-U10+W1-W5+D1-D5 (20) |
| Applicable Stress Test Qs | 3/10 = 30% (手动适配 CLI) | 5/5 = 100% (4.B 直接可用) | 15/20 = 75% (D层大部分N/A) |
| Convergence Rounds | 2 | 1 | 1 |
| High Severity Findings | 1 | 0 | 1 |
| Medium Severity Findings | 4 | 1 | 4 |
| Template Friction | High (手动适配 CLI) | Low (4.B 直接可用) | Medium (tech-stack 来源需适配) |
| spec_lint Final | N/A (不存在) | 13/13 pass | 13/13 pass |

### 对比分析

1. **SDD 耗时 60 min < 编码耗时**：通过（gpt-researcher 的对齐评分功能编码预计 4-8 小时）
2. **方法论泛化能力**：5-step cycle 在全栈项目上完整走通，无步骤被跳过
3. **模板重写比例**：~20%（主要是 tech-stack 段和 §8 示例格式），远低于 50% 失败阈值
4. **20题压测的边际收益**：通用层(U) 发现 6/10 问题，Web层(W) 发现 1/5，数据层(D) 发现 1/5。Web/数据层对功能级 MVP 的增量价值有限
5. **适用题比例 75% vs TRACK-001 的 30%**：项目类型分层表显著提升了题目匹配度

---

## Start / Stop / Continue 反馈

### Start（应该开始做的事）
| 建议 | 原因 |
|------|------|
| 为"功能级 MVP"增加轻量化压测子集（10题而非20题） | D层5题对无持久化 MVP 几乎全部 N/A，浪费评审时间 |
| 在 tech-stack 段增加"继承目标项目栈"模式 | 当前模板假设从 conductor 读取，但验证外部项目时需从目标项目继承 |

### Stop（应该停止做的事）
| 建议 | 原因 |
|------|------|
| 不要对"功能层面无持久化"的 MVP 强制使用数据层问题 | D1-D5 在 MVP scope 下全部 trivially pass，不提供真实检验 |

### Continue（应该继续做的事）
| 建议 | 原因 |
|------|------|
| 保持 spec_lint advisory → gate 两阶段策略 | v1 草稿阶段不阻塞迭代，final 阶段强制通过，平衡效率和质量 |
| 保持 scorecard_parser 自动化收敛判断 | 比手动统计更快更准确 |
| 保持 §8 正例/反例要求 | 迫使 SDD 作者思考边界情况，TRACK-005 中 §8 examples 帮助明确了评分器的实际局限 |

---

## 开放式反馈

1. **哪个步骤的模板设计最有帮助？** Step 3 压力测试 — 项目类型分层表让 20 题自动组装，U5 发现的"LLM不可用→死循环"是真实设计缺陷
2. **哪个步骤的模板设计有问题？** Step 1 灵感捕获 — 模板假设输入是"语音转录"，但 TRACK-005 的输入是"代码库探索结果"，需要增加"代码库分析"输入模式
3. **AI 输出质量如何？** SDD 生成质量高，一轮出草稿。压测发现的问题真实有效。spec_lint 格式适配需要对 §8 格式有先验知识
4. **如果重新来过，会调整什么？** 先检查 spec_lint 格式要求再写 SDD，避免 final 阶段返工格式
5. **对工具链有什么改进建议？** scorecard_parser 可增加"N/A"严重度选项，区分"通过检验"和"不适用本项目"

---

## 行动项

| 编号 | 行动项 | 来源 | 状态 |
|------|--------|------|------|
| 1 | 在 template_03 中增加"功能级 MVP"压测子集指引（通用 + 相关层，跳过 N/A 层） | Start #1 | □ 待办 |
| 2 | 在 template_02 tech-stack 段增加"继承目标项目栈"选项 | Start #2 | □ 待办 |
| 3 | 在 template_01 增加"代码库探索"输入模式（与"语音转录"并列） | 开放式 #2 | □ 待办 |
| 4 | scorecard_parser 增加 "n/a" severity 选项 | 开放式 #5 | □ 待办 |
| 5 | spec_lint 格式要求文档化为速查表，供 SDD 作者在 Step 2 开始前参考 | 开放式 #4 | □ 待办 |

---

## 结论

**TRACK-005 验证通过**：SDD 5-step methodology 在全栈项目（gpt-researcher）上成功完成完整闭环。

**关键发现：**
- 方法论核心流程（需求→SDD→压测→收敛→锁定）在全栈上下文泛化成功
- 模板需要 ~20% 适配（低于 50% 失败阈值），主要集中在 tech-stack 来源和输入模式
- 20题压测中 75% 适用，但数据层对功能级 MVP 增量价值有限
- 建议进入 TRACK-006（模板迭代），聚焦行动项 #1-#5

**Decision Gate → 进入 TRACK-006（模板迭代）**
