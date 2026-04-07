import re
import numpy as np
import cv2
import pytesseract


def _order_corners(pts):
    """Return corners in (top-left, top-right, bottom-right, bottom-left) order."""
    pts = pts.reshape(4, 2).astype("float32")
    s    = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    return np.array([
        pts[np.argmin(s)],
        pts[np.argmin(diff)],
        pts[np.argmax(s)],
        pts[np.argmax(diff)],
    ], dtype="float32")


def _warp_grid(gray):
    """Find the Sudoku grid and return a flat 540×540 bird's-eye view."""
    blurred = cv2.GaussianBlur(gray, (9, 9), 3)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=11, C=2,
    )

    # Dilate to close small gaps in grid lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(thresh, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    # Try progressively looser polygon approximations across the top candidates
    grid_contour = None
    for eps in [0.02, 0.03, 0.01, 0.05]:
        for c in contours[:5]:
            peri  = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, eps * peri, True)
            if len(approx) == 4:
                grid_contour = approx
                break
        if grid_contour is not None:
            break

    size = 540
    dst  = np.array([[0, 0], [size-1, 0], [size-1, size-1], [0, size-1]], dtype="float32")

    if grid_contour is not None:
        src = _order_corners(grid_contour)
    else:
        # Fall back: treat the whole image as the grid
        h, w = gray.shape
        src  = np.array([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]], dtype="float32")

    M      = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(gray, M, (size, size))
    return warped


def _remove_grid_lines(warped):
    """Erase horizontal and vertical grid lines from the warped image."""
    _, thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    cell = warped.shape[0] // 9

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (cell, 1))
    h_lines  = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=2)

    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, cell))
    v_lines  = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel, iterations=2)

    mask    = cv2.add(h_lines, v_lines)
    mask    = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)

    cleaned = warped.copy()
    cleaned[mask > 0] = 255   # paint grid lines white (background)
    return cleaned


def _read_cell(cell_img):
    """Return the digit in a single cell image, or 0 if empty."""
    pad = 5
    h, w = cell_img.shape
    inner = cell_img[pad:h - pad, pad:w - pad]

    _, bw = cv2.threshold(inner, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours to locate the digit
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0

    # Keep only contours large enough to be a digit
    ih, iw = inner.shape
    min_area = (ih * iw) * 0.006
    contours = [c for c in contours if cv2.contourArea(c) >= min_area]
    if not contours:
        return 0

    # Bounding box around all digit contours combined
    xs, ys, x2s, y2s = [], [], [], []
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        xs.append(x); ys.append(y)
        x2s.append(x + cw); y2s.append(y + ch)
    x1, y1, x2, y2 = min(xs), min(ys), max(x2s), max(y2s)

    digit = bw[y1:y2, x1:x2]

    # Thicken strokes slightly — helps 7, 6, 9 without distorting 8
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))
    digit  = cv2.dilate(digit, kernel, iterations=1)

    # Centre the digit on a white canvas with padding (black digit on white = Tesseract default)
    canvas_size = 150
    margin = 20
    dh, dw = digit.shape
    scale  = min((canvas_size - 2*margin) / dh, (canvas_size - 2*margin) / dw)
    new_h, new_w = max(1, int(dh * scale)), max(1, int(dw * scale))
    resized = cv2.resize(digit, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.full((canvas_size, canvas_size), 255, dtype=np.uint8)  # white background
    y_off  = (canvas_size - new_h) // 2
    x_off  = (canvas_size - new_w) // 2
    canvas[y_off:y_off + new_h, x_off:x_off + new_w] = 255 - resized  # black digit

    def _ocr(img, psm):
        cfg  = f"--psm {psm} --oem 1 -c tessedit_char_whitelist=123456789"
        text = pytesseract.image_to_string(img, config=cfg).strip()
        return re.sub(r"[^1-9]", "", text)

    text = _ocr(canvas, 10) or _ocr(canvas, 8) or _ocr(canvas, 6)
    return int(text[0]) if text else 0


def parse_sudoku_image(img_bytes):
    """
    Parse a Sudoku puzzle from raw image bytes.
    Returns a 9×9 list of ints (0 = empty cell).
    Raises ValueError if the image cannot be decoded.
    """
    arr = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image.")

    gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    warped  = _warp_grid(gray)
    cleaned = _remove_grid_lines(warped)

    cell_size = cleaned.shape[0] // 9
    grid = []
    for row in range(9):
        r = []
        for col in range(9):
            y1, y2 = row * cell_size, (row + 1) * cell_size
            x1, x2 = col * cell_size, (col + 1) * cell_size
            r.append(_read_cell(cleaned[y1:y2, x1:x2]))
        grid.append(r)

    return grid
