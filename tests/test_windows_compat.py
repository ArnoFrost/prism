from pathlib import Path


SDK_ROOT = Path(__file__).resolve().parents[1]


def test_setenv_uses_portable_hostname_helper():
    content = (SDK_ROOT / "bin" / "setenv").read_text(encoding="utf-8")

    assert "prism_short_hostname()" in content
    assert "device_id=$(prism_short_hostname)" in content
    assert "device_id: $(prism_short_hostname)" in content
    assert "device_id=$(hostname -s)" not in content
    assert "device_id: $(hostname -s)" not in content


def test_relink_has_windows_junction_fallback():
    content = (SDK_ROOT / "bin" / "relink").read_text(encoding="utf-8")

    assert "is_windows()" in content
    assert "mklink /D" in content
    assert "mklink /J" in content
    assert "LINK_KIND=\"copy\"" in content
    assert "_can_use_file_copy_fallback()" in content
    assert "MSYS2_ARG_CONV_EXCL='*'" in content
    assert "_windows_reparse_target()" in content
    assert "_is_managed_link" in content


def test_relink_avoids_bsd_only_sed_in_place():
    content = (SDK_ROOT / "bin" / "relink").read_text(encoding="utf-8")

    assert "sed -i ''" not in content
    assert "_trim_trailing_blank_lines" in content


def test_relink_archived_skill_scan_is_opt_in_compat():
    content = (SDK_ROOT / "bin" / "relink").read_text(encoding="utf-8")

    assert "ARCHIVE_COMPAT=false" in content
    assert "PRISM_SCAN_ARCHIVED" in content
    assert "if $ARCHIVE_COMPAT; then" in content
    assert "$ARCHIVE_COMPAT || return" in content
