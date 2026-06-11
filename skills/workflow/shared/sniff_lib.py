#!/usr/bin/env python3
"""prism-workflow 共享嗅探库 facade — 向后兼容 `import sniff_lib`。

子模块：sniff_workspace / sniff_routing / sniff_reviews / sniff_structures。
零外部依赖，纯 stdlib。
"""

__version__ = "1.2.0"

import os
import sys

_PKG_DIR = os.path.dirname(os.path.realpath(__file__))
if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)

import sniff_reviews as _sniff_reviews
import sniff_routing as _sniff_routing
import sniff_structures as _sniff_structures
import sniff_workspace as _sniff_workspace

for _mod in (_sniff_workspace, _sniff_routing, _sniff_reviews, _sniff_structures):
    for _name in dir(_mod):
        if _name.startswith("__"):
            continue
        globals()[_name] = getattr(_mod, _name)
