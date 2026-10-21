"""Submit a JSONL assessment dataset to the running CARI API."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--api", default="http://127.0.0.1:8010")
    args = parser.parse_args()

    submitted = 0
    failures = 0
    for line in args.dataset.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        request = Request(
            f"{args.api.rstrip('/')}/assess",
            data=json.dumps(json.loads(line)).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request) as response:
                if response.status == 200:
                    submitted += 1
                else:
                    failures += 1
        except Exception as exc:
            failures += 1
            print(f"Failed assessment on line {submitted + failures}: {exc}")
    print(f"Submitted: {submitted}; failures: {failures}")


if __name__ == "__main__":
    main()
