# TRACK-007 Postmortem — 外部项目 Step 5 编码验证

日期: 2026-03-05
状态: completed

## 1. 目标回顾

验证 `spec/gpt-researcher/spec_final.md` 在外部项目上的 spec→code 转化质量。

## 2. 量化指标

| 指标 | 值 | Warning 线 | Fail 线 | 判定 |
|------|-----|-----------|---------|------|
| SDD 耗时 | ~60 min (TRACK-005) | — | — | 基准 |
| 编码耗时 | ~45 min | > 5h | > 8h | PASS (0.75x) |
| 歧义暂停次数 | 1 | > 3 | > 5 | PASS |
| spec 偏差率 | 2/39 = 5.1% | > 20% | > 30% | PASS |
| 测试数 | 28 passed | — | — | — |

**编码耗时说明**：从读 spec_final 到 28 测试全绿的壁钟时间，不含环境搭建（仓库同步、pytest 环境排查）。实际编码极快因为 spec 描述充分，组件边界清晰。

**编码耗时 / SDD 耗时 = 0.75x** — 远低于 Warning 线(5x)。这表明高质量 SDD 可以大幅缩短编码时间。

## 3. 歧义暂停记录

| # | Spec 章节 | 歧义描述 | 决策 |
|---|----------|---------|------|
| 1 | 3.2.1 | Spec 说 AlignmentScorer 依赖 GenericLLMProvider，但 codebase 统一通过 create_chat_completion() 调用 | 遵循 codebase 惯例用 create_chat_completion()，属于实现细节偏差 |

## 4. Spec 偏差记录

| # | Behavior ID | 偏差内容 | 原因分类 | 影响 |
|---|------------|---------|---------|------|
| 1 | A2 | AlignmentScorer 内部通过 create_chat_completion() 而非直接使用 GenericLLMProvider | 发现更优方案 | 无功能影响，代码更一致 |
| 2 | F4 | Timeout 计算增加 60s 下限：`3 * max(first_cycle_duration, 60.0)` | spec 不可行 | 避免即时完成的 mock/快速研究触发误超时 |

偏差率：2/39 = 5.1%

## 5. 实现清单 vs Behavior Inventory

| Category | Total | Implemented | Deviated | Notes |
|----------|-------|------------|----------|-------|
| A. API Methods | 3 | 3 | 1 (A2 实现路径) | 接口签名和行为完全匹配 |
| B. Data Models | 3 | 3 | 0 | |
| C. Env Variables | 5 | 5 | 0 | |
| D. CLI Parameters | 5 | 5 | 0 | |
| E. WebSocket Messages | 5 | 5 | 0 | |
| F. Error Handling | 7 | 7 | 1 (F4 floor) | |
| G. Scoring Prompt | 5 | 5 | 0 | |
| H. Business Rules | 6 | 6 | 0 | |
| **Total** | **39** | **39** | **2** | |

## 6. 可审计证据

- **外部仓 commit**: `5164c58b` on `~/dev/gpt-researcher` (master branch)
- **测试命令**: `cd ~/dev/gpt-researcher && /opt/anaconda3/bin/python3 -m pytest tests/test_alignment.py -v -p no:logfire`
- **测试结果**: 28 passed, 0 failed, 0 skipped (8.61s)
- **文件变更**: 9 files, +971 lines

## 7. 关键发现

### 7.1 SDD 质量直接决定编码速度

编码耗时仅 ~45 min（含 3 次测试修复迭代），远低于预估的 4-8h。主要原因：

1. **spec_final 接口定义精确** — 数据模型字段、类型、枚举值全部明确，无需猜测
2. **组件边界清晰** — AlignmentScorer / RetryOrchestrator / models 三层分离，可以独立实现
3. **错误处理表格化** — 6 种错误场景的行为已在 spec 中表格列出，直接转化为 if/else

### 7.2 Behavior Inventory 有效防止口径漂移

39 项冻结清单让偏差追踪有据可查。两处偏差都在编码中被即时识别和记录，验证了 inventory 作为"测量分母"的可行性。

### 7.3 唯一的真实歧义来自实现层而非需求层

spec 在"做什么"上完全清晰，唯一的暂停发生在"怎么做"上（用哪个 LLM 调用路径）。这说明 SDD 方法论在需求→设计的转化上已经成熟，但可以考虑在模板中增加"实现路径建议"章节。

### 7.4 环境搭建是隐藏成本

pytest 环境冲突（logfire/opentelemetry 插件、anaconda vs venv）占用了额外的排查时间。这不算在编码耗时内（按协议），但在实际项目中是真实成本。

## 8. 改进建议

| # | 建议 | 优先级 | 触发条件 |
|---|------|--------|---------|
| 1 | SDD 模板增加"推荐实现路径"提示（如"使用项目现有 LLM 调用封装"）| Low | 下次模板迭代 |
| 2 | Behavior Inventory 模板化为 SDD 产物的标准一环 | Medium | 验证 inventory 在第二个项目上同样有效 |
| 3 | 测试环境配置纳入 spec 的"前置条件"章节 | Low | 面向外部贡献者时 |

## 9. 与历史 Track 对比

| 维度 | TRACK-001 | TRACK-003 | TRACK-005 | TRACK-007 |
|------|-----------|-----------|-----------|-----------|
| 主题 | 首次闭环 | 方法论迭代 | 全栈泛化 | 外部编码验证 |
| SDD 耗时 | 80 min | 45 min | 60 min | — (复用 005) |
| 编码耗时 | ~2h | ~1.5h | — | ~45 min |
| 收敛轮次 | 2 | 1 | 1 | 1 (首轮实现) |
| Spec 偏差 | 未测量 | 未测量 | 未测量 | 5.1% (2/39) |
| 模板摩擦 | High | Low | Medium | None |

## 10. 结论

TRACK-007 验证了方法论的核心价值链路：**高质量 SDD → 低成本编码**。

- 编码耗时 0.75x SDD 耗时（远低于 5x warning 线）
- Spec 偏差率 5.1%（远低于 20% warning 线）
- 仅 1 次歧义暂停（远低于 3 次 warning 线）

方法论从"规划可行" → "迭代稳定" → "泛化验证" → **"编码转化验证"** 全链路闭合。
