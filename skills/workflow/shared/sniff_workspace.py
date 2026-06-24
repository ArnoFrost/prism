"""Workspace / yaml / obsidian / prism context 探测。"""
import os
import re
from datetime import date
from glob import glob

def _workspace_info(path: str, ws_type: str | None = None) -> dict:
    """构造 workspace 元数据，保留调用路径中的 symlink 语义。"""
    name = os.path.basename(os.path.normpath(path))
    resolved_type = ws_type or ("ai-task" if "ai-task" in name else "prism")
    return {
        "path": os.path.abspath(path),
        "type": resolved_type,
        "project_yaml": os.path.isfile(os.path.join(path, "project.yaml")),
        "readme": os.path.isfile(os.path.join(path, "README.md")),
    }


def _looks_like_workspace_root(path: str) -> bool:
    """判断当前路径本身是否已经是 Prism workspace 根。"""
    return (
        os.path.isfile(os.path.join(path, "project.yaml"))
        and (
            os.path.isdir(os.path.join(path, "topics"))
            or os.path.isdir(os.path.join(path, "tasks"))
        )
    )


def find_workspace(project_dir: str) -> dict | None:
    """查找 Prism Workspace 或 ai-task.local。

    支持三类入口：
    1. 仓库根目录下存在 `workspace.*.local` / `ai-task.local`
    2. 传入路径本身已经是 workspace 根
    3. 传入路径位于 workspace 下方的 topic / 子目录内
    """
    current = os.path.abspath(project_dir)
    for _ in range(30):
        if _looks_like_workspace_root(current):
            return _workspace_info(current)

        for pattern in ["workspace.*.local", "ai-task.local"]:
            matches = glob(os.path.join(current, pattern))
            for m in matches:
                if os.path.isdir(m):
                    ws_type = "ai-task" if "ai-task" in os.path.basename(m) else "prism"
                    return _workspace_info(m, ws_type)

        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def _check_vault(path: str) -> dict | None:
    """检查给定路径是否为有效的 Obsidian vault（含 .obsidian/ 目录）"""
    expanded = os.path.expanduser(path)
    obsidian_dir = os.path.join(expanded, ".obsidian")
    if os.path.isdir(obsidian_dir):
        return {"detected": True, "vault_root": os.path.abspath(expanded)}
    return None


def _find_prism_local_yaml(project_dir: str) -> str | None:
    """查找 prism.local.yaml：项目目录 → ~/prism/ → 家目录"""
    candidates = [
        os.path.join(project_dir, "prism.local.yaml"),
        os.path.expanduser("~/prism/prism.local.yaml"),
        os.path.expanduser("~/prism.local.yaml"),
        os.path.expanduser("~/.prism.local.yaml"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _strip_yaml_quotes(value: str) -> str:
    """去除 YAML 值的引号包裹"""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or \
           (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return value


def _read_vault_path_from_yaml(yaml_path: str) -> str | None:
    """从 prism.local.yaml 读取协作树物理根（d02 双读 workspace_root / vault_path）。"""
    parsed = parse_prism_local_yaml(yaml_path)
    if not parsed:
        return None
    return resolve_prism_local_paths(parsed).get("storage_root")


def _expand_config_path(path: str | None) -> str | None:
    """展开 yaml 中的 ~ 为用户主目录绝对路径（relink/bash 不展开变量内 ~）。"""
    if not path:
        return None
    return os.path.normpath(os.path.expanduser(path))


def _workspace_git_defaults() -> dict:
    return {
        "present": False,
        "enabled": False,
        "branch": "master",
        "remote": "origin",
        "debounce_seconds": 300,
        "interval_minutes": 0,
        "large_file_mb": 20,
        "notify_on_success": False,
        "notify_on_block": True,
        "schedule": [],
    }


def _apply_workspace_git_field(result: dict, key: str, raw: str) -> None:
    val = _strip_yaml_quotes(raw.strip())
    if key == "enabled":
        result["enabled"] = val.lower() == "true"
    elif key in ("notify_on_success", "notify_on_block"):
        result[key] = val.lower() == "true"
    elif key == "branch" and val:
        result["branch"] = val
    elif key == "remote" and val:
        result["remote"] = val
    elif key in ("debounce_seconds", "interval_minutes", "large_file_mb") and val.isdigit():
        result[key] = int(val)


def parse_prism_local_yaml(yaml_path: str) -> dict | None:
    """解析 prism.local.yaml 顶层字段、workspaces 块与 projects 块。

    零 PyYAML 依赖。projects 值可为 string（legacy）或 {path, workspace} object。
    workspaces 块缺失时 workspaces={}，由 parse_workspaces 合成 flat work。
    """
    result = {
        "device_id": None,
        "sdk_path": None,
        "skills_path": None,
        "vault_path": None,
        "workspace_root": None,
        "workspace_subdir": None,
        "obs_vault": None,
        "obs_vault_personal": None,
        "default_workspace": None,
        "workspaces": {},
        "projects": {},
    }

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return None

    section: str | None = None
    ws_id: str | None = None
    in_ws_git = False
    in_ws_git_schedule = False
    project_code: str | None = None

    top_keys = set(result.keys()) - {"workspaces", "projects"}

    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue

        if line[0] not in (" ", "\t"):
            section = None
            ws_id = None
            in_ws_git = False
            in_ws_git_schedule = False
            project_code = None

            if stripped == "workspaces:":
                section = "workspaces"
                continue
            if stripped == "projects:":
                section = "projects"
                continue

            m = re.match(r"^(\w+):\s*(.*)$", stripped)
            if m:
                key, val = m.group(1), _strip_yaml_quotes(m.group(2).strip())
                if key in top_keys:
                    result[key] = val
            continue

        if section == "workspaces":
            m_id = re.match(r"^  ([\w-]+):\s*$", stripped)
            if m_id:
                ws_id = m_id.group(1)
                result["workspaces"][ws_id] = {
                    "workspace_root": None,
                    "workspace_subdir": None,
                    "workspace_git": _workspace_git_defaults(),
                }
                in_ws_git = False
                in_ws_git_schedule = False
                continue

            if ws_id and re.match(r"^    workspace_git:\s*$", stripped):
                in_ws_git = True
                in_ws_git_schedule = False
                result["workspaces"][ws_id]["workspace_git"]["present"] = True
                continue

            if in_ws_git and ws_id:
                if in_ws_git_schedule:
                    m_item = re.match(r'^\s+-\s*["\']?([^"\']+)["\']?\s*$', stripped)
                    if m_item:
                        result["workspaces"][ws_id]["workspace_git"]["schedule"].append(
                            m_item.group(1).strip()
                        )
                        continue
                    if re.match(r"^\s+\w", stripped) and not stripped.strip().startswith("- "):
                        in_ws_git_schedule = False
                    else:
                        continue

                m_wg = re.match(r"^      (\w+):\s*(.*)$", stripped)
                if m_wg:
                    key, raw = m_wg.group(1), m_wg.group(2)
                    wg = result["workspaces"][ws_id]["workspace_git"]
                    if key == "schedule" and raw.strip() == "":
                        in_ws_git_schedule = True
                        continue
                    _apply_workspace_git_field(wg, key, raw)
                continue

            if ws_id:
                m_field = re.match(r"^    (\w+):\s*(.+)$", stripped)
                if m_field:
                    key, val = m_field.group(1), _strip_yaml_quotes(m_field.group(2).strip())
                    if key in ("workspace_root", "workspace_subdir"):
                        result["workspaces"][ws_id][key] = val
            continue

        if section == "projects":
            m_inline = re.match(r"^  ([\w-]+):\s*(.+)$", stripped)
            if m_inline:
                code, val = m_inline.group(1), _strip_yaml_quotes(m_inline.group(2).strip())
                result["projects"][code] = val
                project_code = None
                continue

            m_obj = re.match(r"^  ([\w-]+):\s*$", stripped)
            if m_obj:
                project_code = m_obj.group(1)
                result["projects"][project_code] = {}
                continue

            if project_code:
                m_sub = re.match(r"^    (\w+):\s*(.+)$", stripped)
                if m_sub:
                    key, val = m_sub.group(1), _strip_yaml_quotes(m_sub.group(2).strip())
                    result["projects"][project_code][key] = val
            continue

    return result


def parse_workspace_git(yaml_path: str) -> dict:
    """解析 prism.local.yaml 可选块 workspace_git（零 PyYAML 依赖）。

    块缺失时返回 present=False, enabled=False 与默认值。
    enabled 仅接受 true/false 字面量（d03：无 auto）。
    """
    defaults = _workspace_git_defaults()
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return dict(defaults)

    result = dict(defaults)
    in_block = False
    in_schedule = False

    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue

        if not in_block:
            if re.match(r"^workspace_git:\s*$", stripped):
                in_block = True
                result["present"] = True
            continue

        # 退出顶层 workspace_git 块（下一个顶层 key）
        if line[0] not in (" ", "\t"):
            break

        if in_schedule:
            m_item = re.match(r'^\s+-\s*["\']?([^"\']+)["\']?\s*$', stripped)
            if m_item:
                result["schedule"].append(m_item.group(1).strip())
                continue
            if re.match(r"^\s+\w", stripped) and not stripped.strip().startswith("- "):
                in_schedule = False
            else:
                continue

        m = re.match(r"^\s+(\w+):\s*(.*)$", stripped)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if key == "schedule" and raw == "":
            in_schedule = True
            continue
        _apply_workspace_git_field(result, key, raw)

    return result


def _normalize_project_entry(value: str | dict | None, default_workspace: str) -> dict | None:
    if value is None:
        return None
    if isinstance(value, dict):
        path = value.get("path")
        workspace = value.get("workspace") or default_workspace
        if not path:
            return None
        return {"path": path, "workspace": workspace}
    if isinstance(value, str) and value:
        return {"path": value, "workspace": default_workspace}
    return None


def parse_workspaces(parsed: dict | None, yaml_path: str | None = None) -> dict[str, dict]:
    """解析命名 workspaces；无 workspaces 块时合成 flat work（Phase A 双读）。"""
    if not parsed:
        return {}

    if parsed.get("workspaces"):
        out: dict[str, dict] = {}
        for wid, ws in parsed["workspaces"].items():
            root = _expand_config_path(ws.get("workspace_root"))
            sub = ws.get("workspace_subdir")
            pwr = os.path.join(root, sub) if root and sub else None
            out[wid] = {
                "workspace_root": root,
                "workspace_subdir": sub,
                "prism_workspace_root": pwr,
                "workspace_git": dict(ws.get("workspace_git") or _workspace_git_defaults()),
            }
        return out

    paths = resolve_prism_local_paths(parsed)
    wg = parse_workspace_git(yaml_path) if yaml_path else _workspace_git_defaults()
    storage = _expand_config_path(paths["storage_root"])
    subdir = paths["workspace_subdir"]
    pwr = os.path.join(storage, subdir) if storage and subdir else None
    return {
        "work": {
            "workspace_root": storage,
            "workspace_subdir": subdir,
            "prism_workspace_root": pwr,
            "workspace_git": wg,
        }
    }


def resolve_project_binding(
    parsed: dict | None,
    code: str,
    yaml_path: str | None = None,
) -> dict | None:
    """按 CODE 解析 workspace 绑定与 instance_path（d04 Phase C）。"""
    if not parsed:
        return None
    default_ws = parsed.get("default_workspace") or "work"
    raw = parsed.get("projects", {}).get(code)
    norm = _normalize_project_entry(raw, default_ws)
    if not norm:
        return None

    workspaces = parse_workspaces(parsed, yaml_path)
    ws_id = norm["workspace"]
    ws = workspaces.get(ws_id)
    if not ws or not ws.get("prism_workspace_root"):
        return None

    pwr = ws["prism_workspace_root"]
    instance_path = os.path.join(pwr, code) if pwr else None
    return {
        "code": code,
        "path": _expand_config_path(norm["path"]) or norm["path"],
        "workspace_id": ws_id,
        "storage_root": ws.get("workspace_root"),
        "workspace_subdir": ws.get("workspace_subdir"),
        "prism_workspace_root": pwr,
        "instance_path": instance_path,
        "workspace_git": ws.get("workspace_git"),
    }


def resolve_all_project_bindings(
    parsed: dict | None,
    yaml_path: str | None = None,
) -> list[dict]:
    if not parsed:
        return []
    out: list[dict] = []
    for code in parsed.get("projects", {}):
        binding = resolve_project_binding(parsed, code, yaml_path)
        if binding:
            out.append(binding)
    return out


def resolve_prism_local_paths(parsed: dict | None) -> dict:
    """d02 双读：yaml 物理根与 PKM vault 解析为 canonical 路径。

    storage_root       — Prism workspace 协作树物理根（workspace_root 或 vault_path）
    prism_workspace_root — join(storage_root, workspace_subdir)；export PRISM_WORKSPACE
    obs_vault            — PKM Obsidian vault（obs_vault 或 obs_vault_personal）
    """
    empty = {
        "storage_root": None,
        "workspace_subdir": None,
        "prism_workspace_root": None,
        "obs_vault": None,
    }
    if not parsed:
        return dict(empty)

    storage_root = _expand_config_path(
        parsed.get("workspace_root") or parsed.get("vault_path")
    )
    subdir = parsed.get("workspace_subdir")
    prism_workspace_root = None
    if storage_root and subdir:
        prism_workspace_root = os.path.join(storage_root, subdir)

    obs_vault = _expand_config_path(
        parsed.get("obs_vault") or parsed.get("obs_vault_personal")
    )

    return {
        "storage_root": storage_root,
        "workspace_subdir": subdir,
        "prism_workspace_root": prism_workspace_root,
        "obs_vault": obs_vault,
    }


def find_prism_context(project_dir: str) -> dict | None:
    """从 prism.local.yaml 构建完整的 Prism 上下文。

    返回 dict 含:
      device_id            - 当前设备标识
      sdk_path             - SDK 路径
      skills_path          - Skills 仓库路径
      vault_path           - 协作树物理根（deprecated 别名 = storage_root）
      storage_root         - d02 协作树物理根
      workspace_subdir     - 相对子目录
      workspace_root       - 聚合根 prism_workspace_root（workflow 沿用此键）
      prism_workspace_root - 与 workspace_root 相同
      obs_vault            - PKM vault 路径
      projects             - 已注册项目 {CODE: local_path}
    找不到 prism.local.yaml 时返回 None。
    """
    yaml_path = _find_prism_local_yaml(project_dir)
    if not yaml_path:
        return None

    parsed = parse_prism_local_yaml(yaml_path)
    if not parsed:
        return None

    paths = resolve_prism_local_paths(parsed)
    workspaces = parse_workspaces(parsed, yaml_path)
    default_ws = parsed.get("default_workspace") or "work"
    default_root = (workspaces.get(default_ws) or {}).get("prism_workspace_root")
    prism_workspace_root = default_root or paths["prism_workspace_root"]

    return {
        "device_id": parsed["device_id"],
        "sdk_path": parsed["sdk_path"],
        "skills_path": parsed["skills_path"],
        "vault_path": paths["storage_root"],
        "storage_root": paths["storage_root"],
        "workspace_subdir": paths["workspace_subdir"],
        "workspace_root": prism_workspace_root,
        "prism_workspace_root": prism_workspace_root,
        "default_workspace": default_ws,
        "workspaces": workspaces,
        "obs_vault": paths["obs_vault"],
        "projects": parsed["projects"],
        "config_path": yaml_path,
    }


def resolve_workspace_path(
    prism_context: dict,
    project_code: str,
    yaml_path: str | None = None,
) -> str | None:
    """根据项目代号解析其 Workspace 实例目录的绝对路径。

    多 workspace 时按 projects 绑定；否则 {workspace_root}/{CODE}/。
    仅在目录实际存在时返回，否则返回 None。
    """
    cfg = yaml_path or prism_context.get("config_path")
    if cfg and os.path.isfile(cfg):
        parsed = parse_prism_local_yaml(cfg)
        if parsed:
            binding = resolve_project_binding(parsed, project_code, cfg)
            if binding:
                inst = binding["instance_path"]
                return inst if os.path.isdir(inst) else None

    if not prism_context or not prism_context.get("workspace_root"):
        return None
    ws_path = os.path.join(prism_context["workspace_root"], project_code)
    return ws_path if os.path.isdir(ws_path) else None


def find_obsidian(start_dir: str, project_dir: str | None = None) -> dict:
    """多级探测 Obsidian vault，对齐 obsidian-config.md 规范。

    探测优先级：
      1. prism.local.yaml → vault_path
      2. 环境变量 OBSIDIAN_AI_VAULT
      3. iCloud 默认路径 (~/.../iCloud~md~obsidian/Documents/AI Obsidian)
      4. 从 start_dir 向上递归查找 .obsidian/（兜底）
    """
    search_root = project_dir or start_dir

    yaml_path = _find_prism_local_yaml(search_root)
    if yaml_path:
        vault_path = _read_vault_path_from_yaml(yaml_path)
        if vault_path:
            result = _check_vault(vault_path)
            if result:
                return result

    env_vault = os.environ.get("OBSIDIAN_AI_VAULT")
    if env_vault:
        result = _check_vault(env_vault)
        if result:
            return result

    icloud_base = os.environ.get(
        "OBSIDIAN_ICLOUD_BASE",
        os.path.expanduser(
            "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
        ),
    )
    default_vault = os.path.join(icloud_base, "AI Obsidian")
    result = _check_vault(default_vault)
    if result:
        return result

    # 第 4 级兜底：从 start_dir 向上递归找 .obsidian/。
    # 必须用 realpath（解析 symlink），否则通过 `workspace.{code}.local`
    # 软链进入的 vault 子目录无法被识别 —— r02@019 误判 standard 的根因。
    current = os.path.realpath(start_dir)
    for _ in range(20):  # 与 detect_format 对齐，最多 20 层
        candidate = os.path.join(current, ".obsidian")
        if os.path.isdir(candidate):
            return {"detected": True, "vault_root": current}
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    return {"detected": False, "vault_root": None}


def _find_topics_dir(workspace_path: str) -> str:
    """查找专项目录：优先 topics/，fallback 到 tasks/（兼容旧项目）"""
    for name in ("topics", "tasks"):
        d = os.path.join(workspace_path, name)
        if os.path.isdir(d):
            return d
    return os.path.join(workspace_path, "topics")


def check_writable(path: str) -> bool:
    """检查路径是否可写（检查最近的已存在祖先目录）"""
    check = path
    while not os.path.exists(check):
        check = os.path.dirname(check)
        if not check:
            return False
    return os.access(check, os.W_OK)
