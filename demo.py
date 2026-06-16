"""
demo.py — Quick demo of the Balance Sheet QA system.
Run this to test without needing a real PDF.

Usage:
    python demo.py
    python demo.py path/to/balance_sheet.pdf
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from balance_sheet_qa import BalanceSheetQA, SAMPLE_BALANCE_SHEET

# ── Programmatic usage example ────────────────────────────────────────────────

def demo():
    qa = BalanceSheetQA()

    # Option 1: Load from a real file
    # qa.load("infosys_balance_sheet.pdf")

    # Option 2: Load from raw text (demo)
    qa.load_from_text(SAMPLE_BALANCE_SHEET)

    questions = [
        "What are the total assets of the company?",
        "How much cash does the company have?",
        "What is the current ratio and what does it indicate?",
        "What is the total equity including non-controlling interests?",
        "Compare current assets vs current liabilities.",
        "What is the book value per share?",
    ]

    print("=" * 65)
    print("  BALANCE SHEET Q&A DEMO — Infosys FY2024")
    print("=" * 65)

    for q in questions:
        print(f"\n❓ {q}")
        print("-" * 55)
        answer = qa.ask(q)
        print(f"💡 {answer}")
        print()

    # Reset for a fresh conversation
    qa.reset_history()

    # Single follow-up question example
    print("\n── Follow-up question (fresh context) ──")
    answer = qa.ask("Is this company financially healthy based on the balance sheet?")
    print(f"💡 {answer}")


if __name__ == "__main__":
    # If a PDF path is passed, use that; otherwise run demo
    if len(sys.argv) > 1:
        qa = BalanceSheetQA()
        qa.load(sys.argv[1])
        # Run interactive CLI
        from balance_sheet_qa import run_cli
        run_cli(sys.argv[1])
    else:
        demo()
