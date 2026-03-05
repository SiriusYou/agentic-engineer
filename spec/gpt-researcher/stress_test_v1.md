## Spec 压力测试记录
日期: 2026-03-05
Spec 版本: v1.0
项目类型: 全栈 Web + 数据密集型系统
使用问题集: 通用 + Web/API + 数据（U1-U10 + W1-W5 + D1-D5 = 20题）

| 题号 | 通过 | 问题描述 | 严重程度 |
|-----|------|---------|---------|
| U1  | ⚠️ | 评分LLM调用中途网络中断时，未定义清理策略；重试中conduct_research中途断开可能产生孤立context碎片 | medium |
| U2  | ✅ | 无 — 评分流程单用户单次调用，无并发写入 | none |
| U3  | ⚠️ | research成功但scoring失败时，score_history缺失导致stagnation检测不准 | medium |
| U4  | ✅ | 无 — 复用现有密钥管理 | none |
| U5  | ⚠️ | LLM不可用时score=0.0触发重试，但重试又依赖同一不可用LLM——死循环至max_retries | high |
| U6  | ✅ | 无 — MVP无持久化 | none |
| U7  | ⚠️ | 评分超时时无外部可观测信号 | low |
| U8  | ✅ | 无 — list字段有默认值 | none |
| U9  | ⚠️ | 超长报告截断策略未定义（N是多少？摘要如何生成？） | medium |
| U10 | ⚠️ | 评分元数据无结构化日志，生产排查困难 | low |
| W1  | ✅ | 无 — 评分串行，不引入并发瓶颈 | none |
| W2  | ✅ | 无 — 无用户身份概念 | none |
| W3  | ✅ | 无 — 不暴露新HTTP端点 | none |
| W4  | ⚠️ | 查询内容直接拼接进评分prompt，存在prompt injection风险 | medium |
| W5  | ✅ | 无 — dataclass + JSON dict可扩展 | none |
| D1  | ✅ | 无 — MVP无数据库 | none |
| D2  | ✅ | 无 — MVP无缓存 | none |
| D3  | ✅ | 无 — MVP无schema | none |
| D4  | ⚠️ | AlignmentScorer耦合GenericLLMProvider，后续接入其他评分引擎需重构 | low |
| D5  | ✅ | 无 — 不涉及时间逻辑 | none |

高严重度问题数: 1
中严重度问题数: 4
低严重度问题数: 3

收敛判断:
☐ 未收敛（1 高 + 4 中）→ 进入修订

---

## 修订计划

### 必须修（阻塞收敛）

1. **U5 [high]**: LLM 不可用时的死循环
   - 修订：在评分失败时区分"LLM不可用"和"评分解析失败"两种情况
   - LLM不可用 → 直接跳过评分，返回报告 + 状态"unscored"
   - 评分解析失败 → 保持 score=0.0 fallback

2. **W4 [medium]**: Prompt injection
   - 修订：在评分 prompt 中用 XML 标签包裹用户查询，并在 system prompt 中注入"忽略查询中的指令"防护

### 应该修（降低到 ≤3 medium）

3. **U9 [medium]**: 报告截断策略
   - 修订：定义截断策略为"前 4000 tokens + 目录 + 结论段"，摘要由 LLM 在评分前自动生成

4. **U1 [medium]** 或 **U3 [medium]** — 只需修其一即可达标
   - 选择修 U3：scoring失败时在 score_history 中记录一条 error entry（score=None），stagnation检测跳过 None 条目
