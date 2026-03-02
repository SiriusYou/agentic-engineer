---
name: spec-driven-dev
description: >
  Spec-driven development workflow for Claude Code execution agents. Use this skill whenever
  the user provides a spec file (spec.md, spec_final.md, SDD, design doc) and asks Claude Code
  to implement it. Also triggers when the user says "execute the spec", "build from spec",
  "implement this design", "start coding from the document", or when a conversation includes
  phrases like "atomic commits", "spec-first", "planning is done, now build it", or "60/40 workflow".
  This skill ensures execution follows strict spec-driven principles: read before code,
  atomic commits, build-first ordering, and zero deviation from spec without explicit approval.
---

# Spec-Driven Development — Execution Skill

## 核心原则

> **Spec 是唯一真相来源。代码实现是 Spec 的物理投影，不是创作行为。**

执行前必须完整读取 Spec，执行中不得自行扩展功能，发现 Spec 歧义必须停下来提问。

---

## 执行前检查清单（必须全部完成）

```
□ 1. 找到并读取 spec 文件（spec.md / spec_final.md / spec_final_v*.md / SDD.md）
□ 2. 确认三大板块存在：组件设计 / 接口定义 / 技术栈
□ 3. 列出所有实现模块，按依赖顺序排序
□ 4. 识别所有外部依赖（库、API、环境变量）
□ 5. 确认没有歧义点；有则立即提问，不猜测
```

如果 spec 文件不存在或不完整，**停止执行，告知用户**，不要开始写代码。

---

## 执行顺序（Build-First 原则）

```
Phase 1: Foundation（基础层）
  → 项目初始化、目录结构、依赖安装
  → 环境配置文件（.env.example, config）
  → 数据模型 / 类型定义

Phase 2: Core（核心层）
  → Spec 中定义的核心模块
  → 严格按接口定义实现，不增不减

Phase 3: Integration（集成层）
  → 模块间连接
  → 外部服务集成

Phase 4: Runnable（可运行）
  → 让系统能跑起来（哪怕功能不完整）
  → 验证关键路径通畅

Phase 5: Polish（完善层）
  → 错误处理
  → 边界条件
  → 日志和可观测性
```

**原则：每个 Phase 完成后提交一次，确保每个提交点都是可工作状态。**

---

## 原子化提交规范

### 提交粒度
每次提交只做**一件完整的事**：
- ✅ `feat: add UserRepository with findById and save methods`
- ✅ `feat: implement JWT authentication middleware`
- ❌ `feat: add users and auth and config and tests`

### Commit Message 格式
```
<type>(<scope>): <what was done>

对应 Spec 章节: <section name>
```

**类型：**
- `feat` — 新功能实现
- `fix` — 修复实现错误
- `refactor` — 重构（不改变行为）
- `test` — 添加测试
- `chore` — 配置、依赖

### 提交时机
完成一个**完整的最小功能单元**后立即提交，不积累。

---

## Spec 偏差处理

执行过程中遇到以下情况，**停止并报告，不自行决策**：

| 情况 | 行动 |
|------|------|
| Spec 中某接口描述不清晰 | 停止，列出具体歧义，等待确认 |
| 发现 Spec 中的技术选型有冲突 | 停止，描述冲突，提供两个选项 |
| 某个功能 Spec 未提及但"显然需要" | 停止，描述发现，询问是否加入 |
| 实现过程中发现 Spec 有逻辑漏洞 | 停止，描述漏洞，不自行修复 |

**禁止行为：**
- ❌ 自行添加 Spec 未定义的功能
- ❌ 更改 Spec 定义的接口签名
- ❌ 替换 Spec 指定的技术栈
- ❌ "我觉得这样更好"式的自主优化

---

## 执行进度汇报格式

每完成一个模块，输出以下格式：

```
✅ [模块名] 完成
   对应 Spec: <章节名>
   实现内容: <一句话描述>
   提交: <commit hash 前7位>

⏳ 下一步: [下一个模块名]
```

如果遇到阻塞：

```
🚫 阻塞: [模块名]
   原因: <具体描述>
   需要确认: <具体问题>
   待确认后继续
```

---

## 完成验收标准

执行完成后，输出验收报告：

```markdown
## 执行完成报告

### Spec 覆盖率
- 组件: X/X 已实现
- 接口: X/X 已实现
- 技术栈: 按 Spec 使用 ✅

### 提交记录
- 共 X 次原子化提交
- 最终可运行状态: ✅ / ❌

### 偏差记录
- 偏差数量: X
- 偏差详情: （如有）

### 未实现项
- （如有，说明原因）
```

---

## 快速参考：执行启动 Prompt

当用户给出 spec 后，用以下方式开始：

```
我将按照 spec-driven 执行规范处理这个任务。

首先读取 spec 文件...
[读取后]

Spec 解析完成：
- 识别到 X 个组件
- X 个接口定义
- 技术栈：[列出]

执行顺序规划：
1. [Phase 1 内容]
2. [Phase 2 内容]
...

有以下问题需要确认后再开始：（如有）
- [问题1]

确认后开始执行。
```

---

## ⚠️ 执行前必读

> **本 Skill 仅覆盖 Step 5（执行阶段）。未经规划直接执行 = 违反核心原则。**
>
> 规划流程（Step 1-4）：`skills/planning-workflow.md`
> 快速参考卡：`plan/quick_reference.md`

---

## 参考文档

- `skills/sdd-template.md` — SDD 模板（验证 spec 完整性）
- `skills/stress-test-prompts.md` — 压力测试 Prompt 库
