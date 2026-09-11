from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def chroma_to_alpha(source: Path, output: Path) -> None:
    image = Image.open(source).convert("RGB")
    rgb = np.asarray(image, dtype=np.float32)

    # The source is generated on a controlled green plate. Alpha is inferred
    # from green dominance rather than Euclidean RGB distance: this keeps
    # neutral/cream fur opaque while making green-mixed edge pixels softer.
    red = rgb[..., 0]
    green = rgb[..., 1]
    blue = rgb[..., 2]
    green_excess = green - np.maximum(red, blue)
    key_strength = np.clip((green_excess - 5.0) / 220.0, 0.0, 1.0)
    alpha = np.power(1.0 - key_strength, 1.7)
    if image.width >= 3 and image.height >= 3:
        alpha_image = Image.fromarray(np.rint(alpha * 255.0).astype(np.uint8), "L")
        alpha = np.asarray(alpha_image.filter(ImageFilter.MinFilter(3)), dtype=np.float32) / 255.0
    key = np.array([0.0, 255.0, 0.0], dtype=np.float32)

    # Remove green spill by reversing the source-over composition against
    # the known plate color. This preserves orange/cream fur at the edge.
    safe_alpha = np.maximum(alpha[..., None], 1.0 / 255.0)
    foreground = (rgb - (1.0 - alpha[..., None]) * key) / safe_alpha
    foreground = np.clip(foreground, 0.0, 255.0)

    rgba = np.dstack((foreground.astype(np.uint8), np.rint(alpha * 255.0).astype(np.uint8)))
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(output, optimize=True)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: chroma_to_alpha.py SOURCE OUTPUT")
    chroma_to_alpha(Path(sys.argv[1]), Path(sys.argv[2]))
