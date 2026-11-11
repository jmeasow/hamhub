#!/usr/bin/env python3
"""HamHub Quiz - practice tool for the Canadian Basic Amateur Radio
Operator Certificate exam.

Loads the question bank from ``questions.json`` (generated ahead of time
from the official ISED PDF by extract_questions.py) and quizzes the user
with random multiple-choice questions until they quit. Needs only the
Python standard library to run.

Usage:
    python ham_quiz.py [path/to/questions.json]

During the quiz:
    - Type A, B, C or D (case-insensitive) to answer.
    - Type Q to quit and see your final score.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_JSON_NAME = "questions.json"
CHOICE_LETTERS = ("A", "B", "C", "D")


@dataclass
class Question:
    id: str
    text: str
    choices: dict  # original bank letter (A/B/C/D) -> choice text
    answer: str  # original bank letter that is correct


def load_questions(json_path: Path) -> list:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return [
        Question(id=q["id"], text=q["question"], choices=q["choices"], answer=q["answer"])
        for q in data
    ]


class Deck:
    """Hands out questions in a random order without repeats until the
    whole bank has been asked once, then reshuffles and starts over."""

    def __init__(self, questions: list):
        self._questions = questions
        self._order: list = []

    def draw(self) -> Question:
        if not self._order:
            self._order = list(range(len(self._questions)))
            random.shuffle(self._order)
        return self._questions[self._order.pop()]


def ask_question(question: Question) -> bool:
    """Prints a question with shuffled choices, prompts for an answer,
    reports correctness, and returns True if the user answered correctly."""
    shuffled_letters = list(CHOICE_LETTERS)
    random.shuffle(shuffled_letters)

    print(f"\n[{question.id}] \n\n{question.text}\n")
    display_to_original = {}
    for display_letter, original_letter in zip(CHOICE_LETTERS, shuffled_letters):
        display_to_original[display_letter] = original_letter
        print(f"  {display_letter}) {question.choices[original_letter]}")
    print()

    while True:
        raw = input("Your answer (A/B/C/D, Q to quit): ").strip().upper()
        if raw in ("Q", "QUIT", "EXIT"):
            raise KeyboardInterrupt
        if raw in display_to_original:
            break
        print("Please enter A, B, C, D, or Q to quit.")

    chosen_original = display_to_original[raw]
    is_correct = chosen_original == question.answer
    correct_display_letter = next(
        d for d, o in display_to_original.items() if o == question.answer
    )

    if is_correct:
        print("Correct!")
    else:
        print(
            f"Incorrect. The correct answer was "
            f"{correct_display_letter}) {question.choices[question.answer]}"
        )

    return is_correct


def run_quiz(questions: list) -> None:
    deck = Deck(questions)
    correct = 0
    total = 0

    print(f"Loaded {len(questions)} questions. Let's begin!")
    print("Type A, B, C, or D to answer, or Q to quit at any time.\n")

    try:
        while True:
            question = deck.draw()
            total += 1
            if ask_question(question):
                correct += 1
            print(f"Score so far: {correct}/{total}")
    except (KeyboardInterrupt, EOFError):
        pass

    print("\n--- Final Score ---")
    if total == 0:
        print("No questions answered.")
    else:
        pct = 100 * correct / total
        print(f"{correct}/{total} correct ({pct:.1f}%)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "questions_json",
        nargs="?",
        default=str(Path(__file__).resolve().parent / DEFAULT_JSON_NAME),
        help="Path to the questions JSON file (defaults to %(default)s)",
    )
    args = parser.parse_args()

    json_path = Path(args.questions_json)
    if not json_path.exists():
        print(
            f"Error: could not find {json_path}.\n"
            "Run extract_questions.py first to generate it from the question bank PDF.",
            file=sys.stderr,
        )
        sys.exit(1)

    questions = load_questions(json_path)
    if not questions:
        print(f"Error: no questions found in {json_path}.", file=sys.stderr)
        sys.exit(1)

    run_quiz(questions)


if __name__ == "__main__":
    main()
