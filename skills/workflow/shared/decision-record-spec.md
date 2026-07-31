# Decision Record Contract

> `prism decision record` 的机械写盘合同。CLI 只保存已经由人类确认的治理事件，不判断选择是否正确，也不替代 Clarify、Review 或 Scope。

## 记录门槛

调用方必须同时提供：

1. `--authorized` 与非空 `--authorization-text`，证明用户明确授权正式记录。
2. 一个可审计治理事件：
   - `contract_change`
   - `execution_authorization`
   - `cross_topic`
   - `hard_to_reverse`
   - `long_term_audit`

普通偏好、事实调查、Clarify 推荐和低风险可逆选择默认不调用 record。CLI 只校验调用方声明，不自行判断事件价值。

## 命令

```bash
prism decision record <topic_dir> \
  --title "<标题>" \
  --summary "<摘要>" \
  --decision accept|reject|defer \
  --source clarify|review|explicit_user|execution_boundary \
  --auditable-event <事件类型> \
  --authorized \
  --authorization-text "<用户授权原文>" \
  --idempotency-key "<稳定键>"
```

可选关系参数：

- `--review-ref rXX`：仅 `source=review` 可用，且引用必须唯一存在。
- `--supersedes dXX`
- `--derived-from dXX`
- `--related dXX`

三类 dXX 关系参数可重复，但同一个 dXX 不得同时出现在多种关系中。

## 事务边界

一次成功 record 的主事务包含：

1. 分配下一个 dXX。
2. 写入 `decisions/dXX_<title>.md` 和同族 `decision_artifact`。
3. lazy-create 或追加 `decision.index.md`。

实现使用 topic 级跨进程锁、同目录临时文件、`fsync`、原子替换和异常回滚。任一引用缺失、索引形态未知或替换失败时 fail-closed，不留下新的半成品 dXX/index。

`review.index`、rXX frontmatter、scope/focus 不属于 record 主事务：前两者是可由 tidy/finalize 重建的辅助镜像，后两者必须由 `workflow-scope` 根据已记录决策更新。

## 幂等与断链

- 幂等键在 topic 内唯一，格式为 1–128 位字母数字及 `.`、`_`、`:`、`-`。
- CLI 对规范化后的有效请求计算 SHA-256 `request_fingerprint`；规范化覆盖标题、摘要、裁决、来源、治理事件、授权原文、review 引用和 dXX 关系。
- 相同键、相同请求指纹且 dXX、index、artifact 完整时返回 `idempotent_noop`。
- 相同键但请求指纹不同时返回 `IDEMPOTENCY_PAYLOAD_CONFLICT`，不静默沿用首次结果。
- 相同键对应的 legacy 记录缺少请求指纹时返回 `IDEMPOTENCY_UNVERIFIABLE`，调用方必须换新键或先人工治理旧记录。
- 相同键对应多个 dXX，或任一主链缺失时返回错误，不自动猜测或再写一份。
- rXX/dXX 文件身份只接受精确的 `rXX.md` / `rXX_*.md` 与 `dXX.md` / `dXX_*.md`；`r01` 不得前缀匹配 `r010`，legacy `d01.md` 必须参与引用与后续编号。
- 编号分配在 topic 锁内完成，并发调用不会复用同一 dXX。

## 输出

成功：

```json
{
  "action": "record",
  "status": "recorded",
  "decision_id": "d02",
  "path": "decisions/d02_example.md",
  "index_path": "decision.index.md",
  "idempotency_key": "topic:gate4:r02",
  "timestamp": "2026-07-31T20:30:00+08:00"
}
```

重复调用将 `status` 改为 `idempotent_noop`。`--json` 使用 Prism outer schema；预期失败返回稳定错误码。
