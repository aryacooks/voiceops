"""Create an allowlisted submission bundle; refuse missing deliverables by default."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = ("README.md", ".env.example", ".gitignore", "requirements.txt", "requirements-dev.txt",
         "pyproject.toml", "pytest.ini", "run.py", "build_index.py", "app.py", "report.pdf", "demo.mp4")
FOLDERS = ("src", "eval", "report", "docs", "sample_outputs", "scripts", "tests")
REQUIRED = ("README.md", ".env.example", "requirements.txt", "run.py", "src/zentro/agent.py",
            "report.pdf", "demo.mp4")
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".venv", "dataset", "index", ".git"}


def package(output: Path, allow_incomplete: bool = False) -> dict:
    missing = [name for name in REQUIRED if not (ROOT / name).is_file()]
    if not any((ROOT / "sample_outputs").glob("*.reply.wav")):
        missing.append("sample_outputs/<recording>.reply.wav (real Gnani output)")
    if missing and not allow_incomplete:
        raise SystemExit("Submission is incomplete. Missing: " + ", ".join(missing))
    paths = [ROOT / name for name in FILES if (ROOT / name).is_file()]
    for folder in FOLDERS:
        paths.extend(path for path in (ROOT / folder).rglob("*") if path.is_file())
    manifest = {
        "status": "incomplete_source_bundle" if missing else "deliverables_present",
        "missing_deliverables": missing,
        "note": "Presence checks do not certify correctness, live evaluation or voice quality. See report.pdf and eval/results/.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(set(paths)):
            relative = path.relative_to(ROOT)
            if any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            if path.name.startswith(".env") and path.name != ".env.example":
                continue
            if path.suffix in {".pyc", ".pyo", ".zip"} or path.name == ".DS_Store":
                continue
            archive.write(path, str(relative))
        archive.writestr("BUNDLE_STATUS.json", json.dumps(manifest, indent=2) + "\n")
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert ".env" not in names and not any(name.startswith("dataset/") for name in names)
    print(f"Created {output}: {len(names)} files, {manifest['status']}")
    if missing:
        print("Missing: " + ", ".join(missing))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "team_name_voiceops.zip")
    parser.add_argument("--allow-incomplete", action="store_true", help="Create a clearly labelled source bundle even when voice/demo artifacts are unavailable.")
    args = parser.parse_args()
    package(args.output, args.allow_incomplete)
