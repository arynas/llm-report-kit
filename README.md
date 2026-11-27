# llm-report-kit

Turn public GDELT news headlines into a PowerPoint and PDF with figures, links, and layout checks. The demo uses the public Social Listening MCP adapter to compute the facts. It runs without an LLM account, an API key, or a running MCP server.

## Install

Use Python 3.11 or newer and install [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/). On Linux, `soffice` or `libreoffice` must be on `PATH`. The installer fetches dependencies from PyPI and the pinned public Social Listening MCP source from GitHub.

From the project root in a terminal on macOS or Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/llm-report-kit fetch-data --data-dir data
```

`fetch-data` downloads about 11 MB from the [public snapshot release](https://github.com/arynas/Social-Listening-MCP/releases/tag/data-2026-10-v2) and verifies the SHA-256 digests of the archives and the extracted files. You can run it again to verify the local copies. The snapshot covers 1 September through 14 October 2026 in Asia/Jakarta time.

## Krakatau pilot

```sh
.venv/bin/llm-report-kit outline --data-dir data --keyword Krakatau \
  --start 2026-09-01 --end 2026-09-14 --out runs/krakatau-outline
cat runs/krakatau-outline/outline.md
```

The outline has four slides. Review the dates, the 1,976 headlines, the peak of 733 on 6 September, and the coverage warning for the previous period. Pass the reviewed inputs to `build` to approve them for rendering. The command recomputes and compares the facts against the verified snapshot before export.

```sh
.venv/bin/llm-report-kit build --data-dir data \
  --inputs runs/krakatau-outline/report-inputs.json --out runs/krakatau
```

The output folder contains `outline.md`, `report-inputs.json`, `report.pptx`, `report.pdf`, and `check_report.json`. The checker verifies the displayed total and peak, the 14 editable chart values, the links and slide count, and common text layout errors. A failed check exits with its findings. Use a fresh output path for each build.

## Out-of-coverage case

With the same snapshot, request 18–31 August 2026:

```sh
.venv/bin/llm-report-kit outline --data-dir data --keyword Krakatau \
  --start 2026-08-18 --end 2026-08-31 --out runs/out-of-coverage-outline
cat runs/out-of-coverage-outline/outline.md
.venv/bin/llm-report-kit build --data-dir data \
  --inputs runs/out-of-coverage-outline/report-inputs.json --out runs/out-of-coverage
.venv/bin/python tests/smoke.py runs/krakatau runs/out-of-coverage
```

This report has one slide explaining the missing coverage. The check report records `data_available: false`, a `null` total, and zero chart points.

## Examples and limits

| Case | Outline | PowerPoint | PDF | Check report |
| --- | --- | --- | --- | --- |
| Krakatau | [Outline](examples/krakatau/outline.md) | [PPTX](examples/krakatau/report.pptx) | [PDF](examples/krakatau/report.pdf) | [JSON](examples/krakatau/check_report.json) |
| Out of coverage | [Outline](examples/out-of-coverage/outline.md) | [PPTX](examples/out-of-coverage/report.pptx) | [PDF](examples/out-of-coverage/report.pdf) | [JSON](examples/out-of-coverage/check_report.json) |

The slides are in Indonesian. The snapshot contains headlines and article links. Headline volume describes the coverage of this dataset. Article link targets are checked against the snapshot, so the demo can run without visiting the article sites.

The layout checks cover text overlap, clipping, small text, and slide bounds. Review the finished deck visually for issues such as an object covering a chart. The CLI uses local rules for verification.

Data from the [GDELT Project](https://www.gdeltproject.org/). The [release datasheet](https://github.com/arynas/Social-Listening-MCP/releases/download/data-2026-10-v2/datasheet.md) describes the source data and its limitations. The MIT license covers the kit's code. The dataset retains its source attribution and [GDELT terms](https://gdeltproject.org/about.html).
