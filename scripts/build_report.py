"""Build the canonical HTML report: python scripts/build_report.py.

Requires Node.js, Playwright and Chromium/Chrome for this report-only build.
The grading pipeline itself remains Python-only. See report/BUILD.md.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def finalize(output: Path):
    try:
        from pypdf import PdfReader, PdfWriter
    except ModuleNotFoundError:
        raise SystemExit('Report metadata checks require pypdf. Run: uv run --with pypdf scripts/build_report.py')
    reader = PdfReader(output)
    if len(reader.pages) != 4:
        raise SystemExit(f'Expected four PDF pages, found {len(reader.pages)}.')
    for page in reader.pages:
        if abs(float(page.mediabox.width) - 595.28) > 1 or abs(float(page.mediabox.height) - 841.89) > 1:
            raise SystemExit('The report must use A4 portrait pages.')
    writer = PdfWriter(clone_from=reader)
    writer.add_metadata({'/Title': 'ZentroMart VoiceOps - Capstone Report',
                         '/Author': 'Arya Bysani · IIT Guwahati',
                         '/Subject': 'Implementation, evaluation and lessons from a grounded voice support agent',
                         '/Keywords': 'VoiceOps, ZentroMart, Gnani, RAG, capstone',
                         '/Creator': 'VoiceOps report builder'})
    with tempfile.NamedTemporaryFile(suffix='.pdf', dir=output.parent, delete=False) as handle:
        temporary = Path(handle.name)
        writer.write(handle)
    temporary.replace(output)
    print(f'Verified four A4 pages and set report author metadata: {output}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'report/report.html')
    parser.add_argument('--output', type=Path, default=ROOT / 'report.pdf')
    parser.add_argument('--finalize-only', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.finalize_only:
        finalize(args.output.resolve())
        return 0
    if not args.source.is_file() or args.source.suffix.lower() != '.html':
        parser.error('The canonical source is report/report.html; supply an existing HTML file.')
    node = shutil.which('node')
    if not node:
        parser.error('Node.js is required for report rendering. See report/BUILD.md.')
    result = subprocess.run([node, str(ROOT / 'scripts/print_report.cjs'),
                             str(args.source.resolve()), str(args.output.resolve())], check=False)
    if result.returncode:
        return result.returncode
    finalize(args.output.resolve())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
