"""Auto-detect maroon price text, mask it, inpaint with IOPaint, verify.

Rule-based pipeline (replaces hand-drawn rectangle masks):
1. Detect text pixels by calibrated color: dark maroon (R>G+14, R>B+14, R<150, G<115, B<115)
2. Clean specks, dilate to cover antialiased edges, keep components big enough to be text
3. Inpaint only those regions with lama (keeps product pixels intact - no ghosting)
4. Re-detect on output; if text pixels remain, widen mask and retry (max 3 rounds)
"""
import os
import re
import shutil
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

BASE = r"D:\Mis projectos\Thasha Ehibidores"
VENV_PY = os.path.join(BASE, "venv", "Scripts", "python.exe")
WORK = os.path.join(BASE, "_work")

FOLDERS = [
    "Exhibidores de Yute",
    "Exhibidores de joyeria fina",
    "Exhibidores de joyeria gris",
    "Exhibidores de joyeria negro",
]


def text_core(img_rgb: np.ndarray) -> np.ndarray:
    """Boolean mask of pixels matching the maroon font color.

    Calibrated on glyph cores (R~50-90, G/B~25-45). The G/B caps must stay
    well below ~110 or shadowed jute fabric (RGB ~140,110,90) matches too.
    """
    c = img_rgb.astype(int)
    R, G, B = c[..., 0], c[..., 1], c[..., 2]
    return (R > G + 22) & (R > B + 20) & (R < 170) & (G < 85) & (B < 85)


_reader = None


def get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
    return _reader


def ocr_text_boxes(img_rgb: np.ndarray, min_conf: float = 0.3, min_h: int = 22):
    """Text boxes found by EasyOCR, filtered to catalog-text scale.

    Filters: confidence, glyph height (price/title text is large), box not
    absurdly big, and at least 2 real characters (rejects specks read as 'i').
    """
    h, w, _ = img_rgb.shape
    boxes = []
    for pts, txt, conf in get_reader().readtext(img_rgb):
        # '$' + digits is never a false read on these photos; accept low conf
        # (thin charcoal font gets O/0 confusion, e.g. '$6O0/ $550' conf 0.26)
        price_like = re.search(r"\$\s*[\dOo]{2,}", txt)
        if conf < (0.15 if price_like else min_conf):
            continue
        if sum(c.isalnum() or c in "$/" for c in txt) < 2:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, y0, x1, y1 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
        if y1 - y0 < min_h:
            continue
        if (x1 - x0) * (y1 - y0) > 0.2 * w * h:
            continue
        boxes.append((x0, y0, x1, y1, txt, conf))
    return boxes


def neutral_text_core(img_rgb: np.ndarray) -> np.ndarray:
    """Dark glyph pixels inside OCR-confirmed text boxes (any font color)."""
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    out = np.zeros(gray.shape, bool)
    for x0, y0, x1, y1, _txt, _conf in ocr_text_boxes(img_rgb):
        out[y0:y1, x0:x1] |= gray[y0:y1, x0:x1] < 160
    return out


def build_mask(img_rgb: np.ndarray, dilate_px: int = 13, min_area: int = 250) -> np.ndarray | None:
    """Return uint8 inpaint mask (255 = remove) or None if no text found.

    Detection = trusted maroon brand color (anywhere) + dark glyphs inside
    OCR-confirmed text boxes (any font color). Safety rules so a false
    positive can never erase the product:
    - a component bbox larger than 25% of the image is never text -> skip
    - if the union mask still covers >22% of the image, refuse and flag the
      file for manual review
    """
    maroon = text_core(img_rgb).astype(np.uint8)
    maroon = cv2.morphologyEx(maroon, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    neutral = neutral_text_core(img_rgb).astype(np.uint8)
    neutral = cv2.morphologyEx(neutral, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    core = maroon | neutral
    if core.sum() < min_area:
        return None
    h, w = core.shape
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_px, dilate_px))
    dil = cv2.dilate(core, k)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(dil)
    mask = np.zeros(core.shape, np.uint8)
    found = False
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        comp = labels[y:y+bh, x:x+bw] == i
        core_px = int((core[y:y+bh, x:x+bw] & comp).sum())
        if core_px < min_area:
            continue  # too small to be a price line
        if bw * bh > 0.25 * w * h:
            continue  # giant blob = fabric/floor false positive, never text
        pad = 8
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(w, x + bw + pad), min(h, y + bh + pad)
        mask[y0:y1, x0:x1] = 255
        found = True
    if not found:
        return None
    if mask.sum() / 255 > 0.22 * w * h:
        raise ValueError("mask covers >22% of image - manual review needed")
    return mask


def leftover_px(img_rgb: np.ndarray, region: np.ndarray) -> int:
    """Count remaining text-colored pixels inside/near the treated region."""
    core = (text_core(img_rgb) | neutral_text_core(img_rgb)).astype(np.uint8)
    core = cv2.morphologyEx(core, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    near = cv2.dilate(region, np.ones((31, 31), np.uint8))
    return int((core & (near > 0)).sum())


def run_iopaint(image_dir: str, mask_dir: str, out_dir: str) -> None:
    cmd = [VENV_PY, "-m", "iopaint", "run", "--model=lama", "--device=cpu",
           f"--image={image_dir}", f"--mask={mask_dir}", f"--output={out_dir}"]
    for attempt in (1, 2):
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            return
        log = os.path.join(BASE, "iopaint_error.log")
        with open(log, "ab") as fh:
            fh.write(f"\n=== rc={r.returncode} attempt={attempt} {image_dir} ===\n".encode())
            fh.write(r.stdout[-4000:] + b"\n" + r.stderr[-4000:])
        print(f"  iopaint rc={r.returncode} (attempt {attempt}), see iopaint_error.log")
    sys.exit(f"iopaint failed twice for {image_dir}")


def process_folder(folder: str) -> None:
    src = os.path.join(BASE, folder)
    out = os.path.join(BASE, folder + " - sin precio")
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)

    img_dir = os.path.join(WORK, "imgs")
    mask_dir = os.path.join(WORK, "masks")
    res_dir = os.path.join(WORK, "res")
    for d in (img_dir, mask_dir, res_dir):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)

    files = sorted(f for f in os.listdir(src) if f.lower().endswith((".jpg", ".jpeg", ".png")))
    masks: dict[str, np.ndarray] = {}
    clean: list[str] = []
    manual: list[str] = []
    for f in files:
        rgb = np.array(Image.open(os.path.join(src, f)).convert("RGB"))
        try:
            m = build_mask(rgb)
        except ValueError:
            manual.append(f)
            print(f"  MANUAL REVIEW {f}: detection too large, skipped")
            continue
        if m is None:
            clean.append(f)
            shutil.copy2(os.path.join(src, f), os.path.join(out, f))
        else:
            masks[f] = m
            stem = os.path.splitext(f)[0]
            Image.fromarray(rgb).save(os.path.join(img_dir, stem + ".png"))
            Image.fromarray(m).save(os.path.join(mask_dir, stem + ".png"))

    print(f"[{folder}] {len(files)} images: {len(masks)} with text, {len(clean)} clean, {len(manual)} manual")
    if masks:
        run_iopaint(img_dir, mask_dir, res_dir)

    # verify each result; retry with wider dilation if maroon pixels remain
    for f, m in masks.items():
        stem = os.path.splitext(f)[0]
        res_path = os.path.join(res_dir, stem + ".png")
        rgb_src = np.array(Image.open(os.path.join(src, f)).convert("RGB"))
        for attempt, dil in enumerate((21, 31), start=1):
            res = np.array(Image.open(res_path).convert("RGB"))
            left = leftover_px(res, m)
            if left < 60:
                break
            print(f"  retry {attempt} for {f}: {left} text px left, dilate={dil}")
            try:
                m2 = build_mask(rgb_src, dilate_px=dil)
            except ValueError:
                print(f"  MANUAL REVIEW {f}: retry mask too large, keeping current result")
                break
            if m2 is None:
                break
            m = m2
            s_img, s_msk, s_res = (os.path.join(WORK, x) for x in ("r_img", "r_msk", "r_res"))
            for d in (s_img, s_msk, s_res):
                shutil.rmtree(d, ignore_errors=True)
                os.makedirs(d)
            Image.fromarray(rgb_src).save(os.path.join(s_img, stem + ".png"))
            Image.fromarray(m).save(os.path.join(s_msk, stem + ".png"))
            run_iopaint(s_img, s_msk, s_res)
            shutil.copy2(os.path.join(s_res, stem + ".png"), res_path)
        else:
            res = np.array(Image.open(res_path).convert("RGB"))
            print(f"  WARNING {f}: still {leftover_px(res, m)} text px after retries - check manually")
        shutil.copy2(res_path, os.path.join(out, stem + ".png"))

    # final sweep: no output image (processed or copied) may contain readable text
    flagged = []
    for f in sorted(os.listdir(out)):
        rgb = np.array(Image.open(os.path.join(out, f)).convert("RGB"))
        hits = [(t, c) for *_xy, t, c in ocr_text_boxes(rgb, min_conf=0.4)
                if sum(ch.isalnum() for ch in t) >= 3]
        if hits:
            flagged.append(f)
            print(f"  OCR-SWEEP {f}: readable text remains: {hits[:3]}")
    print(f"[{folder}] done -> {out}  ({'OK' if not flagged else f'{len(flagged)} flagged'})")


if __name__ == "__main__":
    targets = sys.argv[1:] or FOLDERS
    for folder in targets:
        process_folder(folder)
    shutil.rmtree(WORK, ignore_errors=True)
    print("ALL DONE")
