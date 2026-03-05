# ⚡ 快速参考卡（Quick Reference）
# 高频使用版：每次启动新项目时看这一页就够了

---

## 5步流程一览

```
Step 1  灵感捕获          WisprFlow 录音 → template_01 → raw_requirements.md
          │
Step 2  SDD 生成          新建 Gemini → template_02 → spec_v1.md  (先看 skills/sdd-template.md 末尾速查)
          │
Step 3  压力测试          全新 Gemini（必须新窗口）→ template_03 → scorecard_v1.json + stress_test_v1.md
          │
          ├── 发现漏洞 → Step 4
          └── 满足收敛阈值（0 高 + ≤3 中）→ Step 5
          │
Step 4  反馈修正          回到 Step 2 的 Gemini → template_04 → spec_v2.md → 重回 Step 3
          │
Step 5  锁定执行          spec_vN.md 复制为 spec_final.md → 交给 Claude Code
```

---

## 每步用哪个对话

| 步骤 | 工具 | 对话要求 |
|-----|------|---------|
| Step 1 | 任意 AI | 随便 |
| Step 2 | Gemini | **新建** |
| Step 3 | Gemini | **必须全新**（和 Step 2 完全隔离），分层问题（10-20 题） |
| Step 4 | Gemini | 复用 Step 2 的对话 |
| Step 5 | Claude Code | 新项目 |

---

## 文件命名规范

```
项目目录/spec/
├── raw_requirements.md    Step 1 输出
├── spec_v1.md             Step 2 输出
├── scorecard_v1.json      Step 3 输出（结构化评判数据）
├── stress_test_v1.md      Step 3 输出（漏洞记录表）
├── spec_v2.md             Step 4 输出（如有）
├── scorecard_v2.json      Step 3 重测（结构化评判数据，如有）
├── stress_test_v2.md      Step 3 重测（漏洞记录表，如有）
└── spec_final.md          最终锁定，唯一交付给 Claude Code 的文件
```

---

## 常见卡点处理

**Q: Step 2 的 SDD 缺少某个章节**
→ 在同一对话追问，不要新建

**Q: Step 3 发现了很多问题，感觉要改很多**
→ 正常，这说明压测有效。批量整理后一次性给 Step 4 处理，不要来回小修

**Q: Step 4 修订后重测，又发现新问题**
→ 正常，循环 2-3 轮是预期内的。如果循环超过 5 轮，说明原始需求本身不清晰，
   回到 Step 1 重新梳理需求

**Q: spec_final.md 锁定后发现遗漏**
→ 参见上方「变更请求流程」，按 CR 流程创建 spec_final_v2.md

---

## 变更请求流程（Change Request）

适用于 spec_final.md 锁定后发现需要修改的情况。

### 触发条件
| 类型 | 示例 | 严重度 |
|------|------|--------|
| Spec 逻辑漏洞 | 执行中发现接口定义冲突 | 必须走 CR |
| 外部需求变更 | 客户/产品要求新功能 | 必须走 CR |
| 遗漏问题 | 压力测试未覆盖的场景 | 必须走 CR |
| 文字勘误 | 错别字、格式问题 | 直接修正，不走 CR |

### 流程
1. 创建变更说明：一句话描述 + 影响的 Spec 章节列表
2. 评估范围：如果影响 >50% 章节，考虑重新走 Step 1
3. 复制 spec_final.md → spec_final_v2.md
4. 在 spec_final_v2.md 中修改（只改必须改的章节）
5. 全新 Gemini 对话，对完整 spec_final_v2.md 重新执行 Step 3（压力测试）
6. 满足收敛阈值（0 高 + ≤3 中）后锁定 spec_final_v2.md
7. 通知 Claude Code 切换到新版本

### 文件命名
spec_final.md → spec_final_v2.md → spec_final_v3.md
（配套产物：scorecard_final_v2.json, stress_test_final_v2.md）

### 原则
- 绝不修改已锁定的 spec_final.md
- 每次变更有明确的触发原因记录
- 修改范围最小化，只改必须改的章节
- 已提交的代码不回滚，在新版 Spec 基础上增量修改

---

## 项目复盘（Phase 0）

项目完成后，使用 `plan/template_00_postmortem.md` 执行复盘。
记录每步耗时、迭代轮次、严重度下降曲线，收集流程改进数据。

---

## 工具命令参考

### scorecard_parser

```bash
# 默认 Markdown 输出
python3 tools/scorecard_parser.py spec/scorecard_v1.json

# JSON 结构化输出（用于自动化管道）
python3 tools/scorecard_parser.py spec/scorecard_v1.json --format json

# 写入文件
python3 tools/scorecard_parser.py spec/scorecard_v1.json --output report.md
python3 tools/scorecard_parser.py spec/scorecard_v1.json --format json --output report.json
```

### check_workflow_consistency

```bash
# 完整报告
python3 tools/check_workflow_consistency.py

# 摘要模式（适合 CI/hook）
python3 tools/check_workflow_consistency.py --format summary
```

---

## Claude Code 启动命令

```
请按照 spec-driven-dev 执行规范，实现 spec/spec_final.md 中定义的系统。
原子化提交，严格对应 Spec 章节，发现歧义立即停下来报告。
```
