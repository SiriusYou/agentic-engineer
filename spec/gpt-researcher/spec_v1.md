# Output Alignment Scoring + Auto-Retry — 软件设计文档
版本: v1.0 | 状态: Draft

## 1. 项目概述

### 1.1 目标（一句话）
在 gpt-researcher 的研究流程末端插入 LLM 驱动的对齐评分器，自动评估报告是否回答了原始查询，不达标时自动重试，为无人值守管道提供质量闸门。

### 1.2 核心用户场景

1. **作为** API 调用者，**我希望** 在调用 `conduct_research()` + `write_report()` 后自动获得一个 0-10 的对齐评分，**从而** 程序化判断是否接受输出或触发后续处理。
2. **作为** CLI 用户，**我希望** 运行研究命令后在终端看到对齐评分和重试情况摘要，**从而** 不必逐字阅读报告即可判断质量。
3. **作为** 自动化管道运营者，**我希望** 设置对齐阈值后系统自动重试低分报告，**从而** 无需人工介入即可保证输出质量基线。
4. **作为** 成本敏感用户，**我希望** 系统在评分停滞时提前终止重试，**从而** 避免无效的 API 调用浪费。

### 1.3 系统边界（明确不做）
- 不实现多维度评分（准确性、深度、格式）— 仅 prompt 对齐度
- 不实现人工反馈闭环
- 不训练或微调专用评分模型
- 不修改前端 UI（Next.js 部分不动）
- 不改变现有 SourceCurator 逻辑
- 不做跨 report_type 差异化评分标准

## 2. 技术栈

| 层次 | 技术选型 | 版本 | 选择理由 |
|------|---------|------|---------|
| 主语言 | Python | 3.11+ | gpt-researcher 现有语言 |
| 异步运行时 | asyncio | stdlib | 与现有 async 架构一致 |
| LLM 调用 | GenericLLMProvider | 现有 | 复用 gpt-researcher 的 LLM 抽象层 |
| 配置 | Config 类 | 现有 | 复用 `gpt_researcher/config/` |
| 实时通信 | WebSocket | 现有 | 复用 `websocket_manager.py` |
| 序列化 | JSON (stdlib) | 3.11+ | 评分元数据输出格式 |
| 测试 | pytest + pytest-asyncio | latest | 现有测试基础设施 |

### 环境变量

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| ALIGNMENT_SCORE_THRESHOLD | float | 7.0 | 对齐评分阈值，低于此值触发重试 |
| ALIGNMENT_MAX_RETRIES | int | 2 | 最大重试次数（不含首次） |
| ALIGNMENT_ENABLED | bool | true | 是否启用对齐评分 |
| ALIGNMENT_AUTO_RETRY | bool | true | 是否启用自动重试（false = advisory only） |
| ALIGNMENT_STAGNATION_DELTA | float | 0.5 | 连续两轮评分提升低于此值则终止重试 |

## 3. 系统架构

### 3.1 组件总览

```
                    ┌──────────────────────────────────┐
                    │       GPTResearcher (agent.py)    │
                    │                                    │
                    │  conduct_research()                │
                    │       ↓                            │
                    │  write_report()                    │
                    │       ↓                            │
                    │  ┌─────────────────────────────┐  │
                    │  │  AlignmentScorer (新组件)    │  │
                    │  │  evaluate_alignment()        │  │
                    │  │       ↓                      │  │
                    │  │  score < threshold?           │  │
                    │  │    ├─ yes → retry loop        │  │
                    │  │    └─ no  → return report     │  │
                    │  └─────────────────────────────┘  │
                    │       ↓                            │
                    │  AlignmentResult (元数据)          │
                    └──────────────────────────────────┘
```

### 3.2 组件详情

#### 3.2.1 AlignmentScorer

- **职责：** 接收原始查询和生成的报告，调用 LLM 评估对齐度，返回结构化评分
- **输入：** `query: str`, `report: str`, `report_type: str`
- **输出：** `AlignmentScore` (score: float, reasoning: str, suggestions: list[str])
- **依赖：** `GenericLLMProvider`, `Config`
- **不负责：** 决定是否重试（由 RetryOrchestrator 决定）、修改报告内容

#### 3.2.2 RetryOrchestrator

- **职责：** 根据评分结果决定是否重试、检测评分停滞、管理重试计数和成本
- **输入：** `AlignmentScore`, 配置参数（阈值、最大重试次数、停滞 delta）
- **输出：** `RetryDecision` (should_retry: bool, reason: str)
- **依赖：** `AlignmentScorer`, `GPTResearcher`（触发重新研究）
- **不负责：** 执行评分（委托给 AlignmentScorer）、直接调用 LLM

#### 3.2.3 AlignmentResult（数据模型）

- **职责：** 聚合单次研究+评分周期的完整结果，供 API/CLI 消费
- **字段：** final_report, final_score, retry_count, score_history, total_cost, metadata
- **不负责：** 业务逻辑、评分计算

## 4. 接口定义

### 4.1 Python API — `GPTResearcher` 扩展

#### `GPTResearcher.conduct_research_with_alignment()`

- **描述：** 执行完整的研究+评分+重试循环
- **签名：**
  ```python
  async def conduct_research_with_alignment(self) -> AlignmentResult
  ```
- **返回：** `AlignmentResult`
- **副作用：** 可能触发多轮 `conduct_research()` + `write_report()`，通过 WebSocket 发送状态更新

#### `AlignmentScorer.evaluate_alignment()`

- **描述：** 单次评估报告与查询的对齐度
- **签名：**
  ```python
  async def evaluate_alignment(
      self, query: str, report: str, report_type: str = "research_report"
  ) -> AlignmentScore
  ```
- **返回：**
  ```python
  @dataclass
  class AlignmentScore:
      score: float          # 0.0 - 10.0
      reasoning: str        # LLM 的评分理由
      suggestions: list[str]  # 改进建议（用于重试时的 prompt 增强）
      cost: float           # 本次评估的 API 成本
  ```
- **错误处理：** LLM 调用失败时返回 score=0.0, reasoning="Evaluation failed: {error}"

#### `RetryOrchestrator.should_retry()`

- **描述：** 根据评分历史判断是否应继续重试
- **签名：**
  ```python
  def should_retry(
      self, current_score: AlignmentScore, score_history: list[AlignmentScore]
  ) -> RetryDecision
  ```
- **返回：**
  ```python
  @dataclass
  class RetryDecision:
      should_retry: bool
      reason: str  # "below_threshold" | "stagnation" | "max_retries" | "passed"
  ```

### 4.2 CLI 扩展

#### 新增参数

```
--alignment           启用对齐评分（默认：启用）
--no-alignment        禁用对齐评分
--alignment-threshold FLOAT  对齐阈值（默认 7.0）
--max-retries INT     最大重试次数（默认 2）
--no-auto-retry       仅评分不重试（advisory 模式）
```

#### CLI 输出格式

```
📊 Alignment Score: 8.2/10 (passed)
   Retries: 0 | Total Cost: $0.03

── or if retried ──

📊 Alignment Score: 7.5/10 (passed after 1 retry)
   Score History: 5.8 → 7.5
   Total Cost: $0.09
```

### 4.3 WebSocket 状态消息

```json
{"type": "alignment", "status": "evaluating", "message": "Evaluating alignment..."}
{"type": "alignment", "status": "score", "score": 5.8, "threshold": 7.0}
{"type": "alignment", "status": "retrying", "attempt": 1, "max": 2, "reason": "below_threshold"}
{"type": "alignment", "status": "complete", "final_score": 7.5, "retries": 1}
```

## 5. 数据模型

### 5.1 AlignmentScore

| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| score | float | 0.0 ≤ x ≤ 10.0 | 对齐评分 |
| reasoning | str | 非空 | LLM 评分理由 |
| suggestions | list[str] | 可空 | 改进建议列表 |
| cost | float | ≥ 0 | API 调用成本 |

### 5.2 AlignmentResult

| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| final_report | str | 非空 | 最终采用的报告文本 |
| final_score | float | 0.0 ≤ x ≤ 10.0 | 最终对齐评分 |
| retry_count | int | 0 ≤ x ≤ max_retries | 实际重试次数 |
| score_history | list[AlignmentScore] | 长度 ≥ 1 | 每轮评分历史 |
| total_cost | float | ≥ 0 | 含评分在内的总成本 |
| passed | bool | - | 最终评分是否达标 |
| termination_reason | str | enum | "passed" / "max_retries" / "stagnation" / "timeout" |

### 5.3 无持久化

MVP 不引入数据库或文件持久化。所有数据通过返回值和 WebSocket 消息传递。历史数据持久化属于后续迭代范围。

## 6. 错误处理策略

| 错误类型 | 处理方式 | 用户提示 |
|---------|---------|---------|
| LLM 评分调用失败 | 返回 score=0.0，不阻塞报告输出 | "Alignment evaluation failed, report returned without scoring" |
| LLM 评分返回非数值 | 解析失败时 fallback 为 score=0.0 | "Could not parse alignment score, treating as unscored" |
| 重试中 conduct_research 失败 | 停止重试，返回上一轮最佳报告 | "Research retry failed, returning best available report (score: X)" |
| 超时（总耗时 > 3x 原始研究时间） | 停止重试，返回当前最佳 | "Alignment retry timed out, returning best report (score: X)" |
| 配置参数越界 | 启动时 clamp 到有效范围 | 日志 warning: "threshold clamped to [0, 10] range" |
| WebSocket 断开 | 评分流程继续，跳过状态推送 | 无（客户端已断开） |

## 7. 评分 Prompt 设计

```
You are evaluating whether a research report adequately answers the original query.

Original Query: {query}
Report Type: {report_type}

Research Report:
{report}

Rate the alignment between the query and the report on a scale of 0 to 10:
- 0-3: Report is largely irrelevant or misses the core question
- 4-6: Report partially addresses the query but has significant gaps
- 7-8: Report adequately answers the query with minor gaps
- 9-10: Report comprehensively and precisely answers the query

Respond in JSON format:
{
  "score": <float>,
  "reasoning": "<1-2 sentences explaining the score>",
  "suggestions": ["<improvement suggestion 1>", "<improvement suggestion 2>"]
}
```

## 8. 已知局限与误报/漏报边界

### 评分器局限
- **自我评价偏差**：使用同一 LLM 家族评估自身输出可能偏高；MVP 接受此风险，后续可引入交叉模型评估
- **长报告截断**：极长报告可能超出评分 LLM 的上下文窗口；使用报告摘要 + 前 N 段作为评分输入
- **主观查询**：对于"探索性"查询（如"tell me about X"），高对齐度的定义模糊；评分可能偏低

### 重试局限
- **相同结果**：重试可能返回高度相似的报告（相同搜索结果 + 相同 LLM）；suggestions 注入可部分缓解
- **成本不可预测**：重试次数取决于评分结果，总成本在运行前不确定
