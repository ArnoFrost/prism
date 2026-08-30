# Prism 4.0 Testing Contract

Prism 4.0 的测试只守边界，不复刻协作仪式。新增测试前先判断它要保护哪条 contract；如果只是某次人工流程的完整回放，优先改成更小的 invariant。

本文档是验证控制面：说明每组测试守护哪条 current contract、归谁、怎么跑、什么时候该退役。协议语义本身见 `prism-4-refoundation-alignment.md`，模块归属见 `architecture.md`，历史形态映射见 `migration.md`。

## 分层

| 层 | 守什么 | 权威来源 | 典型落点 |
|----|--------|----------|----------|
| Protocol | Topic / Artifact / Capability / Invocation / Decision Semantics 不变形；Findings 不授权；Plan 默认 advisory；Decision 才 authorizes | Alignment（Protocol Semantics SSOT） | `test_prism4_core.py` / `test_prism4_use_cases.py` |
| Authority | typed authority guard；Plan acceptance 与 operative 推导；candidate 冒充、Agent 自证一律拒绝 | Alignment §5.5 / §6.1 | `test_prism4_authority_hardening.py` |
| Adapter | 当前 Local Markdown 适配器的持久化边界；序号 store 全局唯一；prune 按文件系统身份判定；索引是投影 | `prism4/local_files.py` | `test_prism4_local_files.py` |
| Projection | Brief / index 只投影 current state，可安全重建 | Alignment §7 | `test_prism4_projection.py` |
| CLI Surface | 入口只保留机械事实、投影、校验与 guarded commitment；退役 noun 无隐藏 alias；维护动词仍可用 | CLI allowlist 合同 | `test_prism4_cli.py` / `test_prism4_cli_allowlist.py` |
| Distribution | `dist-whitelist.yaml` 是当前分发面唯一权威；Catalog 只存治理元数据 | `skills/schema/` | `test_prism4_distribution_profile.py` |
| Install / Release | `setup` 后命中当前 SDK；版本元数据一致；分发包可启动；doctor 可做最小健康检查 | `bin/release_gate.py` | `test_setup_smoke.py` / `test_install_e2e.py` / `test_release_metadata.py` / `test_release_gate.py` |
| Docs / Active Surface | 活文档不漂回历史形态；公开叙事不泄露私有路径；退役入口不回到文档与三入口技能 | 本文档 + `AGENTS.md` | `test_docs_active_surface.py` |
| Maintenance Scripts | `bin/relink` 的 Workspace 回写路径；重复 `paths:` 防护与二次写入幂等 | `bin/relink` | `test_relink_writeback.sh` |

## 契约登记表

| Contract ID | 权威来源 | Owner | Primary tests | 最小运行命令 | 退役条件 |
|-------------|----------|-------|---------------|--------------|----------|
| C-PROTOCOL | Alignment §3–§6 | SDK | `test_prism4_core.py`、`test_prism4_use_cases.py` | `uv run --with pytest python -m pytest tests/test_prism4_core.py tests/test_prism4_use_cases.py -q` | 五原语定义变更 |
| C-AUTHORITY | Alignment §5.5 / §6.1 | SDK | `test_prism4_authority_hardening.py` | `uv run --with pytest python -m pytest tests/test_prism4_authority_hardening.py -q` | authority 模型重定义 |
| C-ADAPTER | `prism4/local_files.py` | SDK | `test_prism4_local_files.py` | `uv run --with pytest python -m pytest tests/test_prism4_local_files.py -q` | 更换 Workspace adapter |
| C-PROJECTION | Alignment §7 | SDK | `test_prism4_projection.py` | `uv run --with pytest python -m pytest tests/test_prism4_projection.py -q` | Brief / index 不再是投影 |
| C-CLI-ALLOWLIST | CLI allowlist 合同（`KEEP` 表） | SDK | `test_prism4_cli_allowlist.py` | `uv run --with pytest python -m pytest tests/test_prism4_cli_allowlist.py -q` | allowlist 判据变更 |
| C-CLI-SURFACE | `prism4/cli.py` | SDK | `test_prism4_cli.py` | `uv run --with pytest python -m pytest tests/test_prism4_cli.py -q` | 协作面 noun 变更 |
| C-DISTRIBUTION | `dist-whitelist.yaml` | SDK | `test_prism4_distribution_profile.py` | `uv run --with pytest python -m pytest tests/test_prism4_distribution_profile.py -q` | 分发模型变更 |
| C-DOCS-ACTIVE | 本文档 + `AGENTS.md` | SDK | `test_docs_active_surface.py` | `uv run --with pytest python -m pytest tests/test_docs_active_surface.py -q` | 公开叙事面重定义 |
| C-INSTALL-RELEASE | `bin/release_gate.py` | SDK | `test_setup_smoke.py`、`test_install_e2e.py`、`test_release_metadata.py`、`test_release_gate.py` | `uv run --with pytest python -m pytest tests/test_setup_smoke.py tests/test_release_metadata.py -q` | 安装分发方式变更 |
| C-RELINK-WRITEBACK | `bin/relink` | SDK | `test_relink_writeback.sh` | `bash tests/test_relink_writeback.sh` | `bin/relink` 不再回写 Workspace |

`C-RELINK-WRITEBACK` 是 bash 用例，pytest 不收集 `.sh`，由 CI 显式调用；接入口见 `.github/workflows/ci.yml`。

## 发布门禁

版本提升或分发前至少跑：

```bash
uv run --with pytest python -m pytest tests/ -q
bash tests/test_relink_writeback.sh
uv run python bin/release_gate.py --repo . --base <sha> --head <sha> --json
bin/doctor --scope ci
bin/prism --version
```

若只改文档叙事，至少跑：

```bash
uv run --with pytest python -m pytest tests/test_docs_active_surface.py tests/test_release_metadata.py -q
```

若只改安装、分发、寻址，至少跑：

```bash
uv run --with pytest python -m pytest tests/test_setup_smoke.py tests/test_install_e2e.py tests/test_prism4_cli.py -k "doctor or setup or version or install" -q
```

## 新增测试规则

- 一个反馈沉淀一个最小 invariant，不复制完整人工过程。
- 能在 use case / adapter 层测清楚的，不升级成 CLI e2e。
- CLI 测试只证明参数能抵达语义层、用户入口不会误导。
- e2e 只守安装包能启动、doctor 能过、版本正确。
- 避免大段 golden text；只断言关键字段、关系、路径和少量提示语。
- 任何新增测试都要能回答：它防的是 Core 漂移、Authority 绕过、Adapter 漏洞、CLI 误导、安装失败，还是文档叙事回潮？
- 每条语义只保留一个 canonical contract test；CLI / docs / install 层最多留必要 smoke 与关键失败路径。

## 删除测试的判据

删除任何一个测试前，先回答它守哪条 current contract。答不出来就归档待查，不直接删。

回收顺序：

1. 在契约登记表里定位它的 Contract ID。
2. 确认该 contract 已随代码退出活树，或已由另一条 canonical test 接管。
3. 一个文件里同时守 current contract 与历史形态时，先拆出 current 部分再删历史部分（例：`test_pilot_readiness.py` 的 catalog / whitelist 分权拆为 `test_prism4_distribution_profile.py`）。
4. 「不在 pytest 里」不等于「没有守护价值」——`bin/` 下的 bash 用例要在 CI 里显式接入口，而不是删除。
