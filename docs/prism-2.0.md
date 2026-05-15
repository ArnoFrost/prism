# Prism 2.0 — 当前定位与成熟度说明

> 这不是安装文档，也不是完整架构文档。它只回答四个问题：**Prism 现在是什么、为什么算成立、边界在哪里、接下来还差什么。**
> 当前发行口径：`v2.1.0`（v2.0.0 GA 之后的 minor 升级）。`v1.0.0` / `v1.1.x` 是历史里程碑；`v2.0` 表示破坏性收敛与简化阶段（在 v2.0.0 完成）；`v2.1` 是 v2.0 GA 之后补齐的 5 件套交付（迁移 / 贡献者 / 受众分层 / 默认面扫描 / 发布门禁）。本文继续以 "Prism 2.0" 为定位陈述入口；v2.1 增量在 §「v2.1 已完成」中追加。

---

## 一句话版本

Prism 2.0 在 1.0 已成立的"个人 AI 工作流管线"之上，进一步把**治理框架降级为可选**、**默认路径与内部状态痕迹解耦**、**workflow 复杂度刻意收敛**——成为一个"开箱用得轻、需要时治理也跟得上"的本地优先工作系统。

---

## 它现在是什么

四层正交载体仍然成立，与 1.0 阶段一致：

| 层 | 角色 | 当前状态 |
|----|------|---------|
| **SDK** | 协议、模板、CLI、内置 workflow 主干 | v2.0 进入稳定承诺期（pipeline alias 物理移除） |
| **Skills** | 可复用的自然语言能力（可分享的能力层） | 保持轻量，不再承担系统主干职责 |
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

Prism 2.0 已经完成主线四段叙事并进入 GA 口径，但它**还不等于**：

- 一个已经完成大规模泛化验证的通用产品
- 一个对多人团队协作已完全验证的控制面
- 一个已经面向公众大规模开放的发行版

换句话说，v2.0 主线已经落地，当前主要欠账在**更多真实项目 dogfood 与对外试点**——而不在核心架构本身。

---

## 当前边界在哪里

### 已经成立的部分（v2.0 主线四段）

1. **历史包袱清偿** — 产物校验按日期降噪、SKILL.md 复杂度警戒列表、SSOT 边界澄清
2. **deprecated 别名物理移除** — `prism pipeline` 一次性切到 `prism finalize`
3. **治理路径默认弱化** — workflow / 痕迹义务家族明确为可选项；core contract 仅 `SDK + Vault Workspace + uv`
4. **workflow 复杂度简化** — review skill 主文 −14% / 痕迹义务家族永久封顶 4 族 / `detect_review_mode` SSOT 反位修复

外加 v2.0 阶段的**对外面收敛**：默认路径脱敏（README / AGENTS / CLI argparse / cli-contract / SKILL 主文）+ pipeline 残留扫除 + maintainer 文档跳转弱化。

### 仍然保留的边界

- **更多 dogfood 实证**：继续用 v2.0 简化后的默认 lenient 行为跑非自身 topic，验证"agent 心智负担确实下降"在不同项目里仍成立
- **对外试点节奏**：从个人样板走向小范围试点，验证接入成本与复盘收益
- **~~v2.1 规划~~**：v2.1 5 件套已全部完成（详见 §「v2.1 已完成」），不再属于"未来规划"

### 与 1.0 一致仍未关闭的边界

- 第二/第三个非 Prism 项目的长期持续验证仍不够
- 新用户从零接入的 smoke test 还值得再跑一轮
- `Quick Topic` 等降低门槛的轻量入口仍可补

---

## v2.1 已完成

v2.0 GA 之后用一个 minor 升级（`v2.1.0`，2026-05-15）把 5 件套全部落地：

| 件套 | 落点 | 含义 |
|------|------|------|
| **迁移指引** | `docs/migration.md` | v1.x → v2.0 的唯一迁移入口；破坏性变化、14 类用户可感知变化、命令替换脚本、升级检查清单 |
| **贡献者入口** | `docs/contributing.md` | L1-L4 受众分层、默认面写作 checklist、跨仓 commit 引用边界、链接禁用规则 |
| **受众分层元数据** | 维护者文档 frontmatter `audience: maintainer` | 让默认面扫描器跳过维护者文档，避免内部治理标记污染用户首屏 |
| **默认面 WARN 扫描器** | `skills/workflow/shared/scripts/public_surface_scan.py` | 扫描 README / SETUP / docs / SKILL 主文中的内部治理标记（评审编号、行动编号、决策编号、开放问题编号、桥接路径字面量）并输出 WARN（不阻塞） |
| **breaking 发布门禁** | `skills/workflow/shared/scripts/release_gate.py` + CI 步骤 | conventional `feat!:` / `BREAKING CHANGE` 出现时强制要求同一 diff 同步 `CHANGELOG.md` + `docs/migration.md` |

附加修复：CI release_gate 步骤启用 `pipefail` + `fetch-depth: 0`，让发布门禁在 push 事件下能正确解析 base SHA 并真正生效。

## 现在最适合做什么

Prism 2.0/2.1 当前最不需要的是再发起一轮大重构；最适合的是：

1. **继续 dogfood 验证**
   挑更多非自身 topic 跑完整 review，证明默认 lenient + 痕迹合并 + v2.1 5 件套落地后，体验确实更轻、对外协作更顺。

2. **小范围对外试点**
   从个人样板走向小范围试点，验证接入成本与复盘收益。

3. **维护节奏**
   v2.1 之后的改动以 patch / 小 minor 为主；架构层面没有计划中的破坏性变更。

---

## 结论

如果用一句偏克制但明确的话来概括：

> Prism 2.0 把 1.0 留下的双 alias / 治理硬入口 / 默认路径状态痕迹清偿掉了；v2.1 在此之上补齐了对外文档矩阵、受众分层和发布门禁。当前主要欠账在 GA 后的 dogfood 实证与对外试点节奏，而不在核心架构本身。
