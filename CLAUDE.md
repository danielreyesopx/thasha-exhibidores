# CLAUDE.md — Thasha Exhibidores

Static catalog website for jewelry display products (exhibidores de joyería).
Single-page catalog with 4 product categories, image lightbox, and a responsive
bento-grid layout. Pure HTML/CSS/vanilla JS — no framework, no build step.
Hosted on Netlify.

- **Live URL:** https://heartfelt-pie-691c2a.netlify.app
- **Netlify Site ID:** `ee1dde23-de2a-4d94-afdf-842e55ef27aa`
- **Netlify Project:** `heartfelt-pie-691c2a`

---

## Critical rules (do not break)

1. **`index.html` and `catalogo.html` are byte-identical.** After editing either,
   copy it over the other and commit both together. Never let them drift.
2. **Never deploy or recursively scan `venv/`.** It holds 42K+ files (torch, IOPaint,
   EasyOCR) and will hang or time out. Deploy from a clean `_deploy/` staging folder only
   (see Deploy below).
3. **Python is `py -3.12` only.** `python` / `python3` are not on PATH on this machine.
4. **Folder and file names contain spaces** (e.g. `Exhibidores de joyeria fina/`).
   Always quote paths; use `-LiteralPath` in PowerShell.

---

## Tech stack

- **Frontend:** Pure HTML + CSS + vanilla JS. All CSS is inline in a `<style>` tag;
  all JS is inline at the bottom of `<body>`. No build step.
- **Hosting:** Netlify (static site, no functions, no build).
- **Image pipeline:** AI inpainting to remove text/price overlays (IOPaint lama +
  EasyOCR + OpenCV + torch, CPU mode). Use the reusable **`remove-image-text` skill**
  for new work; `auto_process.py` is the legacy project-specific version. See
  "Removing text from images" below.
- **Python runtime:** `py -3.12`, or `venv\Scripts\python.exe`.

---

## Project structure

```
Thasha Ehibidores/
├── index.html              ← Main catalog
├── catalogo.html           ← Byte-identical duplicate of index.html (keep synced)
├── auto_process.py         ← Removes price text from images (IOPaint + EasyOCR)
│
├── Exhibidores de joyeria fina/      ← 15 images  (SOURCE/backup, not served)
├── Exhibidores de joyeria negro/     ← 35 images  (SOURCE/backup, not served)
├── Exhibidores de joyeria gris/      ← 11 images  (SOURCE/backup, not served)
├── Exhibidores de Yute/              ← 21 images  (SOURCE/backup, not served)
│
├── Exhibidores de joyeria fina - sin precio/   ← LIVE images (price-removed)
├── Exhibidores de joyeria negro - sin precio/  ← LIVE images
├── Exhibidores de joyeria gris - sin precio/   ← LIVE images
├── Exhibidores de Yute - sin precio/           ← LIVE images
│
├── .netlify/               ← Netlify deploy config (gitignored)
├── .netlifyignore          ← Excludes venv/.git/etc. from deploy
├── .gitignore
├── venv/                   ← Python venv: iopaint, easyocr, torch (42K+ files!)
└── .github/                ← GitHub config
```

---

## Key files

### `index.html` / `catalogo.html`
- Must remain identical. Edit one, copy to the other.
- Product images use relative paths into the price-removed folders, e.g.
  `Exhibidores de joyeria fina - sin precio/exhibidor.jpg` (note: processed images
  are `.png`, unprocessed ones kept their original `.jpg`).
- Features: sticky nav with active-section tracking, glassmorphism product cards,
  lightbox with keyboard/touch navigation, SVG zoom-hint icons, `loading="lazy"`,
  `prefers-reduced-motion` support.
- **Lightbox images array** is built dynamically from `.product-card img` at page load —
  if product HTML changes, the lightbox updates automatically.
- **Nav sticky offset** uses `offsetTop - 180` for active-state detection. Adjust if
  hero/nav sizes change.

### `auto_process.py` (legacy, project-specific)
- Detects maroon price text in product images, masks it, in-paints with IOPaint lama.
- Hardcoded to this project's 4 folders; output goes to `{folder} - sin precio/`.
- Requires the `venv/` (IOPaint, EasyOCR, OpenCV, torch in CPU mode).
- Run: `py -3.12 auto_process.py`  or  `py -3.12 auto_process.py "Exhibidores de Yute"`.
- Slow — runs IOPaint on CPU. Process one folder at a time for reliability.
- **Superseded by the `remove-image-text` skill below** for any new work. Keep this
  script only as the record of how this catalog was first processed.

---

## Removing text from images — use the `remove-image-text` skill

There is a reusable, global skill that generalizes `auto_process.py`. **Prefer it**
for any new text-removal work (new product photos, watermarks, captions, other
projects) — it is color-agnostic, has safety caps so it can never paint over the
product, and self-verifies with OCR.

- **Skill location:** `C:\Users\Dankai Films\.claude\skills\remove-image-text\`
  (`SKILL.md`, `scripts/remove_text.py`, `references/tuning.md`).
- **When it triggers:** automatically when asked to remove text/prices/watermarks
  from images — e.g. "remove the price from these photos", "clean the watermark
  off these", "take the text out of these catalog pics". You can also invoke it
  explicitly with the `Skill` tool (`remove-image-text`).
- **How it works:** EasyOCR finds the text (any font/color) → tight, text-shaped
  masks (NOT big rectangles — those caused the ghosting we hit early on) →
  IOPaint `lama` inpaints only those pixels → re-OCR verifies and retries wider if
  text survives. Output goes to a new `<input> - no text` folder; **originals are
  never touched.**
- **This project's `venv/` already has every dependency the skill needs**, so just
  run its script with that python (no separate setup):

  ```powershell
  $py    = "venv\Scripts\python.exe"
  $skill = "$env:USERPROFILE\.claude\skills\remove-image-text\scripts\remove_text.py"

  # a whole folder (Spanish + English text)
  & $py $skill "Exhibidores de Yute" --lang es en

  # specific files / custom output
  & $py $skill img1.jpg img2.jpg --out "D:\clean" --lang es en

  # boost recall for a stubborn brand font colour (maroon ~ RGB 90,40,40)
  & $py $skill "Exhibidores de Yute" --color 90,40,40:50 --lang es en
  ```

- **Always verify after a batch:** check the console summary for `MANUAL` / "review
  manually" lines, then spot-check a few outputs for leftover fragments or
  over-erased edges. See the skill's `references/tuning.md` for calibrating a
  `--color` and other tuning.

---

## Design system (current state, last updated 2026-06-15)

Descriptive of what the catalog currently uses — not a spec to enforce.

| Property | Value |
|----------|-------|
| **Palette** | Primary `#1C1917`, Secondary `#44403C`, Accent/Gold `#CA8A04`, BG `#FAFAF9`, Text `#0C0A09` |
| **Typography** | Cormorant (serif, headings) + Montserrat (sans-serif, body) |
| **Style** | Liquid Glass — product cards with `backdrop-filter: blur()`, gold hover glow |
| **Grid** | Bento-style CSS Grid — `auto-fill, minmax(260px, 1fr)` |
| **Layout** | Hero → Sticky Nav → Category Sections → Footer |
| **Breakpoints** | ≤639px (2 cols), 640–1023px (3 cols), ≥1024px (4 cols), ≥1440px (5 cols) |

Font import:
```
@import url('https://fonts.googleapis.com/css2?family=Cormorant:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600;700&display=swap')
```

---

## Local preview

No server needed for a quick look — open `index.html` in a browser.
To serve over HTTP (so relative paths and lazy-loading behave like prod):

```powershell
py -3.12 -m http.server 8080
# then open http://localhost:8080/index.html
```

---

## Deploy

**Do NOT deploy from the project root** — `venv/` (42K+ files) causes timeouts.
Use the `deploy.ps1` script — it is the single source of truth for what ships
(stages a clean `_deploy/` dir, deploys with `--no-build`, cleans up):

```powershell
.\deploy.ps1          # production
.\deploy.ps1 -Draft   # draft / preview URL
```

The catalog references the **`- sin precio` (price-removed) image folders**, so those
are the image folders `deploy.ps1` stages — NOT the original with-price folders. If you
add a product image folder, add its `- sin precio` counterpart to `$DeployItems` in
`deploy.ps1`.

**Never ships:** `venv/`, `.git/`, `.netlify/`, `.github/`, `auto_process.py`,
`deploy.ps1`, `AGENTS.md`, `CLAUDE.md`, the **original with-price** folders, any
`_work`/`_masks`/`_to_inpaint` dirs. (Enforced by `.netlifyignore` + `deploy.ps1`.)

---

## Git rules

- The **`- sin precio/` folders are tracked** — they are the live catalog images.
  Do not gitignore them. `.gitignore` excludes only: `.netlify`, `venv/`, `_work/`,
  `_masks_yute/`, `_to_inpaint_yute/`, `.github/`, `.netlifyignore`.
- The original with-price folders are kept as the source for reprocessing. They are
  committed but no longer referenced by the site.
- `index.html` and `catalogo.html` must be committed together whenever either changes.

---

## Gotchas

1. **venv size:** never deploy it, never scan it recursively (will hang).
2. **index = catalogo:** keep them in sync after every edit.
3. **Spaces in paths:** quote everything; watch URL encoding when moving image files.
4. **Netlify deploy timeout:** only the `_deploy/` staging method above works.
5. **Python:** `py -3.12` only.

---

## Future work ideas

- Add product codes/SKUs to cards
- Add WhatsApp/contact CTA button
- Move product data to JSON (Netlify CMS-managed content)
- Optimize images (WebP, responsive `srcset`)
- Add search/filter capability
