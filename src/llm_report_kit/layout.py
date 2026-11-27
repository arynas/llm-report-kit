"""Check visible text geometry in a rendered PDF."""
from itertools import combinations

import fitz


def inspect_layout(pdf):
    results = []
    with fitz.open(pdf) as document:
        for page in document:
            lines = []
            issues = []
            for block in page.get_text("dict")["blocks"]:
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    spans = [span for span in line["spans"] if span["text"].strip()]
                    if not spans:
                        continue
                    label = "".join(span["text"] for span in spans).strip()
                    bounds = fitz.Rect(line["bbox"])
                    lines.append((bounds, label))
                    if bounds not in page.rect + (-1, -1, 1, 1):
                        issues.append(f"Text outside the page: {label[:55]}")
                    if any(span["size"] < 6 for span in spans):
                        issues.append(f"Text smaller than 6 pt: {label[:55]}")
            if not lines:
                issues.append("No extractable text")
            for (first, first_label), (second, second_label) in combinations(lines, 2):
                intersection = first & second
                if intersection.width > 4 and intersection.height > 0.5 * min(first.height, second.height):
                    issues.append(f"Overlapping text: {first_label[:36]} / {second_label[:36]}")
            results.append({"page": page.number + 1, "issues": sorted(set(issues))})
    return results
