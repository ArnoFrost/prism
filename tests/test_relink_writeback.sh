#!/usr/bin/env bash
# relink _relink_writeback_path 健壮性测试
#
# 运行: bash tests/test_relink_writeback.sh
#
# 覆盖场景:
#   1. 纯注释 paths 段（模板默认状态）→ 应在注释下方追加，不产生重复 paths:
#   2. 已有 map 条目 → 在段末追加
#   3. 已有当前设备条目 → 跳过（幂等性）
#   4. 无 paths 段 → 追加新段
#   5. paths 段在文件末尾（无后续 key）→ 正确追加
#   6. list 格式 → 转为 map
#   7. device_id 含连字符

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PRISM_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

PASS=0
FAIL=0
TOTAL=0

assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  ((TOTAL++)) || true
  if [[ "$expected" == "$actual" ]]; then
    echo -e "  ${GREEN}✓${NC} ${desc}"
    ((PASS++)) || true
  else
    echo -e "  ${RED}✗${NC} ${desc}"
    echo -e "    ${YELLOW}期望:${NC}"
    echo "$expected" | sed 's/^/    /'
    echo -e "    ${YELLOW}实际:${NC}"
    echo "$actual" | sed 's/^/    /'
    ((FAIL++)) || true
  fi
}

assert_count() {
  local desc="$1" pattern="$2" file="$3" expected_count="$4"
  ((TOTAL++)) || true
  local actual_count
  actual_count=$(grep -c "$pattern" "$file" 2>/dev/null || echo 0)
  if [[ "$actual_count" -eq "$expected_count" ]]; then
    echo -e "  ${GREEN}✓${NC} ${desc} (${pattern} 出现 ${actual_count} 次)"
    ((PASS++)) || true
  else
    echo -e "  ${RED}✗${NC} ${desc}: 期望 ${pattern} 出现 ${expected_count} 次，实际 ${actual_count} 次"
    echo -e "    ${YELLOW}文件内容:${NC}"
    cat "$file" | sed 's/^/    /'
    ((FAIL++)) || true
  fi
}

# 导入 _relink_writeback_path 函数（通过 awk 提取完整函数体，含嵌套花括号）
eval "$(awk '/^_relink_writeback_path\(\)/{found=1} found{print; if(/^}$/){exit}}' "$PRISM_DIR/bin/relink")"

TMPDIR_BASE=$(mktemp -d)
trap "rm -rf $TMPDIR_BASE" EXIT

# ───────────────────────────────────────────
echo ""
echo "═══ relink _relink_writeback_path 健壮性测试 ═══"

# ─── 测试 1: 纯注释 paths 段（模板默认状态）───
echo ""
echo "─── 测试 1: 纯注释 paths 段 ───"
T1_FILE="$TMPDIR_BASE/t1_project.yaml"
cat > "$T1_FILE" << 'EOF'
code: "TEST"
name: "Test Project"
paths:
  # {DEVICE_ID}: /path/to/project

task_naming:
  format: "full"
EOF
_relink_writeback_path "$T1_FILE" "MC2" "/Users/arno/test"
assert_count "paths: 只出现 1 次" "^paths:" "$T1_FILE" 1
assert_count "MC2 条目存在" "  MC2: " "$T1_FILE" 1

# ─── 测试 2: 已有 map 条目 ───
echo ""
echo "─── 测试 2: 已有 map 条目 ───"
T2_FILE="$TMPDIR_BASE/t2_project.yaml"
cat > "$T2_FILE" << 'EOF'
code: "TEST"
paths:
  MC1: /Users/other/test

task_naming:
  format: "full"
EOF
_relink_writeback_path "$T2_FILE" "MC2" "/Users/arno/test"
assert_count "paths: 只出现 1 次" "^paths:" "$T2_FILE" 1
assert_count "MC1 保留" "  MC1: " "$T2_FILE" 1
assert_count "MC2 新增" "  MC2: " "$T2_FILE" 1

# ─── 测试 3: 幂等性（已有当前设备条目）───
echo ""
echo "─── 测试 3: 幂等性 ───"
T3_FILE="$TMPDIR_BASE/t3_project.yaml"
cat > "$T3_FILE" << 'EOF'
code: "TEST"
paths:
  MC2: /Users/arno/test

task_naming:
  format: "full"
EOF
T3_BEFORE=$(cat "$T3_FILE")
_relink_writeback_path "$T3_FILE" "MC2" "/Users/arno/test"
T3_AFTER=$(cat "$T3_FILE")
assert_eq "文件内容不变" "$T3_BEFORE" "$T3_AFTER"

# ─── 测试 4: 无 paths 段 ───
echo ""
echo "─── 测试 4: 无 paths 段 ───"
T4_FILE="$TMPDIR_BASE/t4_project.yaml"
cat > "$T4_FILE" << 'EOF'
code: "TEST"
name: "Test Project"

task_naming:
  format: "full"
EOF
_relink_writeback_path "$T4_FILE" "MC2" "/Users/arno/test"
assert_count "新增 paths: 段" "^paths:" "$T4_FILE" 1
assert_count "MC2 条目存在" "  MC2: " "$T4_FILE" 1

# ─── 测试 5: paths 段在文件末尾 ───
echo ""
echo "─── 测试 5: paths 段在文件末尾 ───"
T5_FILE="$TMPDIR_BASE/t5_project.yaml"
cat > "$T5_FILE" << 'EOF'
code: "TEST"
paths:
  MC1: /Users/other/test
EOF
_relink_writeback_path "$T5_FILE" "MC2" "/Users/arno/test"
assert_count "paths: 只出现 1 次" "^paths:" "$T5_FILE" 1
assert_count "MC2 在末尾追加" "  MC2: " "$T5_FILE" 1

# ─── 测试 6: list 格式 ───
echo ""
echo "─── 测试 6: list 格式转 map ───"
T6_FILE="$TMPDIR_BASE/t6_project.yaml"
cat > "$T6_FILE" << 'EOF'
code: "TEST"
paths:
  - /Users/other/test

task_naming:
  format: "full"
EOF
_relink_writeback_path "$T6_FILE" "MC2" "/Users/arno/test"
assert_count "paths: 只出现 1 次" "^paths:" "$T6_FILE" 1
assert_count "MC2 条目存在" "  MC2: " "$T6_FILE" 1
assert_count "旧 list 条目转为注释" "# (legacy)" "$T6_FILE" 1

# ─── 测试 7: device_id 含连字符 ───
echo ""
echo "─── 测试 7: device_id 含连字符 ───"
T7_FILE="$TMPDIR_BASE/t7_project.yaml"
cat > "$T7_FILE" << 'EOF'
code: "TEST"
paths:

task_naming:
  format: "full"
EOF
_relink_writeback_path "$T7_FILE" "MY-MAC-BOOK" "/Users/arno/test"
assert_count "paths: 只出现 1 次" "^paths:" "$T7_FILE" 1
assert_count "含连字符的 device_id 正确写入" "  MY-MAC-BOOK: " "$T7_FILE" 1

# ─── 测试 8: 二次写入幂等 ───
echo ""
echo "─── 测试 8: 二次写入幂等 ───"
T8_FILE="$TMPDIR_BASE/t8_project.yaml"
cat > "$T8_FILE" << 'EOF'
code: "TEST"
paths:
  # 注释

task_naming:
  format: "full"
EOF
_relink_writeback_path "$T8_FILE" "MC2" "/Users/arno/test"
_relink_writeback_path "$T8_FILE" "MC2" "/Users/arno/test"
assert_count "二次写入后 MC2 只出现 1 次" "  MC2: " "$T8_FILE" 1
assert_count "paths: 只出现 1 次" "^paths:" "$T8_FILE" 1

# ═══ 汇总 ═══
echo ""
echo "═════════════════════════════════"
echo -e "  总计: ${TOTAL}  ${GREEN}通过: ${PASS}${NC}  ${RED}失败: ${FAIL}${NC}"
if [[ $FAIL -gt 0 ]]; then
  echo -e "  ${RED}存在失败测试！${NC}"
  exit 1
else
  echo -e "  ${GREEN}✓ 全部通过${NC}"
fi
