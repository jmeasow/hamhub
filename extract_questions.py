#!/usr/bin/env python3
"""Extracts the HamHub question bank from the official PDF into a JSON
file that ham_quiz.py can load without needing any PDF library.

This only needs to be run once (or again whenever ISED publishes an
updated version of ``amateur_basic_questions_en.pdf``). It requires
pdfplumber (see requirements.txt); ham_quiz.py itself does not.

Usage:
    python extract_questions.py [path/to/question_bank.pdf] [-o questions.json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

DEFAULT_PDF_NAME = "amateur_basic_questions_en.pdf"
DEFAULT_JSON_NAME = "questions.json"
DEFAULT_JS_NAME = "web/questions.js"
QUESTION_ID_RE = re.compile(r"^(B-\d{3}-\d{3}-\d{3})\s*\(([A-D])\)\s*$")


def _page_reading_order_text(page) -> str:
    """Returns a page's text reassembled in left-column-then-right-column
    reading order.

    The question bank PDF lays questions out in two side-by-side columns.
    A naive extract_text() interleaves lines from both columns, so each
    column is cropped out separately based on its known x-position before
    extracting text.
    """
    column_split_x = 230
    left = page.crop((0, 0, column_split_x, page.height)).extract_text() or ""
    right = page.crop((column_split_x, 0, page.width, page.height)).extract_text() or ""
    return left + "\n" + right


def _split_question_block(qid: str, answer: str, lines: list) -> Optional[dict]:
    """Splits the raw lines following a question id into the question
    text and its four choices.

    Choice lines start with "A ", "B ", "C ", "D " in that order, but the
    question text itself can also start with a line beginning with a
    bare letter (e.g. "A radio inspector asks..."), so the four choice
    lines are located by scanning backward from the end of the block
    instead of forward from the start.
    """

    def find_last(letter: str, end: int) -> Optional[int]:
        pattern = re.compile(rf"^{letter}\s")
        for i in range(end - 1, -1, -1):
            if pattern.match(lines[i]):
                return i
        return None

    d_idx = find_last("D", len(lines))
    c_idx = find_last("C", d_idx) if d_idx is not None else None
    b_idx = find_last("B", c_idx) if c_idx is not None else None
    a_idx = find_last("A", b_idx) if b_idx is not None else None

    if None in (a_idx, b_idx, c_idx, d_idx):
        return None

    def join(start: int, end: int, strip_prefix: bool = False) -> str:
        chunk = lines[start:end]
        if strip_prefix and chunk:
            chunk = [re.sub(r"^[A-D]\s+", "", chunk[0])] + chunk[1:]
        return " ".join(part.strip() for part in chunk if part.strip())

    question_text = join(0, a_idx)
    choices = {
        "A": join(a_idx, b_idx, strip_prefix=True),
        "B": join(b_idx, c_idx, strip_prefix=True),
        "C": join(c_idx, d_idx, strip_prefix=True),
        "D": join(d_idx, len(lines), strip_prefix=True),
    }

    if not question_text or any(not text for text in choices.values()):
        return None

    return {"id": qid, "question": question_text, "choices": choices, "answer": answer}


def parse_pdf(pdf_path: Path) -> list:
    """Parses the question bank PDF into a list of question dicts."""
    import pdfplumber

    lines: list = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines.extend(_page_reading_order_text(page).split("\n"))

    questions: list = []
    current_id = None
    current_answer = None
    current_lines: list = []

    def flush():
        if current_id is None:
            return
        question = _split_question_block(current_id, current_answer, current_lines)
        if question:
            questions.append(question)

    for raw_line in lines:
        line = raw_line.strip()
        match = QUESTION_ID_RE.match(line)
        if match:
            flush()
            current_id = match.group(1)
            current_answer = match.group(2)
            current_lines = []
        elif line:
            current_lines.append(line)
    flush()

    return questions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pdf",
        nargs="?",
        default=str(Path(__file__).resolve().parent / DEFAULT_PDF_NAME),
        help="Path to the question bank PDF (defaults to %(default)s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(Path(__file__).resolve().parent / DEFAULT_JSON_NAME),
        help="Path to write the extracted questions JSON to (defaults to %(default)s)",
    )
    parser.add_argument(
        "--js-output",
        default=str(Path(__file__).resolve().parent / DEFAULT_JS_NAME),
        help="Path to write the questions as a browser-loadable JS file (defaults to %(default)s)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: could not find question bank PDF at {pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {pdf_path.name}...")
    questions = parse_pdf(pdf_path)
    if not questions:
        print("Error: no questions could be parsed from the PDF.", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    questions_json = json.dumps(questions, indent=2, ensure_ascii=False)
    output_path.write_text(questions_json, encoding="utf-8")
    print(f"Wrote {len(questions)} questions to {output_path}")

    js_output_path = Path(args.js_output)
    js_output_path.parent.mkdir(parents=True, exist_ok=True)
    js_output_path.write_text(
        "// Auto-generated by extract_questions.py - do not edit by hand.\n"
        f"const QUESTIONS = {questions_json};\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(questions)} questions to {js_output_path}")


if __name__ == "__main__":
    main()
