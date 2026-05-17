import os
import stat
import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_DIR / "scripts"
SCRIPT_NAMES = (
    "_common.sh",
    "start_server.sh",
    "status.sh",
    "start_dry_run.sh",
    "tick.sh",
    "stop_dry_run.sh",
    "analyze.sh",
    "smoke_check.sh",
)


def _script_texts() -> dict[str, str]:
    return {name: (SCRIPTS_DIR / name).read_text(encoding="utf-8") for name in SCRIPT_NAMES}


def test_all_scripts_exist():
    for name in SCRIPT_NAMES:
        assert (SCRIPTS_DIR / name).is_file(), f"missing script: {name}"


def test_all_scripts_are_executable():
    for name in SCRIPT_NAMES:
        mode = (SCRIPTS_DIR / name).stat().st_mode
        assert mode & stat.S_IXUSR, f"script is not user-executable: {name}"


def test_all_scripts_have_shebang():
    for name, text in _script_texts().items():
        assert text.startswith("#!/usr/bin/env bash"), f"missing bash shebang: {name}"


def test_all_scripts_pass_bash_syntax_check():
    for name in SCRIPT_NAMES:
        subprocess.run(["bash", "-n", str(SCRIPTS_DIR / name)], check=True)


def test_common_forces_safe_env_defaults():
    common = (SCRIPTS_DIR / "_common.sh").read_text(encoding="utf-8")
    assert "export TRADING_MODE=paper" in common
    assert "export LIVE_TRADING_ENABLED=false" in common
    assert "export ALLOW_MARKET_ORDERS=false" in common
    assert "export KIS_ORDER_DRY_RUN=true" in common


def test_no_script_prints_or_reads_secret_values():
    forbidden_fragments = (
        "cat .env",
        "grep .env",
        "echo $KIS_APP_KEY",
        "echo ${KIS_APP_KEY",
        "echo $KIS_APP_SECRET",
        "echo ${KIS_APP_SECRET",
        "echo $KIS_ACCOUNT_NO",
        "echo ${KIS_ACCOUNT_NO",
        "access_token",
        "refresh_token",
    )
    for name, text in _script_texts().items():
        for forbidden in forbidden_fragments:
            assert forbidden not in text, f"{name} contains forbidden fragment: {forbidden}"


def test_no_script_uses_git_or_pip():
    forbidden_commands = ("git commit", "git push", "git merge", "pip install")
    for name, text in _script_texts().items():
        for forbidden in forbidden_commands:
            assert forbidden not in text, f"{name} contains forbidden command: {forbidden}"


def test_start_server_uses_localhost_only():
    text = (SCRIPTS_DIR / "start_server.sh").read_text(encoding="utf-8")
    assert "127.0.0.1" in text
    assert "0.0.0.0" not in text


def test_scripts_directory_not_ignored_by_gitignore():
    assert not os.popen(f"git check-ignore -q {SCRIPTS_DIR / 'status.sh'}; echo $?").read().strip() == "0"
