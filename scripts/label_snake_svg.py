#!/usr/bin/env python3
"""
Adds weekday labels (Mon/Wed/Fri) to the left of Platane/snk SVG output.

Usage:
  python scripts/label_snake_svg.py dist/github-snake.svg dist/github-snake-labeled.svg
"""

import sys
import xml.etree.ElementTree as ET

LABEL_MARGIN = 34  # px, left padding for labels

def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag

def main():
    if len(sys.argv) != 3:
        print("Usage: label_snake_svg.py <in.svg> <out.svg>")
        sys.exit(1)

    in_path, out_path = sys.argv[1], sys.argv[2]

    tree = ET.parse(in_path)
    root = tree.getroot()

    # Namespace (usually 'http://www.w3.org/2000/svg')
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}", 1)[0] + "}"
    def q(name: str) -> str:
        return f"{ns}{name}"

    # Find all rects and collect unique y positions
    ys = []
    for el in root.iter():
        if strip_ns(el.tag) == "rect" and el.get("x") is not None and el.get("y") is not None:
            try:
                ys.append(float(el.get("y")))
            except ValueError:
                pass

    ys = sorted(set(ys))
    if len(ys) < 7:
        # Fallback: snake might have different structure; still try
        # But usually it's 7 rows.
        pass

    # Heuristic: top row is Sunday, then Mon..Sat
    # Place labels at Mon (index 1), Wed (3), Fri (5) if available.
    def y_for_row(idx: int) -> float:
        if len(ys) > idx:
            return ys[idx]
        return ys[-1] if ys else 0.0

    label_rows = [
        ("Mon", y_for_row(1)),
        ("Wed", y_for_row(3)),
        ("Fri", y_for_row(5)),
    ]

    # Wrap existing children into a translated <g>
    translated = ET.Element(q("g"))
    translated.set("transform", f"translate({LABEL_MARGIN},0)")

    # Move all current children into translated group
    children = list(root)
    for ch in children:
        root.remove(ch)
        translated.append(ch)

    # Add labels group before translated content
    labels_g = ET.Element(q("g"))
    labels_g.set("font-family", "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial")
    labels_g.set("font-size", "10")
    labels_g.set("fill", "#586069")  # GitHub-ish gray

    # Try to align vertically to the center of each row (rect height ~10-11)
    # We'll add +8 to y for baseline alignment.
    for text, y in label_rows:
        t = ET.SubElement(labels_g, q("text"))
        t.set("x", str(LABEL_MARGIN - 6))
        t.set("y", str(y + 8))
        t.set("text-anchor", "end")
        t.text = text

    # Update width/viewBox so translation doesn't clip
    def add_px(value: str, extra: int) -> str:
        # handles "900" or "900px"
        v = value.strip()
        if v.endswith("px"):
            n = float(v[:-2])
            return f"{n + extra}px"
        try:
            n = float(v)
            # if it's int-like, keep it clean
            return str(int(n + extra)) if n.is_integer() else str(n + extra)
        except ValueError:
            return value

    if root.get("width"):
        root.set("width", add_px(root.get("width"), LABEL_MARGIN))
    if root.get("viewBox"):
        parts = root.get("viewBox").split()
        if len(parts) == 4:
            x, y, w, h = map(float, parts)
            # Expand viewBox to the left by LABEL_MARGIN
            x -= LABEL_MARGIN
            w += LABEL_MARGIN
            root.set("viewBox", f"{x:g} {y:g} {w:g} {h:g}")

    root.append(labels_g)
    root.append(translated)

    tree.write(out_path, encoding="utf-8", xml_declaration=True)

if __name__ == "__main__":
    main()
