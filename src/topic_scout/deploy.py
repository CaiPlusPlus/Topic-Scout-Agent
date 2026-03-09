from __future__ import annotations

import argparse
import os

from .repository import Repository
from .web import serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the deployment web server")
    parser.add_argument("--host", default=os.getenv("TOPIC_SCOUT_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", os.getenv("TOPIC_SCOUT_PORT", "8000"))))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    host = args.host
    port = args.port
    serve(Repository(), host=host, port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
