# Prism 3.x Workspace → 4.0 迁移指南

> 本文是给人类与迁移 Agent 共用的 current runbook。目标不是把 3.x 文件“转换成”4.0，而是冻结旧状态、重新建立少量仍有效的 4.0 Topic，并把 Workspace 协作入口改写为当前三入口。

## 一句话结论

迁移采用 **archive old, reconstruct current**：

1. 3.x Topic 不原地改写；整目录移入 `archive/legacy-3x/topic/`，内容保持 byte-identical。
2. 仍需推进的问题重新创建 4.0 Topic，使用新的 Topic / Artifact id；只迁移仍有效的语义，不复制旧工作流结构。
3. 旧 Workspace `AGENTS.md` 原样存档，再按本文模板重写；项目自身的领域规则保留，3.x Prism 路由全部退出。
4. 4.0 不解析、不投影、不更新归档的 3.x Topic。需要继续用 3.x 工具写旧 Topic 时，切回 3.x 发行线或 `legacy-3x-final`。

这不是兼容层，也不是批量格式转换器。Git tag 和归档目录保存历史；current 工作面只解释 Prism 4。

---

## 迁移边界

### 必须迁移

- Workspace 协作入口：`AGENTS.md` 中的 Prism 路由、Artifact 纪律与旧目录说明。
- 仍在真实推进、且跨会话恢复仍有价值的问题空间。
- 当前有效的目标、边界、长期约束、完成条件和实施方案。
- 无法安全遗忘的未决判断与关键证据。

### 必须归档但不得转换

- 3.x `scope.md / focus.md / task.index.md / wave / reviews / decisions`。
- 3.x Topic 内的索引、frontmatter、编号和相对关系。
- Workspace 根旧版 Prism 导航 `README.md / index.md`（仅当它们主要描述 3.x 工作流）。
- 旧 `AGENTS.md` 原文。

### 不默认迁移

- 已完成、暂停或已失去当前价值的旧 Topic。
- 旧 Focus 中的瞬时进度、临时待办和可从 repository reality 重建的状态。
- 已解决 Review 全文、工作流痕迹、Wave 执行记录。
- 旧 Decision 的“Decision 身份”。缺少 current typed authority evidence 时，不得由迁移 Agent 自行重建为 4.0 committed Decision。
- 3.x 的 Skill 路由、固定阶段、Scope/Focus/Task/Wave ontology。

### 永远不做

- 不在旧 Topic 目录内补 `topic.md / intent.md / plan.md`。
- 不把 `scope.md` 改名为 `intent.md`，不把 `focus.md` 改名为 `brief.md`。
- 不复用旧 Topic 编号、Artifact id 或 Decision id 作为 current identity。
- 不运行 `store regenerate-index` 指向 3.x 归档目录。
- 不因为“旧 Decision 看起来合理”而伪造 human-choice evidence。
- 不让两个 Agent 同时修改同一个 Workspace 实例。

---

## 3.x → 4.0 语义映射

| 3.x 状态 | 4.0 承载 | 迁移判据 |
|----------|----------|----------|
| Topic | 新 Topic | 只有仍在推进的问题才重建；历史 Topic 只归档 |
| Scope | Intent | 提取为什么做、目标、非目标、跨方案约束、完成条件 |
| Focus | Brief / Plan | Brief 必须重新投影；仍有效的行动模型进入 Plan |
| Plan / Task / Wave | Plan 章节或 Child Topic | 普通执行颗粒进入 Plan；有独立目标和验收线的耐久子问题才建 Child Topic |
| Review | Review capability / Finding | 只保留尚未吸收的判断或未来仍需引用的关键证据 |
| Decision | Intent / Plan / Finding / 新 Decision | 长期边界归 Intent；方案选择归 Plan；未获 current authority 的旧承诺先成为待复核 Finding |
| Intake / references | Topic Intent / `references/` | 只链接仍有价值的历史来源，不批量复制 |
| index / digest | Brief / regenerated index | 从 current Artifact 重新生成，不迁移旧投影 |

迁移保留的是语义，不是旧文件与新文件的一一对应关系。简单旧 Topic 可以只重建 Intent；没有值得恢复的行动模型时不要生成空 Plan。

---

## Workspace 单元事务

一次只迁移一个 Workspace。每个 Workspace 都经过 Preview → Apply → Verify；Preview 默认 `writes=0`。

### Phase A — Preview（writes=0）

#### A1. 定位项目与 Workspace

在项目仓库执行：

```bash
prism topic probe
readlink workspace.<code>.local
```

若没有 current bridge，先只预览：

```bash
prism host attach --code CODE --workspace WORKSPACE_ID --dry-run
```

同时确认：

- `prism.local.yaml` 已是 named workspaces。
- project binding 是 `{path, workspace}` 对象，不是字符串。
- Workspace 实例根、项目仓库和 CODE 精确对应。
- 没有其他 Agent 正在修改同一 Workspace。

#### A2. 盘点目录

对 `topics/` 下每个编号目录分类：

| 分类 | 机械信号 | 动作 |
|------|----------|------|
| current 4.0 | 根目录存在合法 `topic.md` | 原样保留，不参与迁移 |
| legacy 3.x | 无 `topic.md`，存在 `scope.md / focus.md / task.index.md / reviews/` 等 | 整目录归档 |
| uncertain | 不符合两类，或文件损坏 | 停止该目录，不猜测 |

`prism topic probe` 的 `legacy_dirs` 只能用于数量核对，不能替代逐目录判定。

**已迁移实例快速路径**：若 `topics/` 已经只含合法 4.0 store，3.x 状态也已冻结在某个现有 `archive/` 路径，则不要为了匹配本文默认目录再次搬动历史。Preview 记录真实归档根和既有校验依据；Apply 只校准 current Topic、投影与 Workspace 协作入口。新 `AGENTS.md` 必须写实际路径，不得把模板中的 `archive/legacy-3x/` 当成已发生事实。

#### A3. 选择重建候选

每个 legacy Topic 只能进入以下一种状态：

- **archive-only**：完成、暂停、过时或无需恢复。
- **reconstruct-current**：仍在推进，目标和边界仍有效。
- **needs-human**：无法判断是否仍有效；先归 archive-only 候选，报告给人类，不擅自重建。

Preview 必须输出：

1. 旧 Topic 总数与分类。
2. 完整的拟移动 `source → target` 清单。
3. 拟重建 Topic 的旧来源、建议新标题、Intent 摘要。
4. 旧 `AGENTS.md` 中需要保留的项目规则与需要删除的 3.x Prism 规则。
5. 冲突、损坏文件、外部链接风险和需要人类确认的项目。

### Phase B — 冻结 3.x 历史

显式获得 Apply 或批量迁移授权后：

1. 创建 `archive/legacy-3x/topic/` 与 `archive/legacy-3x/workspace/`。
2. 为所有拟移动文件生成排序后的 SHA-256 清单，写到 `archive/legacy-3x/MANIFEST.md`。
3. 将 legacy Topic **整目录移动**到：

   ```text
   topics/012_example/
     → archive/legacy-3x/topic/012_example/
   ```

4. 旧 `AGENTS.md` 原样复制为 `archive/legacy-3x/workspace/AGENTS.md`。
5. 仅当根 `README.md / index.md` 主要承担 3.x 导航时，原样移入 `archive/legacy-3x/workspace/`；项目领域文档不移动。
6. 移动后重新计算归档文件 SHA-256；除路径前缀外，内容清单必须一致。

若目标路径已经存在，不覆盖、不合并，整个 Workspace 停止 Apply。不要给旧文件补 `archived: true`，因为那仍是改写历史。

推荐归档结构：

```text
Workspace/CODE/
├── AGENTS.md
├── project.yaml
├── topics/                         # 只留 current 4.0 Topic
├── archive/
│   └── legacy-3x/
│       ├── MANIFEST.md
│       ├── workspace/
│       │   ├── AGENTS.md
│       │   ├── README.md
│       │   └── index.md
│       └── topic/
│           ├── 001_old-topic/
│           └── 002_old-topic/
└── docs/
```

Host 的编号扫描会读取 `archive/legacy-3x/topic/`，因此新 Topic 不会复用旧编号。

### Phase C — 重建 current Topic

对每个 `reconstruct-current` 候选：

1. 在项目仓库运行 `prism topic probe`，使用返回的 `next_number`。
2. 创建**新的** Topic id 和目录：

   ```bash
   prism topic new topic:<new-slug> \
     --title "<当前问题标题>" \
     --intent "<为什么仍需要推进；只写目标与边界，不写实施步骤>"
   ```

3. 按 Artifact Contract 校准 `intent.md`：
   - 旧 Scope 中仍有效的目标、非目标、长期约束与完成条件可以做语义保持型转写。
   - 不明确、互相矛盾或可能已经变化的边界标为待确认；不得由 Agent 补齐。
4. 只有行动模型值得跨会话恢复时才创建 Plan：
   - 从旧 Focus / Plan / Task / Wave 提取仍有效的路线。
   - 删除瞬时进度和已经完成的执行痕迹。
   - 记录“采用什么、为什么、为何不采用实质替代”，但不复制旧工作流结构。
5. 只迁移两类 Finding：
   - 仍未解决且不能被 Intent / Plan 吸收的判断。
   - 未来仍值得引用的关键证据。
6. 旧 Decision 的处理：
   - 跨方案边界约束 → Intent。
   - 当前方案选择 → Plan，并注明历史来源。
   - 可能仍是长期承诺、但没有 current authority evidence → advisory Finding“历史承诺待人类复核”。
   - 只有人类重新确认并形成合法 evidence 后，才能记录 current Decision：`prism decision record <topic_id> --body @path --authority-evidence "<evidence ref>"`。
   - 方案级选择进入 Plan 正文；需要 acceptance 走 `prism plan accept <plan_ref> --evidence <authority ref>`。两者都不接受 Agent 自证。
7. 在新 Topic 的 `references/legacy-migration.md` 记录：
   - 旧归档相对路径。
   - 迁移日期与执行 Agent。
   - 哪些语义被吸收进 Intent / Plan / Finding。
   - 哪些内容仅归档、哪些仍待人类确认。
8. 需要直写 Intent / Plan / Findings / Clarify 候选时，先用 `prism artifact next-id <topic_id> --role intent|plan|findings|clarify` 机械取号，再按对应合同写 Markdown。
   - `--role clarify` 分配 `clarify:cNN` payload id，不会把候选变成 Decision。
   - Decision 即使先用 `--role decision` 预分配 id，也只能把该 id 交给 `prism decision record --id <decision_ref> --authority-evidence <evidence_ref>`；不得直写 `decisions/` 绕过 guard。
9. 运行：

   ```bash
   prism store validate --root <new-topic-root>
   prism store regenerate-index --root <new-topic-root>
   prism brief project topic:<new-slug> --root <new-topic-root> --save
   ```

不要手写 Brief 与 `*.index.md`。它们都是 current 状态的投影，不是旧 Focus / 旧索引的复制品；投影缺内容时修源工件。

### Phase D — 重写 Workspace 协作入口（AGENTS.md）

迁移目标是 Workspace 实例的 `AGENTS.md`，它通常通过项目仓库里的 `AGENTS.local.md` 软链接加载。

不要误覆盖项目仓库自己的共享 `AGENTS.md`：

- 项目仓库 `AGENTS.md`：项目级代码与协作规则，通常入 Git。
- Workspace `AGENTS.md`：本地 Prism 状态入口，通常由 `AGENTS.local.md` 软链接加载。
- `AGENTS.*.local.md`：设备或个人覆盖；只清理其中的 3.x Prism 路由，保留真实本机约束。

重写前先把旧 Workspace `AGENTS.md` 归档。新入口只回答三件事：**当前入口在哪**、**4.0 状态纪律**、**本项目特有规则**；不复制 3.x 工作流说明。命令表必须与 `prism --help` 逐条对得上——迁移后的协作入口是 Agent 的每日路径，写错命令比不写更贵。

#### D1. 三层入口

| 层 | 入口 | 承担 |
|----|------|------|
| Cognition 门面 | `/prism` · `/prism-review` · `/prism-plan` | 状态操作（Recover / Topic / Clarify / Maintain / Absorb）、独立评审、行动结构设计 |
| 协作面 CLI | `prism topic` · `host` · `store` · `artifact` · `brief` · `plan` · `decision` | 机械事实、投影重建、acceptance 与 Decision 的 authority guard |
| 维护动词 | `prism doctor` · `relink` · `update`（转发 `bin/` 同名脚本） | 本机环境与软链，不进入协作状态 |

当前分发面只有三个 skill（SSOT：`skills/schema/dist-whitelist.yaml`）：`prism` / `prism-review` / `prism-plan`。**`/prism-compress` / `/prism-topic` / `/prism-clarify` 这类独立入口不是当前入口**：整理与 Topic 归档是 `/prism` 的 Maintain 路由，澄清是 `/prism` 的 Clarify 路由。旧 Workspace 若写了这些 slash，本次一并删除。

#### D2. 命令面

写入模板前用 `prism --help` 复核；本表漂移时以 CLI 为准。

| 动作 | 命令 |
|------|------|
| 探测桥接 | `prism topic probe`（`bridged: yes` 才继续；`next_number` / `recent:` 用于定位；`legacy_dirs` 仅在 >0 时打印） |
| 登记桥接 | `prism host attach --code <CODE> [--workspace <WORKSPACE_ID>] [--dry-run]` |
| 新建 Topic | `prism topic new topic:<slug> --title "..." [--intent "..."]` |
| 子 Topic | `prism topic new topic:<parent>.<child> --title "..." --parent topic:<parent>` |
| 列出热区 | `prism topic list` |
| 预分配工件 / 候选 id | `prism artifact next-id <topic_id> --role intent\|plan\|findings\|decision\|clarify` |
| 查看 / 定位工件 | `prism artifact show <ref>` · `prism artifact locate <ref>` |
| 校验 store | `prism store validate [--root <dir>]` |
| 重建索引投影 | `prism store regenerate-index [--root <dir>]` |
| 投影 Brief | `prism brief project <topic_id> [--save]` |
| 记录 Plan acceptance | `prism plan accept <plan_ref> --evidence <authority ref>` |
| 记录已授权 Decision | `prism decision record <topic_id> --body @path --authority-evidence "<ref>" [--authorizes <ref>] [--supersedes <ref>]` |

#### D3. 写盘纪律

- **只有两个动作走 CLI guard**：Plan acceptance（`plan accept --evidence`）与已授权 Decision（`decision record --authority-evidence`）。二者都要求与目标及作用域绑定的 typed evidence；`--authority human-required` 是 requirement，不是 evidence。
- **Intent / Plan / Findings / Clarify 候选由 Agent 直写 Markdown**，按 `skills/prism4/artifact-contracts/` 对应合同写全，落盘后 `prism store validate`。CLI 不提供通用 `record` / mutation 面——**`prism plan record` / `prism review record` / `prism clarify record` 不存在**，模板里不得出现。
- **投影不手写**：`*.index.md` 由 `store regenerate-index` 重建，Brief 由 `brief project` 生成；投影缺内容时修源工件，不补投影。
- **普通 planning 不默认落盘**：只有跨 session 恢复、handoff 或承接需要 durable snapshot 时才写 Plan。

#### D4. 4.0 状态纪律

- Intent = 目标与边界 SSOT；Plan = 当前实施方案 SSOT；Brief / index 是投影，可随时再生成。
- Findings 只建议、不授权；Plan 也不授权执行（operative = current + valid acceptance）。Plan acceptance 不要求新建 Decision。
- Decision 只承接效力超出单一 Plan 生命周期的承诺；candidate 不得自证，Agent 不得替代人类授权。
- Roles available, not mandatory：不为协议完整生成空壳 Intent / Plan / Findings。
- 子问题用 Child Topic（`children/<slug>/`），普通执行颗粒留在 Plan 内；不建 Task / Wave 层级。
- 新需求新建 4.0 Topic；不在归档的 3.x Topic 内补写 4.0 工件。

#### D5. 目录约定

以下是**尚未迁移 Workspace 的默认布局**。若 Workspace 早期已经把 3.x 历史冻结到 `archive/YYYY-MM/topic/` 或其他稳定位置，保持原地只读并在 AGENTS 写真实路径；不要为模板整齐二次搬家。4.0 生命周期归档也优先遵守仍有效的项目特定布局，未声明时才使用 `archive/{NNN}_{slug}/`。

```text
Workspace/{CODE}/
├── AGENTS.md
├── project.yaml
├── index.md
├── topics/{NNN}_{slug}/        # 热区，4.0 store
│   ├── topic.md                # 机械锚点与导航门牌，不是事实源
│   ├── intent.md
│   ├── plans/ · findings/ · decisions/ · clarifications/
│   ├── children/<slug>/        # 子 Topic（findings / decisions 冒泡回父根）
│   └── references/             # 调研与证据预留位，不是 Core Artifact
└── archive/
    ├── {NNN}_{slug}/           # 4.0 Topic 生命周期归档（编号不复用）
    └── legacy-3x/              # 3.x 冻结区，只读
```

#### D6. 模板

```markdown
# <PROJECT_NAME>

> Prism 4.0 Workspace 协作入口。当前状态只由 4.0 Topic 与有效 Artifact 承载；
> 3.x 状态冻结在 `<LEGACY_ARCHIVE_PATH>`，仅供人工参考。

## 当前入口

| 意图 | 使用 |
|------|------|
| 创建 / 定位 Topic、恢复状态、澄清、整理归档 | `/prism`（先 `prism topic probe`） |
| 独立多视角评审，产出 Findings | `/prism-review` |
| 设计可审查的行动结构，产出 advisory Plan | `/prism-plan` |

未桥接时使用 `prism host attach --code <CODE> [--workspace <WORKSPACE_ID>]`。

## 命令面

| 动作 | 命令 |
|------|------|
| 探测 / 桥接 | `prism topic probe` · `prism host attach` |
| Topic | `prism topic new topic:<slug> --title "..."` · `prism topic list` |
| 工件 / 候选 id | `prism artifact next-id <topic_id> --role intent\|plan\|findings\|decision\|clarify` |
| 校验 / 索引 | `prism store validate` · `prism store regenerate-index` |
| 恢复切片 | `prism brief project <topic_id> [--save]` |
| 授权落盘 | `prism plan accept <plan_ref> --evidence <ref>` · `prism decision record <topic_id> --body @path --authority-evidence "<ref>"` |

维护动词 `prism doctor / relink / update` 走 `bin/`，不进入协作状态。
命令面以 `prism --help` 为准；本表漂移时改本表，不猜命令。

## 4.0 状态纪律

- Intent 是目标与边界 SSOT；Plan 是当前实施方案 SSOT；Brief 与 index 是投影，只可重新生成。
- Findings 只建议、不授权；Plan 也不授权执行；operative = current + valid acceptance。
- Decision 只记录超出单一 Plan 生命周期的承诺，并要求与作用域绑定的 authority evidence；授权在人类。
- Intent / Plan / Findings / Clarify 直写 Markdown 后 `prism store validate`；只有 acceptance 与 Decision 走 CLI guard。
- 子问题用 Child Topic，普通执行颗粒留在 Plan 内；不建 Task / Wave 层级。
- 归档的 `scope / focus / task / wave / reviews / decisions` 不进入 current 计算。

## 项目特定规则

<!-- 从旧 AGENTS.md 或项目现实中保留仍有效的领域、仓库、测试与安全规则。 -->

## 历史边界

- 3.x 归档：`<LEGACY_ARCHIVE_PATH>`（只读；新迁移默认 `archive/legacy-3x/`）
- 4.0 生命周期归档：`<CURRENT_ARCHIVE_LAYOUT>`（未声明时默认 `archive/{NNN}_{slug}/`；编号不复用，preview-first）
- 迁移记录：`<MIGRATION_MANIFEST_PATH>`
- 如需使用 3.x 工具写旧 Topic，切换到 3.x 发行线或 `legacy-3x-final`；不要在当前分支恢复兼容实现。
```

### Phase E — Verify

Apply 后必须满足：

- `topics/` 中所有编号目录都是合法 4.0 store；`legacy_dirs: 0`。
- 新迁移实例的 `archive/legacy-3x/topic/` 校验和与移动前一致；已迁移快速路径则核对 Preview 登记的真实归档根且不二次搬动。
- `prism topic list` 只列 current Topic。
- 每个新 Topic 都通过 `store validate`，Brief 可重新生成，`*.index.md` 由 `store regenerate-index` 产出。
- Workspace `AGENTS.md` 不再把 `workflow-* / workspace-init / scope / focus / task / wave` 写成当前入口。
- Workspace `AGENTS.md` 的命令表与 `prism --help` 一致：无 `prism plan/review/clarify record` 等不存在的 verb，无 `/prism-compress` / `/prism-topic` / `/prism-clarify` 等未分发 slash，维护动词不与协作面混写。
- 所有 Intent / Plan / Findings 都是直写 Markdown + `store validate` 的产物；只有 acceptance 与 Decision 经过 CLI guard 且带 evidence ref。
- 项目仓库共享规则和 Workspace 项目特定规则没有因模板覆盖丢失。
- 没有迁移 Agent 自行创建缺少 authority evidence 的 committed Decision。
- `git status` 只包含预期的项目仓库改动；Workspace 本地状态不被误提交到业务仓库。

验证失败时，不继续下一个 Workspace。归档移动可以按 MANIFEST 逆向恢复；新建 4.0 Topic 是独立目录，不需要修改旧历史即可撤回。

---

## 批量迁移编排

批量迁移可以并行，但并行单元是 **Workspace**：

- 一个 Agent 一次只负责一个 CODE。
- 同一 Workspace 只允许一个写入 Agent。
- 每个 Agent 先提交 Preview；统一授权后再 Apply。
- 混合 Workspace 中已有的 4.0 Topic 必须保持不动。
- 某个 Workspace 阻塞不影响其他 Workspace，但不得在该 Workspace 做部分归档。

### 迁移 Agent 启动话术

```text
请依据 Prism SDK 的 docs/migration.md 执行“Prism 3.x Workspace → 4.0”迁移。

本次只处理 Workspace <CODE>，项目仓库为 <PROJECT_PATH>。
先执行 Phase A Preview，writes=0：确认 bridge 和 Workspace 根，逐个分类 topics/ 下的
current 4.0、legacy 3.x 与 uncertain 目录；列出拟归档路径、拟重建 Topic、AGENTS.md
保留规则、冲突和人类待确认项。不要在 Preview 写文件。

获得 Apply 授权后，严格执行 archive old, reconstruct current：
1. 旧 Topic 整目录移到 archive/legacy-3x/topic，内容不得改写，并做前后 SHA-256 核对；
2. 仍有效的问题使用新 id 新建 4.0 Topic，只做语义重建，不转换旧文件；
3. 旧 Decision 不得自证或自动变成 current Decision；
4. 归档旧 Workspace AGENTS.md，再按文档 Phase D 重写协作入口：三层入口与命令面以 `prism --help` 为准，
   写盘纪律写清「只有 acceptance 与 Decision 走 CLI guard，其余直写 Markdown + store validate」，
   项目特定规则原样保留；
5. 完成 store validate、store regenerate-index、Brief regenerate、legacy_dirs=0 与 dead-route scan。

最终按文档的迁移报告格式返回；遇到 uncertain、目标冲突、归档目标已存在或 authority
不足时停止该 Workspace，不猜测、不覆盖、不做部分 Apply。
```

### 标准迁移报告

```markdown
## Workspace migration result

- code:
- project:
- workspace_root:
- mode: preview | applied | blocked
- legacy_topics:
- reconstructed_topics:
- current_topics_preserved:

### Archive moves
| source | target | checksum | result |

### Reconstructed state
| legacy source | new Topic | Intent | Plan | Findings | pending human |

### AGENTS rewrite
- archived_original:
- preserved_project_rules:
- removed_3x_routes:
- command_surface_verified:      # 命令表 / slash 已逐条对 `prism --help` 与 dist-whitelist 复核

### Verification
- topic probe:
- store validate:
- brief regenerate:
- checksum:
- dead-route scan:

### Skipped / blocked
```

---

## SDK 与本机环境切换

Workspace 迁移前，本机必须先运行 current Prism 4：

```bash
cd ~/prism
git status --short --branch
git switch prism-4
bin/setenv --validate
bin/doctor --scope config
bin/relink --dry-run
```

若 `prism.local.yaml` 仍是扁平配置，使用 `bin/setenv --example` 作为 current schema 参考，手工重写 named workspaces 和对象式 project binding。当前分支不自动转换旧配置。

项目未桥接时：

```bash
cd <PROJECT_PATH>
prism host attach --code <CODE> --workspace <WORKSPACE_ID> --dry-run
prism host attach --code <CODE> --workspace <WORKSPACE_ID>
prism topic probe
```

不要调用 3.x `workspace-init` 或 `workflow-*`。未知或退役 verb 在 current 分支统一走 argparse failure。

---

## 回滚与历史查看

- 3.x 可执行终态：Git tag `legacy-3x-final`。
- 4.0 中间形态只从 Changelog 与 Git tags 查看，不恢复进 current 工作树。
- 旧 Workspace 内容：`archive/legacy-3x/` + MANIFEST 校验和。
- 新建 4.0 Topic 与旧归档彼此独立；撤回新 Topic 不要求改写旧目录。
- 若必须继续维护旧 3.x Topic，使用匹配的 3.x SDK checkout，并避免让 4.0 adapter 写该归档目录。
