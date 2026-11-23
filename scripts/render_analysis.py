#!/usr/bin/env python3
"""Render red-pen programmer requirement annotations onto e-doc page images."""

import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

RED = (217, 43, 43)
WHITE_BG = (255, 255, 255, 220)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def to_px(norm_x: float, norm_y: float, width: int, height: int) -> tuple[int, int]:
    return int(round(norm_x / 1000.0 * width)), int(round(norm_y / 1000.0 * height))


def render_spec(spec_path: Path, out_dir: Path) -> None:
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    doc_name = data.get("doc_name") or spec_path.stem
    doc_out_dir = out_dir / doc_name
    doc_out_dir.mkdir(parents=True, exist_ok=True)

    annotated_images: list[Image.Image] = []

    for idx, page in enumerate(data.get("pages", []), start=1):
        img_path = Path(page["image"])
        if not img_path.is_absolute():
            img_path = spec_path.parent.parent / img_path

        img = Image.open(img_path).convert("RGBA")
        w, h = img.size
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for item in page.get("annotations", []):
            box = item.get("box")
            if box and len(box) == 4:
                x1, y1 = to_px(box[0], box[1], w, h)
                x2, y2 = to_px(box[2], box[3], w, h)
                stroke = int(item.get("stroke_width", max(2, round(w / 400))))
                draw.rectangle([x1, y1, x2, y2], outline=RED + (255,), width=stroke)

            label = item.get("label")
            label_pos = item.get("label_pos")
            if label and label_pos and len(label_pos) == 2:
                lx, ly = to_px(label_pos[0], label_pos[1], w, h)
                font_size = int(item.get("font_size", max(14, round(w / 62))))
                font = load_font(font_size)
                anchor = item.get("anchor", "lt")
                align = item.get("align", "left")

                bbox0 = draw.multiline_textbbox((0, 0), label, font=font, align=align)
                tw = bbox0[2] - bbox0[0]
                th = bbox0[3] - bbox0[1]

                ax = anchor[0] if len(anchor) >= 1 else "l"
                ay = anchor[1] if len(anchor) >= 2 else "t"
                dx = -tw / 2 if ax == "m" else (-tw if ax == "r" else 0)
                dy = -th / 2 if ay == "m" else (-th if ay == "b" else 0)
                tx, ty = int(round(lx + dx - bbox0[0])), int(round(ly + dy - bbox0[1]))

                if item.get("bg", False):
                    pad = 3
                    draw.rectangle(
                        [tx + bbox0[0] - pad, ty + bbox0[1] - pad, tx + bbox0[2] + pad, ty + bbox0[3] + pad],
                        fill=WHITE_BG,
                    )

                draw.multiline_text(
                    (tx, ty),
                    label,
                    fill=RED + (255,),
                    font=font,
                    align=align,
                )

        combined = Image.alpha_composite(img, overlay).convert("RGB")
        out_png = doc_out_dir / f"{doc_name}_page_{idx}_annotated.png"
        combined.save(out_png, "PNG")
        annotated_images.append(combined)
        print(f"Saved {out_png}")

    if annotated_images:
        out_pdf = doc_out_dir / f"{doc_name}_annotated.pdf"
        annotated_images[0].save(
            out_pdf,
            "PDF",
            resolution=150.0,
            save_all=True,
            append_images=annotated_images[1:],
        )
        print(f"Saved {out_pdf}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: render_analysis.py <annotations.json> [output_dir]")
        sys.exit(1)

    spec_path = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else spec_path.parent.parent / "output"
    render_spec(spec_path, out_dir)


if __name__ == "__main__":
    main()
