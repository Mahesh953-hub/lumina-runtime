from __future__ import annotations

import numpy as np
from PIL import Image


def observe(image: Image.Image) -> dict:
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    luminance = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    quantized = (rgb * 255).astype(np.uint8).reshape(-1, 3)
    colors, counts = np.unique(quantized, axis=0, return_counts=True)
    order = np.argsort(counts)[-5:][::-1]
    dominant = [
        {"rgb": colors[index].tolist(), "fraction": round(float(counts[index] / len(quantized)), 4)}
        for index in order
    ]
    background = colors[order[-1]]
    mask = np.any(quantized != background, axis=1).reshape(image.height, image.width)
    rows, columns = np.where(mask)
    content_bbox = None
    if rows.size:
        content_bbox = [
            int(columns.min()),
            int(rows.min()),
            int(columns.max()),
            int(rows.max()),
        ]
    histogram = np.histogram(luminance, bins=64, range=(0, 1))[0].astype(float)
    probabilities = histogram / max(histogram.sum(), 1)
    entropy = float(
        -(probabilities[probabilities > 0] * np.log2(probabilities[probabilities > 0])).sum()
    )
    return {
        "dominant_colors": dominant,
        "mean_rgb": [round(float(value), 4) for value in rgb.mean(axis=(0, 1))],
        "geometry": {
            "background_rgb": background.tolist(),
            "content_bbox": content_bbox,
            "non_background_fraction": round(float(mask.mean()), 4),
        },
        "quality": {
            "brightness": round(float(luminance.mean()), 4),
            "contrast": round(float(luminance.std()), 4),
            "entropy": round(entropy, 4),
            "dynamic_range": round(float(np.ptp(luminance)), 4),
        },
    }
