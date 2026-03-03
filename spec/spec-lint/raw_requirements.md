# spec-lint — 需求捕获（Step 1）

## 灵感来源

TRACK-001 postmortem 反馈 #2 指出 SDD 模板的完整性缺乏自动化验证。当前流程依赖人工检查 spec_final.md 是否包含所有必填章节、字段格式是否正确。这在迭代次数增加后成为瓶颈。

## 核心问题

**如何在进入 Step 5 实现前，自动验证 SDD 文档是否满足模板要求？**

## 用户场景

1. 作为方法论使用者，我希望在锁定 spec 前运行 `spec-lint spec/spec_final.md`，确认文档完整
2. 作为 CI pipeline，我希望在 pre-push hook 中自动检查新增/修改的 SDD 文档
3. 作为压力测试审查者，我希望确认 SDD 中的模式定义（章节 8）包含正反例

## 功能需求

- 检查必填章节（1-6）是否存在
- 检查文档头部格式（版本、状态、日期）
- 检测残留的 TBD/待定标记
- 检查 CLI 接口变体（4.B）的 exit code 表完整性
- 检查模式定义章节（8）的正则正反例
- 支持 `--format json` 和 `--format summary` 输出
- 支持 `--strict` 模式（将 warning 升级为 error）

## 非功能需求

- Python 3.8+ 兼容
- 零外部依赖（仅 stdlib）
- 单文件实现（与 check_workflow_consistency.py 风格一致）
- exit code：0 = 通过，1 = 检查失败，2 = 使用错误

## 与现有工具的关系

| 工具 | 验证维度 | 输入 |
|------|---------|------|
| check_workflow_consistency | 跨文件引用一致性、命名规范、阈值同步 | 整个项目目录 |
| spec-lint（本工具） | 单文件 SDD 格式完整性 | 单个 spec_final.md |
| scorecard_parser | 压力测试评分卡解析 | scorecard JSON |

## 约束

- 不涉及语义判断（"SDD 写得好不好"），仅做结构化格式检查
- 不重复 check_workflow_consistency 的跨文件检查逻辑
- 输出接口与 scorecard_parser、check_workflow_consistency 保持一致（stdout/stderr/exit code 三通道）
