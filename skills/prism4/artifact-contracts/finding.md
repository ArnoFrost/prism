# Finding 写法合同

## 职责

**悬置判断 + 关键证据**。Finding 不是 Review log——Review / 讨论的结论若已被 Intent / Plan 完整表达，默认不继续占据当前协作注意力。

## 独立存在的两类判据（仅此两类）

1. **悬置判断**：无法被吸收（问题未解决）+ 不可重建（对话外无痕）+ 不可忘（阻塞施工或影响后续判断）。
2. **验证/证据材料**："为什么我们知道 X 成立"的依据，未来复盘需要且不可安全重推导。

## frontmatter 合同

```yaml
id: "finding:f01"          # finding:fNN，store 内全局递增
role: "findings"
title: "..."
topic: "topic:<slug>"
authority: "advisory"       # Findings 不授权实施
evolution: "supersedable"
created_at: "YYYY-MM-DD"
capability: "prism:review"  # 可选；来源能力。直写沉淀可省略
status: "active"            # active | absorbed | partially-absorbed（退档时追加以下两行）
absorbed_by: "plan:p01"     # 退档时必填
absorbed_at: "YYYY-MM-DD"
```

## 生命周期：吸收为默认

- 结论已完整进入 Intent / Plan → 源文件标 `absorbed` + `absorbed_by`，退出 active，文件保留（历史）。
- 部分吸收 → `partially-absorbed` + `absorbed_note` 说明未吸收部分去向。
- 退档前置：**吸收者已满足转写硬标准**（采用什么 + 为何采用 + 为何不替代方案）。
- `finding.index.md` 登记状态列，是从 findings 再生成的投影。

## 一行式形态（悬置状态的最小载体）

阻塞/等待类状态不必写成完整评审文档，一行式即可：

> "端侧输入通道三选一未决，阻塞下一阶段开工，等待拍板；拍板时升格 Decision。"

多条悬置可合并为一个汇总文件：表格 + 每行「状态 + 阻塞什么 + 等什么」，解决后被对应 Plan / Decision 吸收并从表中退出。
