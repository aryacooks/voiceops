# Build the final report

The canonical source is `report.html` in this directory; the submission PDF is `../report.pdf`. Fonts, CSS and vector figures are embedded, so the report needs no network connection to print. The older `report.md` is retained as a historical draft and is not used by the builder.

From the repository root:

```sh
python scripts/build_report.py
```

The report-only build requires Node.js, Playwright, Chromium or Google Chrome, and pypdf for PDF metadata/page validation. Use `uv run --with pypdf scripts/build_report.py` if pypdf is not installed; the Codex bundled Python is detected automatically when available. This does not add Node.js to the voice agent's grading dependencies. A local Playwright installation, `PLAYWRIGHT_NODE_MODULES`, or the Codex bundled runtime is supported. Set `REPORT_BROWSER_CHANNEL=chrome` to use installed Chrome; otherwise install Playwright's Chromium with its usual browser installer.

The builder verifies four page sections, embedded fonts, footer bounds, horizontal overflow and content overflow before printing A4. The builder then verifies four A4 PDF pages and sets author/title metadata. Selectable text and rendered page images are checked separately during authoring. Report evidence and qualifications are in `REPORT_EVIDENCE.md` and `evidence_manifest.json`.
