#!/usr/bin/env python3
"""prism-workflow-review 预探测脚本 — 嗅探项目目录环境，输出结构化 JSON 供 Agent 消费。

用法: uv run python sniff.py <project_dir> [--topic <主题名>]

参数:
  project_dir       - 项目根目录
  --topic <主题名>  - 评审主题（可选），用于 affinity 与 review 编号推导

输出 JSON 字段:
  project_dir       - 输入的项目目录（绝对路径）
  workspace         - Prism Workspace 信息（null 表示未找到）
  obsidian          - Obsidian 环境信息
  prism             - Prism SDK 上下文（device_id / workspace_root / projects）
  output_dir        - 已解析的 3.0 topic 根目录；未定位时为 null（须边界澄清门）
  reviews_dir       - 已解析的 reviews/ 目录；未定位时为 null
  boundary_clarification_required - next_review_source=none 时为 true
  writable          - output_dir 可写（未定位时为 false）
  format            - "ofm" | "standard"
  route             - "deep" | "short"
  topic             - 评审主题（null 表示未提供）
  topic_affinity    - 专项亲和检测结果
    .suggestion     - "cohesion" | "ask_user" | "new_topic"
  structures        - 3.0 结构层探测（present / task_index / tasks[] / task_count）
"""

import json
import os
import sys

from sniff_lib import (
    find_workspace,
    find_obsidian,
    find_prism_context,
    _find_topics_dir,
    detect_topic_affinity,
    resolve_review_output_dir,
    enumerate_reviews,
    enumerate_structures,
    check_review_density,
    check_writable,
    next_review_number_for_topic,
    resolve_topic_reviews_dir,
)


def sniff(project_dir: str, topic: str | None = None) -> dict:
    project_dir = os.path.abspath(project_dir)

    # 版本校验
    import sniff_lib
    if not hasattr(sniff_lib, "__version__"):
        print("警告: sniff_lib.py 缺少 __version__，可能为过期副本", file=sys.stderr)

    workspace = find_workspace(project_dir)
    obsidian = find_obsidian(
        workspace["path"] if workspace else project_dir,
        project_dir=project_dir,
    )
    prism = find_prism_context(project_dir)

    topic_affinity = None
    if topic and workspace:
        topics_dir = _find_topics_dir(workspace["path"])
        topic_affinity = detect_topic_affinity(topics_dir, topic)

    # 自动计算下一个 review 编号
    # 修复: 旧实现用 `project_dir/reviews`，当 project_dir 是仓库根（而非 topic 子目录）时
    # 会恒返回 r01，造成对已有 reviews/r03 的 topic 重复从 r01 起新。
    # 新实现通过 topic_affinity.matched_topic 定位正确的 topic/reviews/ 目录。
    next_review_number, next_review_source = next_review_number_for_topic(
        project_dir, workspace, topic_affinity, topic_hint=topic
    )

    # review 密度告警：基于定位到的正确 reviews/ 目录
    review_density_warning = None
    reviews_dir_resolved, _ = resolve_topic_reviews_dir(
        project_dir, workspace, topic_affinity, topic_hint=topic
    )
    if reviews_dir_resolved:
        review_density_warning = check_review_density(reviews_dir_resolved)

    # 3.0 结构层探测：从已解析的 topic 目录识别 structures/ + task 层 + .tN 编码
    # topic_dir = reviews/ 的父级；未解析到则回退 project_dir 自身
    if reviews_dir_resolved:
        resolved_topic_dir = os.path.dirname(reviews_dir_resolved)
    else:
        resolved_topic_dir = project_dir
    structures = enumerate_structures(resolved_topic_dir)

    # AP-41 / 029 r07 — 稀疏空态可消费语义化（empty_reason 枚举）
    # 让消费者能区分「合法空态」与「实现/参数路径问题」
    empty_reason = _compute_empty_reason(
        workspace=workspace,
        topic=topic,
        topic_affinity=topic_affinity,
        next_review_source=next_review_source,
    )

    output_dir, reviews_dir = resolve_review_output_dir(
        project_dir, workspace, topic_affinity, topic_hint=topic
    )
    boundary_clarification_required = next_review_source == "none"
    writable = bool(output_dir and check_writable(output_dir))
    fmt = "ofm" if obsidian["detected"] else "standard"
    route = "deep" if workspace and writable else "short"

    return {
        "project_dir": project_dir,
        "workspace": workspace,
        "obsidian": obsidian,
        "prism": prism,
        "output_dir": output_dir,
        "reviews_dir": reviews_dir,
        "boundary_clarification_required": boundary_clarification_required,
        "writable": writable,
        "format": fmt,
        "route": route,
        "topic": topic,
        "topic_affinity": topic_affinity,
        "next_review_number": next_review_number,
        "next_review_source": next_review_source,  # "affinity" | "topic_hint" | "project_dir" | "none"
        "review_density_warning": review_density_warning,
        "empty_reason": empty_reason,
        "structures": structures,  # V4：3.0 结构层（structures/ + task 层 + .tN）
    }


# ============================================================
# AP-41 — 稀疏空态语义化（029/r07 / d07 OQ-1 落地）
# ============================================================

# empty_reason 枚举（按检测优先级，前者更"根本"）：
#   null                          — 非空态，正常工作（workspace + topic + 强亲和）
#   "no_workspace_bridge"         — 项目根没找到 workspace.*.local / ai-task.local 桥接
#                                   （消费者 hint：先 ln -s 桥接 vault，或换其他项目根）
#   "topic_not_specified"         — workspace 存在但未提供 --topic
#                                   （topic_affinity 必为 null；非 bug，但 affinity 路由不可用）
#   "topic_affinity_unavailable"  — workspace + topic 都给了但 topic_affinity 仍为 null
#                                   （workspace 内可能没 topics/ 子目录）
#   "affinity_low_confidence"     — topic_affinity 命中但 strength=low/none
#                                   （建议消费者按 ask_user 提示用户确认 topic）

EMPTY_REASONS = (
    "no_workspace_bridge",
    "topic_not_specified",
    "topic_affinity_unavailable",
    "affinity_low_confidence",
)


def _compute_empty_reason(
    workspace: dict | None,
    topic: str | None,
    topic_affinity: dict | None,
    next_review_source: str,
) -> str | None:
    """根据 sniff 各组件结果推算稀疏原因。返回 None 表示非空态。"""
    if workspace is None:
        return "no_workspace_bridge"
    if topic is None:
        return "topic_not_specified"
    if topic_affinity is None:
        return "topic_affinity_unavailable"
    strength = topic_affinity.get("affinity_strength")
    if strength in ("low", "none"):
        return "affinity_low_confidence"
    return None


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="prism-workflow-review 预探测脚本",
        usage="uv run python sniff.py <project_dir> [--topic <主题名>]",
    )
    parser.add_argument("project_dir", help="项目根目录")
    parser.add_argument("--topic", default=None, help="评审主题（可选），用于 affinity 与编号推导")

    args = parser.parse_args()

    if not os.path.isdir(args.project_dir):
        print(f"错误: {args.project_dir} 不是有效目录", file=sys.stderr)
        sys.exit(1)

    result = sniff(args.project_dir, topic=args.topic)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
