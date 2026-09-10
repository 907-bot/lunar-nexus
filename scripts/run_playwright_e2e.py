#!/usr/bin/env python3
"""Automated Playwright E2E Test Runner for NEXUS-LUNAR.
Executes the full browser automation suite against the dashboard,
asserts zero console errors, captures screenshots for each module,
and produces a formatted execution report.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "playwright_test_results"


def main():
    print("=" * 80)
    print("  NEXUS-LUNAR: PLAYWRIGHT BROWSER AUTOMATION TEST SUITE")
    print("=" * 80)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(PROJECT_ROOT / "tests" / "test_playwright_e2e.py"),
        "-v",
        "-s",
    ]

    print(f"\n[Executing] {' '.join(cmd)}\n")
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    print("\n" + "=" * 80)
    if proc.returncode == 0:
        print("  ✓ ALL PLAYWRIGHT BROWSER AUTOMATION TESTS PASSED")
        print(f"  ✓ High-resolution screenshots saved to: {OUTPUTS_DIR}")
    else:
        print(f"  ✗ PLAYWRIGHT TESTS FAILED WITH EXIT CODE: {proc.returncode}")
    print("=" * 80)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
