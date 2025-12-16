#!/usr/bin/env python3
"""Generate a small SVG coverage badge (pass/fail or percentage) and write to a file.

The badge contains only minimal non-sensitive information: a short label and
"coverage: XX%" or "coverage: FAIL" and a green/red color. It does NOT include
branch names, repository names, or other metadata.

Usage: python scripts/generate_coverage_badge.py --file coverage.xml --threshold 80 --output badges/coverage.svg
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET

SVG_TEMPLATE = """<svg xmlns='http://www.w3.org/2000/svg' width='110' height='20' role='img' aria-label='coverage'>
  <rect width='110' height='20' rx='3' fill='#{left_color}'/>
  <rect x='60' width='50' height='20' rx='3' fill='#{right_color}'/>
  <g fill='#fff' font-family='DejaVu Sans,Verdana,Geneva,sans-serif' font-size='11'>
    <text x='8' y='14'>coverage</text>
    <text x='68' y='14'>{right_text}</text>
  </g>
</svg>"""


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--file', default='coverage.xml')
    p.add_argument('--threshold', type=float, required=True)
    p.add_argument('--output', default='badges/coverage.svg')
    return p.parse_args()


def get_coverage_from_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()

    line_rate = root.attrib.get('line-rate')
    if line_rate is not None:
        return float(line_rate) * 100.0

    covered = root.attrib.get('lines-covered')
    valid = root.attrib.get('lines-valid')
    if covered is not None and valid is not None:
        covered = int(covered)
        valid = int(valid)
        return (covered / valid) * 100.0 if valid else 0.0

    raise RuntimeError('Could not extract coverage percentage from XML')


def color_for_pct(pct, threshold):
    return '4c1' if pct >= threshold else 'e05d44'  # green or red


def main():
    args = parse_args()
    try:
        pct = get_coverage_from_xml(args.file)
    except Exception as e:
        print(f'Error reading coverage file: {e}', file=sys.stderr)
        sys.exit(2)

    pass_ok = pct >= args.threshold
    right_text = f'{int(round(pct))}% ' if pass_ok else 'FAIL'
    left_color = '555'  # dull left
    right_color = color_for_pct(pct, args.threshold)

    svg = SVG_TEMPLATE.format(left_color=left_color, right_color=right_color, right_text=right_text)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'Wrote coverage badge to {args.output}: {right_text.strip()}')


if __name__ == '__main__':
    main()
