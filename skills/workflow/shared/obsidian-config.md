# Obsidian 共享配置

> 被多个 skill 引用的 Obsidian vault 路径探测规范和格式约定。
> 引用方式：skill 的 `references/obsidian-config.md` 软链指向此文件。

## 路径探测

Prism 环境下，vault 路径优先从 `prism.local.yaml` 读取：

```
1. 检查项目根目录 prism.local.yaml → vault_path
2. 若不存在 → 尝试环境变量 OBSIDIAN_AI_VAULT
3. 若仍无 → 尝试默认 iCloud 路径（见下表）
4. 展开 ~ 为绝对路径
5. 检查目录是否存在（ls 或 stat）
6. 若不存在 → 告知用户路径无效，请求提供正确路径
```

不要假设路径一定存在。iCloud 同步可能导致目录暂时不可达。

## 默认路径参考

| 用途 | macOS 路径 | 环境变量覆盖 |
|------|-----------|-------------|
| iCloud 基准 | `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/` | `OBSIDIAN_ICLOUD_BASE` |
| AI vault | `$OBSIDIAN_ICLOUD_BASE/AI Obsidian` | `OBSIDIAN_AI_VAULT` |

## CLAUDE.md / AGENTS.md 探测

部分 vault 根目录包含规范文件：
- 若存在 → 优先遵循其中的目录结构和命名规则
- 若不存在 → 使用下方默认规范

## Prism 默认 callout（G0 · OFM v2）

> **SSOT 分层**：本节 = 全仓**默认 callout 词汇**；`format=ofm` 二态与 vault frontmatter 见 sniff / `validate_product`；**评审协议段 + Findings 映射**见 `review/references/review-ofm.md`（仅 `rXX_*.md` 主报告）。

跨端优先 [GitHub Alerts](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts)（GFM 五类）。Obsidian 与 Android Studio 2025.3.4+ 对五类均为全样式渲染；Obsidian-only 扩展在 IDE 预览中多为半样式。

| GFM 类型 | 典型用途（非强制） |
|----------|-------------------|
| `NOTE` | 元信息、改善建议、协议段（review 须置顶，见 review-ofm） |
| `TIP` | TL;DR、结论、建议性行动 |
| `IMPORTANT` | 阻塞 / P0 级发现 |
| `WARNING` | 重要 / P1 级发现 |
| `CAUTION` | 风险、与 WARNING 同族（慎用 Obsidian-only 别名） |

**v1 兼容别名**（新产物不推荐，validator 仍接受）：`info` / `abstract` / `danger` / `warning` / `note` / `success` / `tip` / `warn`。

人类速查：[docs/ofm-cheatsheet.md](../../../docs/ofm-cheatsheet.md)。

### 格式原则（G0）

- Callout 类型**大小写不敏感**
- 跨端产物**禁止** GFM 类型上的 Obsidian 折叠修饰（`[!note]-` / `[!quote]+`）
- 每个章节最多 1–2 个 callout，不过度装饰
- 高亮 `==文本==` 每段最多 1-2 处
- 表格优于嵌套列表
- 中英文之间加空格
- Frontmatter 必须包含 `date`、`status`、`type`、`tags`

## 链接规范

Prism workspace 文件在 Obsidian vault 中存在大量同名文件（`intake.md`、`scope.md`、`r01.md` 等），
vault 默认 `newLinkFormat = shortest` 无法正确解析。遵循以下规则：

| 场景 | 格式 | 示例 |
|------|------|------|
| **专项内互引**（同专项目录下） | Markdown 相对链接 | `[scope](./scope.md)`、`[R1](./reviews/r01.md)` |
| **跨专项引用** | `[[NNN_topic-name]]` wikilink | `[[001_push-notification-guide]]` |
| **跨项目引用** | `[[项目/NNN_topic]]` wikilink | `[[TVKMM/001_push-notification-guide]]` |
| **frontmatter `related:`** | 相对路径字符串（非 wikilink） | `"./reviews/r01.md"` |

### 核心原则

- **通用文件名不用 wikilink**：`intake.md`、`scope.md`、`focus.md`、`r01.md`、`d01.md` 在 vault 内不唯一，必须用相对路径
- **专项目录名可以用 wikilink**：`{NNN}_{topic-name}/` 有编号前缀，vault 内唯一
- **README 导航栏统一用相对链接**：`[intake](./intake.md)`、`[R1](./reviews/r01.md)`
- **不要在 wikilink 里写子路径**：`[[dir/file]]` 会被 Obsidian 按 vault 根解析，几乎必定创建新文件

### Mermaid 语法规范

- 边标签必须紧贴箭头，不加空格：`-->|标签|`，而非 `--> |标签|`（带空格会导致 Obsidian 渲染失败）
- 节点文字避免以 `/` 开头（如 `/sync`），改用无斜杠形式，防止解析歧义
- 节点文本不要写成 `1. xxx`、`2. xxx` 这类列表前缀，改用 `S1`、`Step 1`、`①`
- 节点文字中**禁止使用 `\n` 做视觉换行**，应使用 `<br>`。原因：`\n` 在 Mermaid Live Editor 中可渲染，但在 Obsidian 内置渲染器中行为不一致，`<br>` 是跨渲染器兼容的安全选择
