"""Config checker:  python -m app.llm.check

Validates config/llm.yaml, then makes one tiny live call per distinct model so
you find out immediately whether the model id and thinking level are accepted,
instead of discovering it on the first user request.

Pass --offline to validate the file without calling the API.
"""

from __future__ import annotations

import argparse
import sys

from app.llm.config import KNOWN_ROLES, LLMConfigError, get_llm_settings
from app.llm.factory import MissingAPIKeyError, get_llm, require_api_key
from app.settings import LLM_CONFIG_FILE

OK = "  ok  "
BAD = " FAIL "


def _list_available_models(limit: int = 40) -> list[str]:
    """Best-effort listing of model ids visible to this API key."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=require_api_key())
        ids = sorted(model.id for model in client.models.list())
    except Exception:  # noqa: BLE001 - purely advisory output
        return []
    return ids[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the LLM configuration.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Only parse and validate the config; do not call the OpenAI API.",
    )
    args = parser.parse_args()

    print(f"Config file: {LLM_CONFIG_FILE}\n")

    # --- 1. Parse and validate -----------------------------------------
    try:
        resolved = {role: get_llm_settings(role) for role in KNOWN_ROLES}
    except LLMConfigError as exc:
        print(f"[{BAD}] {exc}")
        return 1

    print("Resolved settings per agent:")
    for settings in resolved.values():
        print(f"  - {settings.describe()}")
    print()

    if args.offline:
        print(f"[{OK}] Config is valid. (Skipped the live API check.)")
        return 0

    # --- 2. Confirm the key exists -------------------------------------
    try:
        require_api_key()
    except MissingAPIKeyError as exc:
        print(f"[{BAD}] {exc}")
        return 1
    print(f"[{OK}] OPENAI_API_KEY found.")

    # --- 3. One live call per distinct model ---------------------------
    failures: list[str] = []
    for model in sorted({s.model for s in resolved.values()}):
        role = next(r for r, s in resolved.items() if s.model == model)
        try:
            get_llm(role).invoke("Reply with the single word: ready")
        except Exception as exc:  # noqa: BLE001 - report any provider error verbatim
            print(f"[{BAD}] {model}: {type(exc).__name__}: {exc}")
            failures.append(model)
        else:
            print(f"[{OK}] {model}: reachable.")

    if not failures:
        print("\nAll good - the backend is ready to serve requests.")
        return 0

    print(
        f"\n{len(failures)} model(s) failed. If the error mentions an unknown or "
        f"unavailable model, edit `defaults.model` in {LLM_CONFIG_FILE}."
    )
    available = _list_available_models()
    if available:
        print("\nModel ids visible to this API key (first 40):")
        for model_id in available:
            print(f"  - {model_id}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
