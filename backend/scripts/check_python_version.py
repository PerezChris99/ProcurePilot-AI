"""Minimal Windows launcher preflight, with no shell-sensitive inline expressions."""
import sys

if __name__ == "__main__":
    if sys.version_info < (3, 12):
        print(
            "ProcurePilot AI requires Python 3.12 or newer; detected "
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        raise SystemExit(1)
    print(
        f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
