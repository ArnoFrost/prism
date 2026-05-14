# Prism 2.0 — 当前定位与成熟度说明

> 这不是安装文档，也不是完整架构文档。它只回答四个问题：**Prism 现在是什么、为什么算成立、边界在哪里、接下来还差什么。**
> 当前阶段版本口径：`v2.0-canary`。`v1.0.0` 与 `v1.1.x` 是已成立的历史里程碑；`v2.0` 表示在其之上完成的破坏性收敛与简化阶段。

---

## 一句话版本

Prism 2.0 在 1.0 已成立的"个人 AI 工作流管线"之上，进一步把**治理框架降级为可选**、**默认路径与内部状态痕迹解耦**、**workflow 复杂度刻意收敛**——成为一个"开箱用得轻、需要时治理也跟得上"的本地优先工作系统。

---

## 它现在是什么

四层正交载体仍然成立，与 1.0 阶段一致：

| 层 | 角色 | 当前状态 |
|----|------|---------|
| **SDK** | 协议、模板、CLI、内置 workflow 主干 | v2.0 进入稳定承诺期（pipeline alias 物理移除） |
| **Skills** | 可分享的通用能力层 | 保持轻量，不再承担系统主干职责 |
| **Env** | 设备/终端/本地习惯层 | 设计已收敛，与 SDK 解耦协作 |
| **Workspace** | topic / review / scope / plan 等状态容器 | 已是项目级协作状态的固定落点 |

变化的是**边界与默认行为**：

- **core contract 收敛**：最小运行合同从"几乎一切"明确收紧为 `SDK + Vault Workspace + uv` 三件
- **workflow 与痕迹义务家族明确为可选项**：不接入治理框架也能用
- **默认路径脱敏**：用户首屏不再看到内部评审/决策链路痕迹

因此，Prism 2.0 更接近"一个**门槛更低、边界更清晰**的个人 AI 工作操作系统稳定版"，而不是"功能更多的 1.0 升级"。

---

## 为什么说它已经成立

### 1. 主干已经做了破坏性收敛，不再背 v1.x 的双 alias 包袱

v1.1.x 的 `prism pipeline` deprecated alias 在 v2.0 由 argparse 直接 reject（`exit 2`）。`prism finalize` 是唯一入口，行为一致、文档统一、不再需要"哪个能用、哪个 deprecated"的心智维护成本。

类似地，痕迹义务家族在 v2.0 起**永久封顶为 4 族**（`task_probe` / `merge_artifact` / `decision_artifact` / `intake_gate_out`）。新场景必须扩展现有 schema，不再开第 5 族——这是刻意把治理面积锁住，避免治理通胀。

### 2. 默认体验和"治理路径"被显性解耦

v2.0 的关键转向是承认：**大多数用户不需要治理框架**。

- `prism finalize` 默认 `lenient`：缺痕迹只 WARN 不 ERR，不阻塞 `success: true`
- `workflow / 痕迹义务` 在 README / AGENTS 明确标"可选项"
- 用户首屏的 README / argparse / 文档不再带内部 review/decision 链路 ID

仅当显式启用 strict 或自身需要"多角色独立评审 + 决策可审计 + 入料路由防膨胀"时，治理框架才进入产品行为。心智门槛被刻意降到了一个"轻"的水位。

### 3. 自省能力与 1.0 一致，且更稳定

Prism 仍然能描述自己、检查自己、治理自己：

- `prism --json manifest`：导出当前 verb registry
- `prism sync`：观察 SDK / Skills / Env 三仓状态
- `bin/doctor`：体检、回滚、输出 release health JSON

v2.0 的差别是这些能力背后的契约（CLI contract / 双 JSON 协议 / 痕迹义务 schema）显性化进了 `docs/cli-contract.md` 与 `docs/architecture.md`，并由测试套守门，不靠"约定俗成"。

### 4. 分层边界依然自洽

四层关系不变：

- **SDK** 承担主流程与契约
- **Skills** 承担轻量可分享能力
- **Env** 承担设备与终端环境
- **Workspace** 承担状态

并继续保持 v1.0 阶段的特征组合：本地优先、零侵入接入、多仓独立版控、软链接桥接。

---

## 它还不等于什么

Prism 2.0 已经在 v2.0-canary 阶段完成了主线四段叙事，但它**还不等于**：

- 一个已经完成大规模泛化验证的通用产品
- 一个对多人团队协作已完全验证的控制面
- 一个 GA 后立即可面向公众开放的发行版

换句话说，v2.0 主线已经落地，主要欠账在**dogfood 验证（多 topic 实证）+ rc1/GA 收尾**——而不在核心架构本身。

---

## 当前边界在哪里

### 已经成立的部分（v2.0 主线四段）

1. **历史包袱清偿** — 产物校验按日期降噪、SKILL.md 复杂度警戒列表、SSOT 边界澄清
2. **deprecated 别名物理移除** — `prism pipeline` 一次性切到 `prism finalize`
3. **治理路径默认弱化** — workflow / 痕迹义务家族明确为可选项；core contract 仅 `SDK + Vault Workspace + uv`
4. **workflow 复杂度简化** — review skill 主文 −14% / 痕迹义务家族永久封顶 4 族 / `detect_review_mode` SSOT 反位修复

外加 v2.0-canary 阶段的**对外面收敛**：默认路径脱敏（README / AGENTS / CLI argparse / cli-contract / SKILL 主文）+ pipeline 残留扫除 + maintainer 文档跳转弱化。

### 仍然保留的边界

- **dogfood 实证**：用 v2.0 简化后的默认 lenient 行为跑 2 个非自身 topic 的完整 review，验证"agent 心智负担确实下降"是 GA 前最后一棒
- **rc1 → GA 节奏**：canary 内 dogfood 1 周 → `v2.0.0-rc1` → squash merge main → `v2.0.0` GA
- **v2.1 规划**（不阻塞 v2.0 GA）：`docs/migration.md` / `audience` 元数据 / 机械守门 WARN / `docs/contributing.md` / 发布门禁约束

### 与 1.0 一致仍未关闭的边界

- 第二/第三个非 Prism 项目的长期持续验证仍不够
- 新用户从零接入的 smoke test 还值得再跑一轮
- `Quick Topic` 等降低门槛的轻量入口仍可补

---

## 现在最适合做什么

Prism 2.0 当前最不需要的是再发起一轮大重构；最适合的是：

1. **跑完 dogfood 验证**
   挑两个非自身 topic 跑完整 review，证明默认 lenient + 痕迹合并后体验确实更轻。

2. **走完 GA 节奏**
   archive 主线收敛 topic → `v2.0.0-rc1` tag → canary dogfood 1 周 → squash merge → `v2.0.0`。

3. **持续真实使用 + 补完 v2.1 规划**
   `migration.md` / `audience` 分层 / 机械守门 / `contributing.md` / 发布门禁是 v2.1 的 5 件套，按节奏落，不强行赶到 v2.0。

---

## 结论

如果用一句偏克制但明确的话来概括：

> Prism 2.0 已经把 1.0 留下的双 alias / 治理硬入口 / 默认路径状态痕迹这些"v1.x 必要但不优雅的妥协"清偿掉了；当前主要欠账在 GA 前的 dogfood 实证与节奏收尾，而不在核心架构本身。
