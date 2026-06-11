# CLI Contract — Prism 命令面契约

> 本文件固化 `bin/` 与 `prism <verb>` 命令面分层 / 稳定性承诺 / "30 秒加 verb" 设计门槛 / 双协议范围。
> 所有对 `bin/` 与 `prism <verb>` 的新增、改名、删除必须引用本文作为依据。
> **init 后日常速查** → [onboarding.md](./onboarding.md)
> 版本：v3.0.0-beta（随 SDK `VERSION` 同步升级）

---

## 1 命令面分层

Prism 的命令面分两层，职责正交：

| 层 | 入口 | 承载动作 | 典型示例 |
|----|------|---------|---------|
| **`bin/`** | 直接可执行脚本 | 仓库/环境级维护动作（一次性、跨 workspace、会碰到本地文件系统/shell 环境） | `bin/setup`、`bin/doctor`、`bin/relink`、`bin/setenv`、`bin/validate-skills`、`bin/create-skill`、`bin/clean`、`bin/rename-artifacts` |
| **`prism <verb>`** | `bin/prism` 统一入口（bash 壳 → `prism_cli.py` 分派） | workspace/topic 级动作（作用于具体专项产物，可重复、面向 Agent） | `prism sniff`、`prism validate`、`prism archive`、`prism migrate`、`prism finalize` |

### Agent 执行入口优先级

面向 Agent 的 workflow 说明必须遵循以下优先级：

| 优先级 | 入口 | 使用场景 | 文档写法 |
|--------|------|----------|----------|
| 1 | `prism <verb>` | Agent 执行 topic / workspace 主流程 | 直接写 `prism sniff` / `prism finalize` / `prism tidy` 等首选命令 |
| 2 | `uv run python <script>` | 维护者直调、调试底层脚本、或 `bin/prism` 不可用时的 fallback | 必须显式标注为“底层脚本 / fallback / 调试入口” |

因此，SKILL / workflow 文档里凡是同时存在高层 verb 与底层脚本的能力，必须以 `prism <verb>` 为主入口；底层 `uv run python ...` 只能作为实现说明或 fallback 示例，不能写成 Agent 的默认执行路径。

### 分层边界（判断树）

新增一个命令时，按以下顺序判断归属：

```
问：这个动作作用于什么？
├─ 仓库/环境/设备级（rc 文件、symlink、IDE 分发、全量 skill 扫描）
│  └─ 归 bin/
├─ 某个具体 topic 或 workspace 内的产物（reviews/ decisions/ scope.md 等）
│  └─ 归 prism <verb>
└─ 不确定
   └─ 默认归 bin/；如果后续发现 10+ 个同类动作再抽离到 prism
```

### 历史豁免条款

| 命令 | 偏离层 | 决定 | 依据 |
|------|-------|------|------|
| `prism sync` | 实际是 repo 级动作（偏 bin/ 语义） | **永久豁免，不改名** | v1.0 历史豁免[^v1.0-decision] |

> **重要**：`prism sync` 是**唯一**历史豁免，不可援引为新豁免的先例。任何新命令必须严格按上述判断树归属，不接受"比照 sync"。

---

## 2 稳定性承诺

`bin/prism` 与 `bin/` 其他命令自 v1.0 起进入稳定承诺期。

### 2.1 稳定性分级

每个 verb / bin 命令在 `prism --json manifest`（1.1+）或本文档 §6 清单中标注稳定性：

| 级别 | 含义 | 变更策略 |
|------|------|---------|
| **stable** | 名称、参数契约、输出 schema 稳定 | 破坏性变更走双 minor 保留（见 §2.2） |
| **experimental** | 可能在下一个 minor 改名/改参数 | 使用者需自行承担升级成本 |
| **deprecated** | 计划移除 | 至少保留一个 minor 版本 + 调用时打 WARN |
| **exempt** | 历史豁免（目前仅 `prism sync`） | 等同 stable；但不接受类比扩展 |

### 2.2 破坏性变更策略（双 minor 保留）

> 适用 stable / exempt 等级。

```
N+0（当前 minor）：原命令正常工作
N+1（下一个 minor）：引入新命令；原命令仍可用但调用时打 WARN；CHANGELOG 明确弃用时间表
N+2（再下一个 minor）：移除原命令；CHANGELOG 标注破坏性变更
```

**例（已发生 — 此契约真实演进过程）**：`prism pipeline` → `prism finalize` 改名链：
- v1.1 同时保留 `prism pipeline`（运行时 WARN）+ 新增 `prism finalize`
- v1.1.x 期间 SKILL/SSOT 引用渐进迁移到 `finalize`
- **v2.0** 物理移除 `prism pipeline`（按本契约 N+2 原则取代原 v1.1.x CHANGELOG 多轮预告的"v1.2 移除"承诺，调整为 v2.0 一次性落地）

### 2.3 不属于破坏性变更的调整

以下调整**不视为破坏性变更**，可在任意 minor 落地：
- 新增 verb / 新增 `bin/` 命令
- 新增可选参数（不改变默认行为）
- 新增 JSON 输出字段（不删除已有字段）
- Bug 修复（当前行为明显错误时）
- 性能优化、错误信息改善

---

## 3 "30 秒加 verb" 设计门槛

> 设计原则：所有 CLI 升级设计须通过此门槛，避免过度工程化挤压人类维护体验。

新增一个 `prism <verb>` 的成本**必须控制在 30 秒内的心智负担**：

| 必做 | 禁止 |
|------|------|
| 在 `prism_cli.py` 加 `cmd_xxx` 函数 | 要求贡献者手写 JSON schema |
| 在 `main()` 加 subparser | 要求贡献者手写 manifest entry（未来由代码自动生成） |
| 在 `dispatch_to_skill_script`（1.1+）列一行 | 要求贡献者预先写完整 pytest 用例（冒烟即可） |
| 添加一个中文 `help=` 描述 | 要求贡献者同步 6 处文档 |

任何让新增 verb 成本 > 30 秒的设计（无论出于何种理由），**必须**在 review 时被否决或降级为可选增强。

---

## 4 机器可读接口（1.1+）

为 Agent 友好性做的机器可读接口走"**单向附加**"原则——加了不改变现有使用方式。

机器可读接口在 v1.1 系列分批落地：

| 接口 | 形式 | 承诺 |
|------|------|------|
| `prism --json` 外层 schema | `{ok, command, version, data, warnings, errors}` 所有 verb 统一（完整定义见 [cli-json-schema.json](./cli-json-schema.json)） | 自首个 minor 全 verb 合规弹性演进：合规 verb 从 `schema_compliant=true` 名单逐步扩展至 100%，合规即视为 stable |
| `prism --json manifest` | 导出 verb 元数据（`verb` / `stability` / `schema_compliant` / `description`）；参数级 schema 延 024 | 1.1 起 experimental，全 verb `schema_compliant=true` 后升 stable |
| `prism --version` | 联动 SDK `VERSION` 文件（不再独立标注），VERSION 缺失时 stderr WARN + stdout 回退 `prism-cli (unknown)` | 1.1 起 stable |

### 4.1 outer schema 字段分层语义

`warnings` / `errors` 字段存在**双层语义**，消费方需严格区分：

| 层 | 触发条件 | 示例 |
|----|---------|------|
| **outer `errors[]`**（CLI 级） | CLI 调用本身失败：参数非法、未捕获异常、dispatch 失败 | `{code: "INVALID_ARG", message: "/x 不是目录"}` |
| **outer `warnings[]`**（CLI 级） | CLI 调用成功但有旁路事件 | `{code: "VERSION_MISSING", message: "..."}` |
| **`data.errors[]`**（业务级） | verb 业务逻辑发现的 ERROR（如 validate 发现 frontmatter 违规） | 各 verb 自定义 |
| **`data.warnings[]`**（业务级） | verb 业务逻辑发现的 WARN | 各 verb 自定义 |

判据：**`ok=true` 时 outer `errors` 必为空数组**（即便 `data.errors` 非空，仍算 CLI 调用成功）；**`ok=false` 时 outer `errors` 必含至少一条**。

### 4.2 `Issue` item 约定

outer `warnings[]` / `errors[]` 的每一项结构：

- **`code`**（必填）：稳定的错误/警告码，`UPPER_SNAKE_CASE`，供消费方分派
- **`message`**（必填）：人类可读说明
- **`hint`**（可选）：修复建议
- **未来字段**：`path` / `severity` / `context` 等延后按需扩；消费方须容忍未知字段（schema `additionalProperties: true`）

### 4.3 双协议范围 — `prism --json` (envelope) vs `bin/doctor --json` (flat)

> 背景：v1.1.x 评审阶段曾发现两个 JSON 解析消费误用：①把 `prism sniff --json` 的 `data` 字段误读成顶层；②误用不存在的 `prism doctor` 命令解析 stderr 文本。本节把双协议显性化，杜绝消费者再次误判。

| 协议 | 入口 | 形态 | 用途 |
|------|------|------|------|
| **envelope JSON** | `bin/prism <verb> --json` 或 `prism --json <verb>` | `{ok, command, version, data, warnings, errors}` 外层包裹 | 所有 `prism` verb；4.1 双层语义；可消费 `data` 字段 |
| **flat JSON** | `bin/doctor --json` | 直接业务字段（`{version, timestamp, sdk_root, errors, warnings, ...}`，无 `data` 包裹）| 仓库/环境级体检；扁平结构便于日志聚合 |

#### 消费者使用规则（必读）

```python
# ❌ 错误（典型误用实例）：把 envelope 当 flat
proc = subprocess.run(["bin/prism", "sniff", "."], ...)
data = json.loads(proc.stdout)
print(data["workspace"])    # ← KeyError，业务字段实际在 data["data"]["workspace"]

# ✅ 正确：先解 envelope，再读 data
envelope = json.loads(proc.stdout)
assert envelope["ok"] is True
business = envelope["data"]
print(business["workspace"])

# ✅ flat JSON 路径（bin/doctor）反而直接读
doctor = json.loads(subprocess.run(["bin/doctor", "--json"], ...).stdout)
print(doctor["errors"], doctor["warnings"])    # 直接读，无包裹
```

#### 命令归属判定（避免命令拼错）

| 你想做什么 | 用什么命令 | 协议 |
|------------|-----------|------|
| 探测 topic / 校验产物 / 工件对齐 / 痕迹抽检 | `bin/prism <verb> --json` | envelope |
| 仓库/环境/IDE 级体检（含 doctor / setup / relink） | `bin/<command> --json` 等 | flat（按命令文档） |

> **不存在 `prism doctor` verb**（`bin/prism --help` 可见 verb 列表 — sniff/validate/archive/reactivate/migrate/sync/relink/finalize/tidy/status/digest/validate-trace/manifest；自 v2.0 起 `pipeline` 已物理移除）。如果尝试 `bin/prism doctor` 会得到 argparse stderr 文本（不是 JSON），不要误读为"协议违反"。正确入口是独立的 `bin/doctor`。

#### 守门测试

`skills/workflow/shared/tests/test_review_sniff_empty_reason.py::TestCliJsonOutput::test_empty_reason_field_in_outer_envelope` 锁定：sniff 业务字段必须在 `envelope.data` 下，envelope 顶层不应出现业务字段（防协议倒退）。

---

## 5 当前 CLI 清单（v2.0.0）

### 5.1 `bin/` 一览

| 命令 | 稳定性 | 用途 |
|------|-------|------|
| `bin/setup` | stable | 一键初始化 / 健康检查 / 重配置检测 |
| `bin/doctor` | stable | 统一体检入口（scope: env / skill / sync / cli / config / release）；`--rollback` 回滚 `--fix` 修改；`--output <path>` 写入文件 |
| `bin/relink` | stable | 跨 IDE 软链接分发 |
| `bin/setenv` | stable | `prism.local.yaml` 配置管理 |
| `bin/validate-skills` | stable | skill frontmatter 合规扫描 |
| `bin/create-skill` | stable | 从模板创建 skill 骨架 |
| `bin/clean` | stable | 归档管理（`--add/--restore/--list`） |
| `bin/rename-artifacts` | stable | 批量重命名工具 |
| `bin/prism` | stable（见 5.2 分 verb） | workflow verb CLI 统一入口 |

### 5.2 `prism <verb>` 一览

> `JSON` 列：✅ = 已迁移到 outer schema（`--json` 合规）；⬜ = 未迁移，沿用旧 payload（024 或后续 minor 收敛）
> **本表由 `prism --json manifest` 反向守（见 `tests/test_cli_contract_sync.py`），任何人工修改需同步 `VERB_REGISTRY`。**

| Verb | 稳定性 | JSON | 用途 |
|------|-------|------|------|
| `prism sniff` | stable | ✅ | 探测 topic_affinity / next_review_number（`--kind review\|intake`） |
| `prism validate` | stable | ✅ | 校验产物格式（frontmatter / 命名规范） |
| `prism archive` | stable | ⬜ | 归档 topic 到 archive/ |
| `prism reactivate` | stable | ⬜ | 将 archive topic 移回 topics/ 活跃区 |
| `prism migrate` | experimental | ⬜ | 迁移 review 子目录格式（1.2 如无新用例将降为过渡期工具） |
| `prism sync` | **exempt** | ⬜ | 嗅探 SDK/Skills/Env 三仓 Git 状态（历史豁免） |
| `prism relink` | stable | ⬜ | 刷新项目/Skills IDE 软链接（委托 `bin/relink`） |
| `prism finalize` | experimental | ⬜ | Decision 后一键 tidy + validate + validate-trace (Step 2.5) + scope 提示 |
| `prism tidy` | experimental | ⬜ | 工件机械对齐（README 指针 / review.index / frontmatter） |
| `prism status` | experimental | ⬜ | Workspace 活跃 topic 健康度扫描 |
| `prism digest` | experimental | ⬜ | Topic 工件采集（供 Agent 生成摘要） |
| ~~`prism pipeline`~~ | **removed (v2.0)** | — | v1.1.x 已为 deprecated alias；v2.0 物理移除。v1.x 调用方请改用 `prism finalize`；调用 `prism pipeline` 现 hard fail（exit 2）|
| `prism manifest` | experimental | ✅ | 导出 verb 元数据（stability + schema_compliant）；参数级 schema 延后批 |
| `prism validate-trace` | experimental | ✅ | 扫描痕迹义务家族（task_probe / decision_artifact / intake_gate_out / merge_artifact，自 v2.0 起永久封顶 4 族）；`--lenient` 旧产物迁移期使用 |

---

## 6 变更历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-21 | v1.0 | 初版；固化 `bin/` vs `prism` 分层、稳定性承诺、30 秒门槛、豁免条款 |
| 2026-04-22 | v1.1-M0 | §4 编号收敛 + `prism --version` 联动 SDK VERSION 承诺写入 |
| 2026-04-22 | v1.1-M1 | §4 加 `cli-json-schema.json` 反向引用；新增 §4.1 双层语义 + §4.2 Issue item 约定；承诺表述从"1.1 起 stable"改为弹性演进 |
| 2026-04-22 | v1.1-M2 | §5.2 加 `JSON` 列 + 新增 `prism manifest` 行；表格改由 `VERB_REGISTRY` 反向守（pytest + pre-commit hook 示例） |
| 2026-04-23 | v1.1-M3 | §5.2 新增 `finalize/tidy/status/digest` 四行；`pipeline` stability 改 deprecated；§2.2 示例更新 |
| 2026-04-23 | v1.1-M4 | T4 `_dispatch_subprocess` 辅助函数；T5 `RELEASE_HEALTH.json` + `--output`；T6 `--rollback`；§6.1 bin/doctor 更新 |
| 2026-04-24 | v1.1.0 | VERSION / README / CHANGELOG / schema 示例口径统一到 `v1.1.0` |
| 2026-05-12 | v1.1.5 | §5.2 新增 `prism validate-trace` 行（痕迹义务家族机器抽检 verb，含 4 族 + `--lenient` 迁移期支持）；§4.x 加 `--json` 双向顺序兼容（`prism manifest --json` ↔ `prism --json manifest`）；finalize 加 `--decision` flag + PRISM_NO_INTERACTIVE 守门 |
| 2026-05-13 | v1.1.6 | §4.3 新增双协议显性化（`prism --json` envelope vs `bin/doctor --json` flat）；finalize 新增 `--trace-strict` / `--trace-lenient` / `--no-trace-validate` flag + Step 2.5 痕迹抽检（特定前缀 topic 默认 strict / 其他 lenient / frontmatter 与 ENV 可覆盖） |
| 2026-05-13 | v1.1.7 | §5.2 finalize description 加 "validate-trace (Step 2.5)"；pipeline 行加"不支持 trace flag"脚注 |
| 2026-05-14 | **v2.0.0-alpha** | §5.2 `prism pipeline` 行从 deprecated 改为 ~~removed (v2.0)~~（物理移除 alias，调用方 hard fail exit 2）；§2.2 改名示例段更新为"已发生改名链"叙事（v1.1 → v2.0 完整路径）；§1 / §2 / §4 默认路径脱敏（移除内部 review/decision 链路引用）；§6 表 vault link 迁出主表[^variant-history]；VERSION / manifest / 默认文档口径对齐。<br>（开发期 v2.0-canary 阶段的契约迭代已收编进本行。）|
| 2026-05-16 | **v2.0.0-beta.1** | 版本口径从 v2.1.0 统一为 v2.0.0-beta.1（v2 尚未对外发布，重新梳理版本号）；`prism --version` 与 SDK `VERSION` 同步。|
| 2026-06-08 | **v3.0.0-beta** | Prism 3.0 beta 首版：维护技能三角、docs 三层 IA、review sniff 路由修复；`VERSION` / 叙事层统一为 `v3.0.0-beta`（结束 v2 发行线与 v3 叙事双轨）。|

[^variant-history]: 各版本变更的详细 review / decision 推导链路保留在 vault Workspace 内部历史档案中，不在本契约暴露；参与维护的人员可通过 SDK 内 `references/maintainer.md` 等维护者文档定位。

[^v1.0-decision]: v1.0 历史豁免决策的完整推导记录在 vault Workspace 治理历史档案中。
