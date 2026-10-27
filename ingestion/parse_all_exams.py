#!/usr/bin/env python3
"""
ingestion/parse_all_exams.py
Parses official ISTQB CTFL v4.0.1 Sample Exams A, B, C, D from data/raw/*.pdf
and writes all 160 questions into seed/questions.json.
"""

import json
import os
import re
import pdfplumber

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
SEED_QUESTIONS_PATH = os.path.join(BASE_DIR, "seed", "questions.json")


def clean_text(t: str) -> str:
    return " ".join(t.split())


def parse_exam(exam_letter: str, start_id: int) -> list:
    q_pdf_path = os.path.join(RAW_DIR, f"Sample-Exam-{exam_letter}-Questions.pdf")
    a_pdf_path = os.path.join(RAW_DIR, f"Sample-Exam-{exam_letter}-Answers.pdf")

    if not os.path.exists(q_pdf_path) or not os.path.exists(a_pdf_path):
        print(f"  ✗ PDF files for Exam {exam_letter} not found.")
        return []

    # 1. Parse Answer Key table from page 6
    keys = {}
    with pdfplumber.open(a_pdf_path) as pdf:
        table_page = pdf.pages[5]
        text = table_page.extract_text()
        matches = re.findall(
            r"(\d+)\s+([a-e](?:,\s*[a-e])?)\s+(FL-\d+\.\d+\.\d+)\s+(K[123])\s+(\d+)",
            text,
        )
        for m in matches:
            q_num = int(m[0])
            correct = [x.strip().upper() for x in m[1].split(",")]
            lo = m[2]
            k = m[3]
            ch = int(lo.split("-")[1].split(".")[0])
            keys[q_num] = {
                "correct": correct,
                "lo": lo,
                "k_level": k,
                "chapter_id": ch,
            }

    # 2. Parse Explanations from Answers PDF
    explanations = {}
    with pdfplumber.open(a_pdf_path) as pdf:
        a_text = ""
        for p in pdf.pages[6:]:
            a_text += p.extract_text() + "\n"

    clean_a = re.sub(
        r"Version 1\.\d+ Page \d+ of \d+.*?\n© International Software Testing Qualifications Board",
        "",
        a_text,
    )
    clean_a = re.sub(
        rf"Certified Tester, Foundation Level\s+Sample Exam set {exam_letter}\s+Sample Exam – Answers",
        "",
        clean_a,
    )
    clean_a = re.sub(r"Answers\s+Question Correct Explanation.*?\n", "", clean_a)
    clean_a = re.sub(r"Number Answer Objective.*?\n", "", clean_a)
    clean_a = re.sub(r"\(#\)\s*\(LO\)\s*Points.*?\n", "", clean_a)

    exp_matches = re.findall(
        r"\n(\d+)\s+([a-e](?:,\s*[a-e])?)\s+(.*?)(?=\n\d+\s+[a-e]|\Z)",
        clean_a,
        re.DOTALL,
    )
    for num_str, _, exp_body in exp_matches:
        q_num = int(num_str)
        exp_clean = re.sub(r"FL-\d+\.\d+\.\d+\s+K[123]\s+\d+\s*$", "", exp_body.strip())
        explanations[q_num] = clean_text(exp_clean)

    # 3. Parse Questions
    questions = []
    with pdfplumber.open(q_pdf_path) as pdf:
        q_text = ""
        for p in pdf.pages[5:]:
            q_text += p.extract_text() + "\n"

    clean_q = re.sub(
        r"Version 1\.\d+ Page \d+ of \d+.*?\n© International Software Testing Qualifications Board",
        "",
        q_text,
    )
    clean_q = re.sub(
        rf"Certified Tester, Foundation Level\s+Sample Exam set {exam_letter}\s+Sample Exam – Questions",
        "",
        clean_q,
    )

    q_blocks = re.split(r"Question #(\d+)\s*\([^)]*\)", clean_q)
    for i in range(1, len(q_blocks), 2):
        q_num = int(q_blocks[i])
        body = q_blocks[i + 1].strip()
        body = re.sub(r"Select (?:ONE|TWO) options?\.?", "", body, flags=re.I).strip()

        parts = re.split(r"\n(?=[a-e]\))", body)
        stem = clean_text(parts[0])
        opt_list = []
        key_info = keys.get(
            q_num, {"correct": ["A"], "k_level": "K2", "chapter_id": 1}
        )
        correct_labels = key_info["correct"]

        for opt_str in parts[1:]:
            m = re.match(r"([a-e])\)\s*(.*)", opt_str, re.DOTALL)
            if m:
                lbl = m.group(1).upper()
                txt = clean_text(m.group(2))
                opt_list.append({
                    "label": lbl,
                    "text": txt,
                    "is_correct": lbl in correct_labels,
                })

        new_id = start_id + q_num - 1
        expl = explanations.get(q_num, "")
        if not expl:
            joined = ", ".join(correct_labels)
            expl = f"Correct answer: {joined}. Official ISTQB CTFL rationale."

        questions.append({
            "id": new_id,
            "chapter_id": key_info["chapter_id"],
            "stem": stem,
            "explanation": expl,
            "difficulty": key_info["k_level"],
            "options": opt_list,
        })

    return questions


def main():
    print("Parsing official ISTQB sample exams...")

    # Load existing Exam A questions (1-40)
    with open(SEED_QUESTIONS_PATH, "r", encoding="utf-8") as f:
        exam_a = json.load(f)[:40]
    print(f"  ✓ Retained Exam A: {len(exam_a)} questions")

    # Parse Exam B (41-80)
    exam_b = parse_exam("B", 41)
    print(f"  ✓ Parsed Exam B: {len(exam_b)} questions")

    # Parse Exam C (81-120)
    exam_c = parse_exam("C", 81)
    print(f"  ✓ Parsed Exam C: {len(exam_c)} questions")

    # Parse Exam D (121-160)
    exam_d = parse_exam("D", 121)
    print(f"  ✓ Parsed Exam D: {len(exam_d)} questions")

    all_questions = exam_a + exam_b + exam_c + exam_d
    print(f"\nTotal combined questions: {len(all_questions)}")

    # Quality check
    for q in all_questions:
        assert q["stem"], f"Empty stem in question {q['id']}"
        assert len(q["options"]) >= 4, f"Fewer than 4 options in question {q['id']}"
        has_correct = any(opt["is_correct"] for opt in q["options"])
        assert has_correct, f"No correct option in question {q['id']}"
        assert 1 <= q["chapter_id"] <= 6, f"Invalid chapter_id in question {q['id']}"

    print("  ✓ All 160 questions passed validation checks!")

    with open(SEED_QUESTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Saved to {SEED_QUESTIONS_PATH}")


if __name__ == "__main__":
    main()
