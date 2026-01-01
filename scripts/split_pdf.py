from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

from PyPDF2 import PdfReader, PdfWriter

INPUT_PDF = "/home/mark/noel-chatbot/content/Super_Made_Simple_7thEd_1125 - no toc.pdf"
OUTPUT_DIR = "/home/mark/chapters_out"

# Assumption per your note:
# printed page 1 == PDF page 1 (i.e. first page of PDF is printed page 1)
# Therefore: PDF index = printed_page - 1
# No offset needed beyond the -1 conversion.

TOC: List[Tuple[str, int]] = [
    # The fundamentals
    ("The fundamentals - Superannuation: a money paradise", 1),
    ("The fundamentals - The ageing population", 4),
    ("The fundamentals - Will there be a pension when I retire?", 6),
    ("The fundamentals - Superannuation - what is it?", 8),
    ("The fundamentals - Why we don't like superannuation", 9),
    ("The fundamentals - It's a box not an asset", 11),
    ("The fundamentals - The carrot and the stick", 13),

    # Contributions
    ("Contributions - The way it used to be", 14),
    ("Contributions - 1983 - the year it all changed", 16),
    ("Contributions - What's the point?", 19),
    ("Contributions - Who may contribute to superannuation", 21),
    ("Contributions - Types of contributions", 24),
    ("Contributions - Splitting your super with your spouse", 28),

    # Taxes on super
    ("Taxes on super - Contributions tax", 30),
    ("Taxes on super - Is superannuation taxed three times?", 34),
    ("Taxes on super - Can I claim a tax deduction?", 35),
    ("Taxes on super - Tax on the end benefit", 38),
    ("Taxes on super - Non-resident beneficiaries of superannuation death benefits", 40),
    ("Taxes on super - The $3 million super tax proposal", 43),
    ("Taxes on super - Cutting your CGT bill with superannuation", 47),
    ("Taxes on super - Salary sacrifice", 51),
    ("Taxes on super - Salary sacrifice for the young", 53),

    # Types of funds
    ("Types of funds - What type of fund you are in", 55),
    ("Types of funds - Defined benefit or accumulation fund?", 62),
    ("Types of funds - Maximising the end benefit", 64),
    ("Types of funds - The value of time", 67),
    ("Types of funds - Risk", 68),
    ("Types of funds - The right assets for your fund", 71),

    # Your own self-managed fund
    ("Your own self-managed fund - Choosing the best superannuation fund", 74),
    ("Your own self-managed fund - Start your own self-managed fund?", 78),
    ("Your own self-managed fund - Running your own fund", 81),
    ("Your own self-managed fund - Which assets to buy?", 84),

    # How much?
    ("How much? - How much can I have in superannuation?", 87),
    ("How much? - Moving money to pension mode", 88),
    ("How much? - How much superannuation do I need?", 90),

    # Access to your superannuation
    ("Access to your superannuation - Access to your superannuation", 92),
    ("Access to your superannuation - Early access to your superannuation", 95),
    ("Access to your superannuation - Changing jobs", 97),

    # When you retire
    ("When you retire - Drawing your superannuation when you retire", 99),
    ("When you retire - Account-based pensions", 101),
    ("When you retire - Transition to retirement pensions (TTRs)", 104),
    ("When you retire - Retirement income streams", 107),
    ("When you retire - Comprehensive income products for retirement (CIPRs)", 109),
    ("When you retire - Lifetime income streams", 110),
    ("When you retire - A tax-free retirement!", 113),
    ("When you retire - Investing after retirement", 115),

    # What happens when you die?
    ("What happens when you die? - Superannuation and death", 117),
    ("What happens when you die? - Who controls your superannuation when you die?", 125),

    # Strategies
    ("Strategies - Saving on life insurance", 128),
    ("Strategies - Creating a sinking fund", 130),
    ("Strategies - Safe as a bank!!", 134),
    ("Strategies - The super shortcut to a million", 136),

    # Gifts from the government
    ("Gifts from the government - Spouse rebate and government co-contribution", 140),
    ("Gifts from the government - Superannuation and Centrelink", 143),

    # Other issues
    ("Other issues - Superannuation and relationship breakdown", 145),
    ("Other issues - Superannuation and small business", 147),
    ("Other issues - Getting engaged", 152),
    ("Other issues - Where to now?", 155),

    # Glossary / Appendices / Index
    ("Glossary", 157),
    ("Appendices - Life expectancy table 2017", 160),
    ("Index", 166),
]


def slugify(s: str) -> str:
    s = s.lower().replace("'", "'")
    s = re.sub(r"[^\w\s\-']", "", s)
    s = re.sub(r"[\s\-]+", "_", s).strip("_")
    return s[:120] if len(s) > 120 else s


def printed_to_pdf_index(printed_page: int) -> int:
    # printed page 1 -> PDF index 0
    return printed_page - 1


def split_pdf_by_toc(input_pdf: str, output_dir: str, toc: List[Tuple[str, int]]) -> None:
    reader = PdfReader(input_pdf)
    n_pages = len(reader.pages)

    print(f"PDF has {n_pages} pages")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Build (title, printed_start, pdf_start_index) list
    items = [(title, printed, printed_to_pdf_index(printed)) for title, printed in toc]
    items.sort(key=lambda x: x[2])

    # Basic validation
    for title, printed, start_idx in items:
        if start_idx < 0 or start_idx >= n_pages:
            raise ValueError(
                f"TOC entry '{title}' has printed page {printed} -> PDF index {start_idx}, "
                f"but PDF has {n_pages} pages."
            )

    # Write chapter PDFs
    for i, (title, printed, start_idx) in enumerate(items):
        end_idx = (items[i + 1][2] - 1) if i + 1 < len(items) else (n_pages - 1)
        if end_idx < start_idx:
            continue

        writer = PdfWriter()
        for p in range(start_idx, end_idx + 1):
            writer.add_page(reader.pages[p])

        out_name = f"{i+1:03d}_{slugify(title)}_p{printed}.pdf"
        out_path = Path(output_dir) / out_name
        with open(out_path, "wb") as f:
            writer.write(f)

    print(f"Done. Wrote {len(items)} files to '{output_dir}'.")


if __name__ == "__main__":
    split_pdf_by_toc(INPUT_PDF, OUTPUT_DIR, TOC)
