# spec/ — 项目规划产物目录

本目录存放首个真实项目闭环的所有规划产物。

## 预期文件结构

```
spec/
├── raw_requirements.md    Step 1 灵感捕获输出
├── spec_v1.md             Step 2 SDD 生成输出
├── scorecard_v1.json      Step 3 压力测试评分卡
├── stress_test_v1.md      Step 3 漏洞记录表
├── spec_v2.md             Step 4 迭代修正输出（如有）
├── scorecard_v2.json      Step 3 重测评分卡（如有）
├── spec_final.md          收敛后锁定的最终 Spec
└── postmortem_v1.md       Phase 0 复盘报告
```

## 如何开始

1. 从 `plan/template_01_inspiration.md` 开始灵感捕获
2. 按 `plan/quick_reference.md` 中的 5 步流程逐步执行
3. 每步产物按上述命名规范保存到本目录
4. 完成后使用 `plan/template_00_postmortem.md` 执行复盘

## 验收标准

- 完整链路一次成功：raw_requirements → spec_final → postmortem
- 记录每步耗时、迭代轮次、严重度下降曲线
