#!/usr/bin/env python3
"""
Clean the synthetic incidents CSV by handling commas inside brackets and unescaped quotes in text.
Output: data/synthetic_incidents_clean.csv
"""
from pathlib import Path
import csv

INPUT = Path('data') / 'synthetic_incidents.csv'
OUTPUT = Path('data') / 'synthetic_incidents_clean.csv'

def smart_split(row: str):
    fields = []
    current = []
    in_quotes = False
    bracket_level = 0
    i = 0
    while i < len(row):
        ch = row[i]
        if ch == '"':
            in_quotes = not in_quotes
            current.append(ch)
        elif ch == '[':
            bracket_level += 1
            current.append(ch)
        elif ch == ']':
            bracket_level = max(0, bracket_level - 1)
            current.append(ch)
        elif ch == ',' and not in_quotes and bracket_level == 0:
            fields.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    fields.append(''.join(current).strip())
    return fields

def main():
    lines = INPUT.read_text(encoding='utf-8').splitlines()
    if not lines:
        raise SystemExit('Input CSV is empty')
    header = lines[0]
    header_cols = header.split(',')
    expected_cols = len(header_cols)

    with OUTPUT.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header_cols)
        for idx, line in enumerate(lines[1:], start=2):
            if not line.strip():
                continue
            cols = smart_split(line)
            if len(cols) != expected_cols:
                # Try to join overflow columns back into the last column
                if len(cols) > expected_cols:
                    head = cols[:expected_cols-1]
                    tail = ','.join(cols[expected_cols-1:])
                    cols = head + [tail]
                else:
                    # Pad missing columns
                    cols = cols + [''] * (expected_cols - len(cols))
            writer.writerow(cols)
    print(f"Wrote cleaned CSV to {OUTPUT}")

if __name__ == '__main__':
    main()
