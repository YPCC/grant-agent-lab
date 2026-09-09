# How to create demo files

Demo files live in [`docs/demo/`](../demo/). They are **screen recordings** of a real UI walkthrough (not generated clips) plus optional stills.

| File | Source UI | Typical length |
|------|-----------|----------------|
| [`e2e-workbench-demo.mp4`](../demo/e2e-workbench-demo.mp4) | Python workbench `:8765` | ~40s |
| [`e2e-copilotkit-demo.mp4`](../demo/e2e-copilotkit-demo.mp4) | CopilotKit Next.js `:3000` | ~30s |
| `still-*.png` | Same session, key frames | — |

Use **H.264 + yuv420p + faststart**, 1440×900, no audio unless you add a voiceover.

## Prerequisites

```bash
cd grant-agent-lab
python3 -m pip install playwright python-docx
python3 -m playwright install chromium
# ffmpeg must be on PATH (https://ffmpeg.org)
ffmpeg -version | head -1
```

For the CopilotKit recording also:

```bash
cd ui-copilotkit
npm install --legacy-peer-deps
```

No model key is required. Structured DOCX review uses `/api/review` / `review_grant_docx.py`.

## Fast path — recorder script

[`scripts/record_demo.py`](../../scripts/record_demo.py) starts Playwright, walks the UI, writes a WebM, then encodes MP4 + stills into `docs/demo/`.

### 1. Python workbench

Terminal A:

```bash
cd grant-agent-lab
PYTHONPATH=. python3 ui-copilotkit/serve_workbench.py
```

Terminal B:

```bash
PYTHONPATH=. python3 scripts/record_demo.py --target workbench
```

Writes `docs/demo/e2e-workbench-demo.mp4` and stills (`still-review.png`, `still-checklist.png`, `still-office-of-research-aid-rbac.png`).

### 2. CopilotKit Next.js

Terminal A:

```bash
cd grant-agent-lab/ui-copilotkit
GRANT_LAB_ROOT="$(pwd)/.." PYTHONPATH="$(pwd)/.." npm run dev
```

Wait until Next prints `Ready`. Terminal B:

```bash
cd grant-agent-lab
PYTHONPATH=. python3 scripts/record_demo.py --target copilotkit
```

Writes `docs/demo/e2e-copilotkit-demo.mp4` and `still-copilotkit-*.png`.

`--url` overrides the base URL. `--skip-encode` keeps the raw WebM only.

## What each walkthrough must show

**Workbench (`:8765`)**

1. Role **PI**
2. Review sample DOCX (Specific Aims extract + score)
3. Missing Essentials checklist
4. Copilot-style chat: “Review this grant DOCX”
5. HITL **revise** then **approve freeze**
6. Submit disabled for PI
7. Switch role to **Office of Research Aid** → Submit enables (demo only)

**CopilotKit (`:3000`)**

1. CopilotKit workbench + **CopilotSidebar**
2. Review sample DOCX / findings rail
3. Sidebar message box
4. PI Submit disabled
5. Role **Office of Research Aid** → Submit enables

Do **not** record eRA login, passwords, or a live NIH submit.

## Manual recording (OBS / browser)

If you prefer not to use Playwright:

1. Launch the UI ([how to launch](how-to-launch-ui.md)).
2. Capture 1440×900 (or 16:9 then crop).
3. Follow the same beat list above. Speak or use on-screen captions.
4. Export, then encode:

```bash
IN=raw-capture.mov   # or .webm / .mkv
OUT=docs/demo/e2e-workbench-demo.mp4
TMP="${OUT%.*}.tmp.mp4"

ffmpeg -y -i "$IN" \
  -vf "scale=1440:900:force_original_aspect_ratio=decrease,pad=1440:900:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -crf 23 -preset medium -threads 4 \
  -pix_fmt yuv420p -movflags +faststart \
  -an \
  "$TMP"
ffprobe -hide_banner -i "$TMP"
mv "$TMP" "$OUT"
```

Keep files under ~10 MB (GitHub warning ~50 MB, hard limit 100 MB). Raise CRF (`-crf 28`) if needed.

## Stills

Take PNGs at 1440×900 from the same session:

| Still | When |
|-------|------|
| `still-review.png` | After workbench review |
| `still-checklist.png` | Missing Essentials list |
| `still-office-of-research-aid-rbac.png` | Submit enabled for Office of Research Aid |
| `still-copilotkit-review.png` | CopilotKit after review |
| `still-copilotkit-ora.png` | CopilotKit, Office of Research Aid role |

Playwright stills are written automatically by `record_demo.py`. Manual: OS screenshot, or:

```bash
ffmpeg -y -ss 00:00:08 -i docs/demo/e2e-workbench-demo.mp4 -frames:v 1 docs/demo/still-review.png
```

## After recording

1. Confirm playback (browser or `ffplay`).
2. Update [`docs/demo/README.md`](../demo/README.md) if length or beats changed.
3. Commit only `docs/demo/*` (not `node_modules/`, `.next/`, or raw WebM):

```bash
git add docs/demo/*.mp4 docs/demo/*.png docs/demo/README.md
git commit -m "Update UI demo recordings"
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Playwright timeout on Review | Sample DOCX review can take ~10s; wait for `.score` not `—` |
| Copilot sidebar covers HITL buttons | Script hides `.chat` / version-mismatch overlay before clicks |
| CopilotKit 1.70 blank page / `useAgent` error | Pin `@copilotkit/react-core` **1.8.14** (see `ui-copilotkit/package.json`) |
| Next `Can't resolve '@copilotkit/runtime'` | Demo does not need runtime; keep the stub in `app/api/copilotkit/route.ts` |
| `python-docx` missing | `pip install python-docx` |
| MP4 won’t play in browser | Must be `libx264` + `yuv420p` + `-movflags +faststart` |

Launch UIs: [how-to-launch-ui.md](how-to-launch-ui.md).
