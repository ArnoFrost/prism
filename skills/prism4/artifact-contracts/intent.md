# Intent 写法合同

## 职责

**目标与边界的 SSOT**：为什么做、要达到什么结果、明确不做什么、长期有效的关键约束、什么状态算 Topic 真正完成。回答「什么算解决」，不回答「怎么做」。

## 何时产生 / 何时必须存在

- **Core 允许 capture-first 的无 Intent Topic**；Role available, not mandatory 在 Intent 上同样成立（Alignment §5.1）。
- **Reference Experience 分层默认**：用户已表达「为什么做」时，Topic 创建默认写入最小 Intent（一句话即可）；动机未知时创建 Topic-only，并在 Brief 中显式标注「尚未形成边界」（诚实降级，不报错、不伪造）。
- 其余节**按需回填，不强制全齐**；边界尚未形成的节，显式写明"尚未形成"，不写空壳占位。
- `prism topic new --intent ...` 可以写入紧凑初始脚手架（如「为什么做 / 边界内 / 完成条件 / 尚未声明」），用于先建立协作边界；当 Topic 进入真实校准后，应按下方五节表达已经形成的目标、非目标、长期约束与完成条件。
- 反模式：`完成条件：未声明` 且 `尚未声明` 区长期空白、又无声明性说明——这是 Role 被误当 checklist 的形态。

## frontmatter 合同

```yaml
id: "intent:i01"           # intent:iNN，Topic 内递增
role: "intent"
title: "..."
topic: "topic:<slug>"
authority: "authoritative"  # Intent 是边界事实源
evolution: "supersedable"   # 改边界 = 显式 supersedes，旧版归档
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"    # 边界修订时更新
```

## 正文五节

| 节 | 写什么 | 不写什么 |
|----|--------|----------|
| 为什么做 | 问题空间与动机 | 实施路径 |
| 要达到什么结果 | 可观察的终态 | 阶段步骤 |
| 明确不做什么 | 长期非目标 | 本方案的临时取舍 |
| 关键约束 | **跨方案持续有效**的边界 | 仅本方案有效的限制（归 Plan） |
| 完成条件 | Topic 关闭判据（Brief 恢复时要能回答） | 达成路径 |

完成条件只写可观察终态（如"新 Agent 只读有效 Artifact 与投影即可恢复目标、边界、方案与下一步"），不写达成路径。

## 生命周期

- Plan 发现边界需要变 → **先显式修 Intent（supersedes），再重新校准 Plan**；Plan 无权自行改 Intent。
- 边界修订走 supersedes + 归档，保证"目标曾经是什么、为什么改"可追溯。
