#!/usr/bin/env python3
"""Workflow reference link integrity smoke tests."""

import os


SDK_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def test_workflow_review_context_pack_reference_resolves():
    ref = os.path.join(
        SDK_ROOT,
        "skills",
        "workflow",
        "workflow-review",
        "references",
        "context-pack-spec.md",
    )
    assert os.path.exists(ref)
