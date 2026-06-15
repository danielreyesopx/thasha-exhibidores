# Thasha Exhibidores — Project Reference for Agents

## Overview
Static catalog website for jewelry display products (exhibidores de joyería). Single-page catalog with 4 product categories, image lightbox, and responsive bento-grid layout. Deployed on Netlify.

**Live URL:** https://heartfelt-pie-691c2a.netlify.app  
**Netlify Site ID:** `ee1dde23-de2a-4d94-afdf-842e55ef27aa`  
**Netlify Project:** `heartfelt-pie-691c2a`

---

## Tech Stack
- **Frontend:** Pure HTML + CSS + vanilla JS (no framework, no build step)
- **Hosting:** Netlify (static site, no functions/build)
- **Python:** AI inpainting pipeline to remove text/price overlays from images (IOPaint + EasyOCR). Use the generalized `remove_text.py` tool for new work; `auto_process.py` is the legacy project-specific version. See "Removing Text From Images" below.
- **Python runtime:** `py -3.12` or `venv\Scripts\python.exe`

---

## Project Structure

```
Thasha Ehibidores/
├── index.html              ← Main catalog (identical to catalogo.html)
├── catalogo.html           ← Duplicate of index.html (keep synced)
├── auto_process.py         ← Removes price text from images (IOPaint + EasyOCR)
├── deploy.ps1              ← Netlify deploy script (single source of truth)
├── AGENTS.md               ← This file
├── CLAUDE.md               ← Concise pointer for Claude Code sessions
│
├── Exhibidores de joyeria fina/      ← 15 images  (SOURCE/backup, not served)
├── Exhibidores de joyeria negro/     ← 35 images  (SOURCE/backup, not served)
├── Exhibidores de joyeria gris/      ← 11 images  (SOURCE/backup, not served)
├── Exhibidores de Yute/              ← 21 images  (SOURCE/backup, not served)
│
├── Exhibidores de joyeria fina - sin precio/   ← LIVE images (price-removed, served)
├── Exhibidores de joyeria negro - sin precio/  ← LIVE images
├── Exhibidores de joyeria gris - sin precio/   ← LIVE images
├── Exhibidores de Yute - sin precio/           ← LIVE images
│
├── .netlify/                ← Netlify deploy config (gitignored)
├── .netlifyignore           ← Excludes venv/.git/originals from deploy
├── .gitignore               ← Excludes venv, _work dirs (sin-precio dirs ARE tracked)
├── venv/                    ← Python venv with iopaint, easyocr, torch (42K+ files!)
└── .github/                 ← GitHub config
```

---

## Design System (UI-UX-Pro-Max, applied 2026-06-15)

> **Note:** This table describes the *current* state of `index.html`. It is not a spec to enforce — if the design changes, update or delete this section rather than treating it as a contract.

| Property | Value |
|----------|-------|
| **Palette** | Primary: `#1C1917`, Secondary: `#44403C`, Accent/Gold: `#CA8A04`, BG: `#FAFAF9`, Text: `#0C0A09` |
| **Typography** | Cormorant (serif, headings) + Montserrat (sans-serif, body) |
| **Style** | Liquid Glass — product cards with `backdrop-filter: blur()`, gold hover glow |
| **Grid** | Bento-style CSS Grid — `auto-fill, minmax(260px, 1fr)` |
| **Layout** | Hero → Sticky Nav → Category Sections → Footer |
| **Breakpoints** | ≤639px (2 cols), 640–1023px (3 cols), ≥1024px (4 cols), ≥1440px (5 cols) |
| **Font import** | `@import url('https://fonts.googleapis.com/css2?family=Cormorant:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600;700&display=swap')` |

---

## Key Files

### `index.html` / `catalogo.html`
- Both files MUST remain identical. If editing one, copy to the other.
- All CSS is inline in `<style>` tag. All JS is inline at bottom of `<body>`.
- Product images reference the **price-removed** folders, e.g. `Exhibidores de joyeria fina - sin precio/exhibidor.jpg`. Processed images are `.png`; images that had no price kept their original `.jpg`. The original with-price folders are no longer referenced (kept only as source/backup).
- Features: sticky nav with active-tracking, glassmorphism product cards, lightbox with keyboard/touch navigation, SVG zoom-hint icons, `loading="lazy"`, `prefers-reduced-motion` support

### `auto_process.py` (legacy, project-specific)
- Detects maroon price text in product images, masks it, in-paints with IOPaint lama
- Hardcoded to this project's 4 folders. Output goes to `{folder} - sin precio/`
- **Creates a temp `_work/` dir** (with `imgs/`, `masks/`, `res/` subdirs) during processing and deletes it on success. If the script crashes mid-run, `_work/` may linger — it's gitignored and safe to delete manually.
- Requires `venv/` with IOPaint, EasyOCR, OpenCV, torch (CPU mode)
- Run: `py -3.12 auto_process.py`  or  `py -3.12 auto_process.py "Exhibidores de Yute"`
- Warning: slow — runs IOPaint on CPU. Process one folder at a time for reliability.
- **Superseded by the generalized `remove_text.py` tool below** for new work. Keep
  this script only as the record of how this catalog was first processed.

---

## Local Preview

No build step — just open the HTML file or serve it:

```powershell
# Option 1: open directly (images load via relative paths)
start index.html

# Option 2: local HTTP server (useful for testing on other devices)
py -3.12 -m http.server 8000
# Then open http://localhost:8000
```

---

## Removing Text From Images — Generalized Tool

A reusable, generalized version of `auto_process.py` lives outside this repo. **Use
it for any new text-removal work** (new product photos, watermarks, captions): it is
color-agnostic, caps mask size so it can never paint over the product, and
self-verifies the result with OCR.

- **Script:** `~/.claude/skills/remove-image-text/scripts/remove_text.py`
  (alongside `SKILL.md` and `references/tuning.md` documenting it). On Windows the
  home path is `C:\Users\Dankai Films\.claude\skills\remove-image-text\`.
- **OpenCode has no Skill tool — run the script directly.** This project's `venv/`
  already has every dependency it needs (IOPaint, EasyOCR, OpenCV, torch), so use
  that python; no separate setup required.

```powershell
$py    = "venv\Scripts\python.exe"
$skill = "$env:USERPROFILE\.claude\skills\remove-image-text\scripts\remove_text.py"

# a whole folder (Spanish + English text)
& $py $skill "Exhibidores de Yute" --lang es en

# specific files / custom output dir
& $py $skill img1.jpg img2.jpg --out "D:\clean" --lang es en

# boost recall for a stubborn brand font colour (maroon ~ RGB 90,40,40)
& $py $skill "Exhibidores de Yute" --color 90,40,40:50 --lang es en
```

- **How it works:** EasyOCR locates the text (any font/color) → tight, text-shaped
  masks (NOT loose rectangles — those smear/ghost nearby product edges) → IOPaint
  `lama` inpaints only those pixels → re-OCR verifies, widening and retrying if text
  survives. Output goes to a new `<input> - no text` folder; **originals untouched.**
- **Flags:** `--out DIR`, `--lang es en` (EasyOCR codes), `--color R,G,B[:tol]`
  (repeatable brand-color booster), `--device cpu|cuda|mps` (default cpu).
- **Always verify after a batch:** read the console summary for `MANUAL` / "review
  manually" lines and spot-check a few outputs for leftover text or over-erased
  edges. See `references/tuning.md` for calibrating a `--color`.

---

## Deploy Instructions

**Do NOT deploy from the project root.** The `venv/` folder has 42K+ files and will cause timeouts.

### Method: `deploy.ps1` (single source of truth)

`deploy.ps1` builds a clean `_deploy/` staging dir from the file list defined inside it, runs `ntl deploy --no-build`, then cleans up. The file list lives in **one place only** — edit `$DeployItems` at the top of `deploy.ps1` if the deploy set changes.

```powershell
.\deploy.ps1           # production deploy
.\deploy.ps1 -Draft    # draft/preview deploy
```

**Netlify auth:** `ntl deploy` uses credentials stored by `ntl login` (interactive OAuth, cached in `~/.netlify/config.json` on first run). If a deploy fails with an auth error, run `ntl login` in a terminal, then retry.

### What goes to Netlify (and only this)
`index.html`, `catalogo.html`, and the 4 **`Exhibidores de * - sin precio`** (price-removed) image directories — those are what the catalog references. Everything else — `venv/`, `.git/`, `auto_process.py`, `deploy.ps1`, the **original with-price** dirs, `_work/` — is excluded. The `--no-build` flag is essential; this is a static site with no build step. If you add a product folder, add its `- sin precio` counterpart to `$DeployItems` in `deploy.ps1`.

---

## Git Rules
- **.gitignore** excludes: `.netlify`, `venv/`, `_work/`, `_masks_yute/`, `_to_inpaint_yute/`, `.git/`, `.github/`, `.netlifyignore`. The **`- sin precio/` dirs are tracked** (they are the live catalog images) — do not ignore them.
- Commit: `index.html`, `catalogo.html`, the `- sin precio` image dirs (live), the original image dirs (source/backup), `auto_process.py`, `deploy.ps1`, `.gitignore`, `.netlifyignore`, `.netlify/netlify.toml`, `AGENTS.md`, `CLAUDE.md`
- Both `index.html` and `catalogo.html` must be committed together if changed

---

## Known Gotchas

1. **venv size:** `venv/` contains torch, IOPaint, EasyOCR — 42K+ files. Never deploy it. Never scan it recursively (will hang).
2. **index.html = catalogo.html:** Always keep them in sync. Copy one to the other after edits.
3. **Image paths use spaces:** Paths like `Exhibidores de joyeria fina/exhibidor multi -uso_1.jpg` — be careful with URL encoding if moving files.
4. **Netlify deploy timeout:** Deploying from root hangs. Always use `.\deploy.ps1` (builds a clean staging dir).
5. **Python version:** Only `py -3.12` works. `python`/`python3` not in PATH on this machine.
6. **Lightbox images array:** Built dynamically from `.product-card img` selectors at page load. If product HTML changes, lightbox auto-updates.
7. **Nav sticky offset:** Category sections have `offsetTop - 180` for active-state detection. Adjust if hero/nav sizes change.

---

## Future Work Ideas
- Add actual product codes/SKUs to cards
- Add WhatsApp/contact CTA button
- Convert to Netlify CMS-managed content (product data as JSON)
- Optimize images (WebP, responsive srcset)
- Add search/filter capability
