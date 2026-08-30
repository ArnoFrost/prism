# Prism 4.0 Testing Contract

Prism 4.0 的测试只守边界，不复刻协作仪式。新增测试前先判断它要保护哪条 contract；如果只是某次人工流程的完整回放，优先改成更小的 invariant。

## 分层

| 层 | 守什么 | 典型落点 |
|----|--------|----------|
| Protocol Contract | Topic / Artifact / Capability / Invocation / Decision Semantics 不变形；Findings 不授权；Plan 默认 advisory；Decision 才 authorizes | `test_prism4_core.py` / `test_prism4_use_cases.py` |
| Adapter Contract | local-file / json adapter 的持久化边界；Relation roundtrip；`references/` 不升 Artifact；Brief 只投影 current state | `test_prism4_local_files.py` / `test_prism4_projection.py` |
| CLI Surface Contract | 用户入口、record 参数、JSON surface、legacy 入口退休 | `test_prism4_cli.py` |
| Install / Release Contract | `setup` 后命中当前 SDK；版本元数据一致；分发包可启动；doctor 可做最小健康检查 | `test_setup_smoke.py` / `test_install_e2e.py` / `test_release_metadata.py` |
| Docs / Active Surface Contract | 活文档不漂回 3.x；公开叙事不泄露私有路径；authority / evolution 口径一致 | `test_docs_active_surface.py` |

## 发布门禁

版本提升或分发前至少跑：

```bash
uv run pytest
uv run python bin/release_gate.py --json
bin/doctor --scope cli
prism --version
```

若只改文档叙事，至少跑：

```bash
uv run --with pytest python -m pytest tests/test_docs_active_surface.py tests/test_release_metadata.py
```

若只改安装、分发、寻址，至少跑：

```bash
uv run --with pytest python -m pytest tests/test_setup_smoke.py tests/test_install_e2e.py tests/test_prism4_cli.py -k "doctor or setup or version or install"
```

## 新增测试规则

- 一个反馈沉淀一个最小 invariant，不复制完整人工过程。
- 能在 use case / adapter 层测清楚的，不升级成 CLI e2e。
- CLI 测试只证明参数能抵达语义层、用户入口不会误导。
- e2e 只守安装包能启动、doctor 能过、版本正确。
- 避免大段 golden text；只断言关键字段、关系、路径和少量提示语。
- 任何新增测试都要能回答：它防的是 Core 漂移、Adapter 漏洞、CLI 误导、安装失败，还是文档叙事回潮？
