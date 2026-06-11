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
    """从 prism.local.yaml 读取 vault_path（简单解析，不引入 PyYAML 依赖）"""
    parsed = parse_prism_local_yaml(yaml_path)
    return parsed.get("vault_path") if parsed else None


def parse_prism_local_yaml(yaml_path: str) -> dict | None:
    """解析 prism.local.yaml 顶层字段和 projects 块。

    与 workspace-init/sniff.py 的同名函数对齐，零 PyYAML 依赖。
    返回 dict 含: device_id, sdk_path, skills_path, vault_path,
    workspace_subdir, projects (dict)。解析失败返回 None。
    """
    result = {
        "device_id": None,
        "sdk_path": None,
        "skills_path": None,
        "vault_path": None,
        "workspace_subdir": None,
        "projects": {},
    }

    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return None

    in_projects = False
    for line in lines:
        stripped = line.rstrip()
        if stripped.lstrip().startswith("#") or not stripped:
            continue

        if stripped == "projects:":
            in_projects = True
            continue

        if in_projects:
            if line[0] != " " and line[0] != "\t":
                in_projects = False
            else:
                m = re.match(r"^\s+([\w-]+):\s*(.+)", stripped)
                if m:
                    result["projects"][m.group(1)] = _strip_yaml_quotes(m.group(2).strip())
                continue

        m = re.match(r"^(\w+):\s*(.+)", stripped)
        if m:
            key, val = m.group(1), _strip_yaml_quotes(m.group(2).strip())
            if key in result and key != "projects":
                result[key] = val

    return result


def parse_workspace_git(yaml_path: str) -> dict:
    """解析 prism.local.yaml 可选块 workspace_git（零 PyYAML 依赖）。

    块缺失时返回 present=False, enabled=False 与默认值。
    enabled 仅接受 true/false 字面量（d03：无 auto）。
    """
    defaults = {
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

        # 退出 workspace_git 块（下一个顶层 key）
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
        val = _strip_yaml_quotes(raw)
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

    return result


def find_prism_context(project_dir: str) -> dict | None:
    """从 prism.local.yaml 构建完整的 Prism 上下文。

    返回 dict 含:
      device_id       - 当前设备标识
      sdk_path        - SDK 路径
      skills_path     - Skills 仓库路径
      vault_path      - Vault 基础路径
      workspace_subdir - Vault 内子目录
      workspace_root  - 计算后的完整 Workspace 根路径
      projects        - 已注册项目 {CODE: local_path}
    找不到 prism.local.yaml 时返回 None。
    """
    yaml_path = _find_prism_local_yaml(project_dir)
    if not yaml_path:
        return None

    parsed = parse_prism_local_yaml(yaml_path)
    if not parsed:
        return None

    workspace_root = None
    if parsed["vault_path"] and parsed["workspace_subdir"]:
        workspace_root = os.path.join(parsed["vault_path"], parsed["workspace_subdir"])

    return {
        "device_id": parsed["device_id"],
        "sdk_path": parsed["sdk_path"],
        "skills_path": parsed["skills_path"],
        "vault_path": parsed["vault_path"],
        "workspace_subdir": parsed["workspace_subdir"],
        "workspace_root": workspace_root,
        "projects": parsed["projects"],
    }


def resolve_workspace_path(prism_context: dict, project_code: str) -> str | None:
    """根据项目代号解析其 Workspace 目录的绝对路径。

    路径 = {workspace_root}/{project_code}/
    仅在目录实际存在时返回，否则返回 None。
    """
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
