# Prism 4.0 Testing Contract

测试只守 current contract，不复刻历史协作仪式。本文档是面向维护者的测试控制面：每个测试文件都必须能回答它保护什么、接受哪些输入、处于什么生命周期，以及何时可以删除。

协议语义见 `prism-4-refoundation-alignment.md`，模块边界见 `architecture.md`。历史格式只允许作为“应 fail closed”的反例输入，不得成为继续支持的正向合同。

## 生命周期

| 状态 | 含义 | 处理方式 |
|------|------|----------|
| `canonical` | 某条 current contract 的主要证明 | 变更合同前必须同步修改 |
| `boundary` | 跨模块、失败路径或消费侧守卫 | 保持小而明确，不复制 canonical 全流程 |
| `smoke` | 只证明入口、安装物或脚本能启动 | 不扩成语义测试 |
| `retiring` | 合同已退出活树，等待删除 | 必须给出接管者或删除依据 |

## 契约登记表

| Contract ID | 守护边界 | Owner | Supported inputs | Lifecycle | Primary tests | 最小运行命令 | Retirement trigger |
|-------------|----------|-------|------------------|-----------|---------------|--------------|--------------------|
| C-PROTOCOL | Topic / Artifact / Capability / Invocation / Decision Semantics；Findings 不授权、Plan 默认 advisory | `prism4/` | current 4.0 typed models 与 use cases | canonical | `test_prism4_core.py`、`test_prism4_use_cases.py` | `uv run pytest tests/test_prism4_core.py tests/test_prism4_use_cases.py -q` | 五原语或 use-case 边界重定义 |
| C-AUTHORITY | authority evidence、Plan acceptance、Decision commitment 与 candidate 拒绝路径 | `prism4/use_cases.py` | current typed refs；无证据、伪证据与早期 Decision 形态仅作 fail-closed 反例 | canonical | `test_prism4_authority_hardening.py` | `uv run pytest tests/test_prism4_authority_hardening.py -q` | authority 模型重定义 |
| C-STORE | Local Markdown adapter、序号唯一、写入 guard、索引投影 | `prism4/local_files.py` | current Markdown store；历史布局仅作 fail-closed 反例 | canonical | `test_prism4_local_files.py` | `uv run pytest tests/test_prism4_local_files.py -q` | 更换持久化 adapter |
| C-ROOT | store root discovery 不误认旧 JSON 或相邻目录 | `prism4/local_files.py` | current store roots；旧 JSON 仅作反例 | boundary | `test_prism4_root_discovery.py` | `uv run pytest tests/test_prism4_root_discovery.py -q` | root discovery 并入另一 canonical contract |
| C-PROJECTION | Brief / index 只投影 current effective state，可安全重建 | `prism4/projection.py` | current artifacts；无 provenance 历史 payload 仅作诊断反例 | canonical | `test_prism4_projection.py` | `uv run pytest tests/test_prism4_projection.py -q` | Brief / index 不再是投影 |
| C-HOST | Topic probe/new 与 host attach 使用 current bridge、current config、无副作用失败 | `prism4/host.py` | named-workspaces 与 `workspace.{code}.local`；旧格式只应 fail closed | canonical | `test_prism4_host_attach.py`、`test_prism4_topic_host.py` | `uv run pytest tests/test_prism4_host_attach.py tests/test_prism4_topic_host.py -q` | Host/bridge 模型重定义 |
| C-CLI | CLI 只保留机械事实、投影、校验和 guarded commitment；退役 noun 无隐藏 alias | `prism4/cli.py`、`bin/prism` | current allowlist 与显式失败输入 | canonical | `test_prism4_cli.py`、`test_prism4_cli_allowlist.py` | `uv run pytest tests/test_prism4_cli.py tests/test_prism4_cli_allowlist.py -q` | CLI noun 或 allowlist 判据重定义 |
| C-METHOD | 三入口 facade、shared kernel 和 method 写法质量保持一致 | `skills/prism4/` | `/prism`、`/prism-review`、`/prism-plan` 及 current shared methods | boundary | `test_prism4_facade.py`、`test_prism4_method_quality.py`、`test_prism4_shared_kernel.py` | `uv run pytest tests/test_prism4_facade.py tests/test_prism4_method_quality.py tests/test_prism4_shared_kernel.py -q` | 三入口或 method packaging 重定义 |
| C-CONSUMER | CLI、skills、schema、活文档对同一 current contract 的消费一致 | SDK consumers | current active surfaces；不扫描 historical 文档作正向合同 | boundary | `test_prism4_consumer_consistency.py`、`test_docs_active_surface.py` | `uv run pytest tests/test_prism4_consumer_consistency.py tests/test_docs_active_surface.py -q` | 消费者被删除或并入其 canonical owner |
| C-DISTRIBUTION | Distribution Profile 是三入口分发唯一权威 | `skills/schema/dist-whitelist.yaml` | current `prism4` profile | canonical | `test_prism4_distribution_profile.py` | `uv run pytest tests/test_prism4_distribution_profile.py -q` | 分发模型重定义 |
| C-INSTALL | setup、安装包、版本元数据、release gate 与 doctor 最小健康合同 | `bin/`、release metadata | current SDK checkout / package；缺依赖失败路径 | smoke | `test_setup_smoke.py`、`test_install_e2e.py`、`test_release_metadata.py`、`test_release_gate.py` | `uv run pytest tests/test_setup_smoke.py tests/test_install_e2e.py tests/test_release_metadata.py tests/test_release_gate.py -q` | 安装或发布载体重定义 |
| C-RELEASE | tag grammar、annotated Tag、通道隔离与发行 / 更新机械面：目标版本 fail-closed、confirmed push 可达、channel/HEAD 回滚一致、source divergence 停止、外部 Skills 不进入产品 updater | `bin/tag_resolve.py`、`bin/release`、`bin/update` | current annotated tag 集合与已选通道；lightweight/历史 baseline/非 SemVer Tag、无 upstream、无 channel source 与 diverged branch 作 fail-closed 反例 | canonical | `test_prism4_release_channel.py` | `uv run pytest tests/test_prism4_release_channel.py -q` | 发行单位改为非 tag 载体 |
| C-RELINK | current profile 分发、项目 bridge 回写与幂等 | `bin/relink` | named-workspaces；旧 path list 只作单向清理输入 | boundary | `test_relink_writeback.sh` | `bash tests/test_relink_writeback.sh` | relink 不再负责 bridge / writeback |
| C-TEST-CONTROL | 所有活测试均登记，且登记表含 owner / inputs / lifecycle / retirement | 本文档 | `tests/test_*` 文件清单 | canonical | `test_testing_contract.py` | `uv run pytest tests/test_testing_contract.py -q` | 测试控制面迁移到可生成清单 |

`test_relink_writeback.sh` 不是 pytest 用例，由 CI 显式调用。其余 `test_*.py` 必须被 `C-TEST-CONTROL` 自动核对，不能成为无主测试。

## 分层与重复预算

- Protocol / Store / Projection / Authority 各自只保留一个 canonical 语义证明面。
- CLI、Host、Consumer 只验证参数传递、边界失败和跨层一致性，不重演完整语义流程。
- Install / Release 只做 smoke；算法行为回到 owner 层测试。
- 历史输入只证明拒绝、隔离或显式诊断，不证明兼容执行。
- 同一 regression 最多保留一个 owner 层断言和一个必要的消费侧断言。

## 新增测试 gate

新增测试文件时必须同时完成：

1. 在登记表的 `Primary tests` 中归入一个 Contract ID；若没有合适合同，先说明为什么需要新增合同。
2. 声明 `Supported inputs`，明确 current 正向输入和仅用于 fail-closed 的历史反例。
3. 选择 lifecycle；不得把 smoke 写成完整流程回放。
4. 写明 retirement trigger，避免“永远不敢删”。
5. 运行 `test_testing_contract.py`，确认不存在孤儿测试。

## 删除与合并判据

满足以下任一条件才删除：合同已退出活树；已有更低层 canonical test 完整接管；测试只复刻实现而不守边界。删除前同步登记表；若一个文件混有 current 与历史断言，先保留 current invariant，再删历史正向兼容部分。

## 常用验证

完整验证：

```bash
uv run pytest tests -q
bash tests/test_relink_writeback.sh
bin/validate-skills --layer sdk
bin/doctor --scope ci
```

配置、Host 或桥接变更：

```bash
uv run pytest tests/test_prism4_host_attach.py tests/test_prism4_topic_host.py tests/test_setup_smoke.py -q
bin/doctor --scope config
```

文档或测试治理变更：

```bash
uv run pytest tests/test_docs_active_surface.py tests/test_testing_contract.py -q
```
