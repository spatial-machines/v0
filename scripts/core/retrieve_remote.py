from __future__ import annotations

import argparse
import json
from datetime import datetime, UTC
from pathlib import Path
from urllib.parse import urlparse

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def infer_name(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name or "downloaded-file"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download a remote file into data/raw and write a manifest."
    )
    parser.add_argument("--url", required=True, help="URL to download")
    parser.add_argument("--label", default=None, help="Output filename (default: inferred from URL)")
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory (default: data/raw/)"
    )
    args = parser.parse_args()

    url = args.url
    output_name = args.label if args.label else infer_name(url)

    raw_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else RAW_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest = raw_dir / output_name

    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            with dest.open("wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            content_type = response.headers.get("content-type")
            content_length = response.headers.get("content-length")

    manifest = {
        "dataset_id": dest.stem,
        "retrieval_method": "http-download",
        "source_name": output_name,
        "source_type": "remote-file",
        "source_url": url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "stored_path": str(dest.resolve().relative_to(PROJECT_ROOT)),
        "format": dest.suffix.lower().lstrip("."),
        "geography_level": None,
        "vintage": None,
        "notes": [f"content-type: {content_type}", f"content-length: {content_length}"],
        "warnings": [],
    }

    out = raw_dir / f"{dest.stem}.manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"downloaded {url} -> {dest}")
    print(f"manifest {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
