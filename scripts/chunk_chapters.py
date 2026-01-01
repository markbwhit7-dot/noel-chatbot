from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple

from PyPDF2 import PdfReader

CHAPTERS_DIR = "/home/mark/chapters_out"
OUTPUT_JSON = "/home/mark/chunks_for_qdrant.json"

# Chunking parameters
CHUNK_SIZE = 800  # tokens (approximate via chars / 4)
CHUNK_OVERLAP = 100  # tokens overlap
CHARS_PER_TOKEN = 4  # rough estimate

# Index entries: (topic, page_start, page_end)
# Parsed from the book's index for topic tagging
INDEX_ENTRIES: List[Tuple[str, int, int]] = [
    ("Access to your superannuation", 92, 93),
    ("Account-based pensions", 101, 104),
    ("Account-based pensions – minimum yearly drawings", 102, 103),
    ("Accumulation funds", 55, 57),
    ("Accumulation phase", 87, 90),
    ("Age pension", 143, 144),
    ("Assets – choosing", 71, 74),
    ("Binding nominations", 125, 126),
    ("Capital gains tax (CGT)", 47, 49),
    ("Catch-up contributions", 24, 27),
    ("Centrelink", 143, 144),
    ("Changing jobs", 97, 98),
    ("Choosing the best superannuation fund", 74, 77),
    ("Claiming a tax deduction", 35, 37),
    ("Co-contribution", 140, 142),
    ("Compounding – power of", 67, 68),
    ("Comprehensive income products", 109, 109),
    ("Concessional contributions", 21, 24),
    ("Contributions tax", 30, 32),
    ("Contributions – types of", 24, 28),
    ("Corporate super funds", 74, 75),
    ("Cutting capital gains tax", 47, 50),
    ("Death benefit nominations", 117, 125),
    ("Death tax", 121, 124),
    ("Defined benefit funds", 62, 63),
    ("Division 296 Special Tax", 43, 46),
    ("Downsizer contribution", 23, 49),
    ("Drawing your superannuation when you retire", 99, 100),
    ("Early access to superannuation", 95, 97),
    ("Employers – contributions by", 21, 24),
    ("Estate planning", 117, 125),
    ("Fees and charges", 76, 77),
    ("Government contributions", 140, 142),
    ("Growth vs defensive assets", 71, 74),
    ("Income streams in retirement", 107, 110),
    ("Insurance inside super", 76, 77),
    ("Insurance inside super (strategies)", 128, 130),
    ("Investing after retirement", 115, 116),
    ("Investment choice", 71, 74),
    ("Investment risk", 68, 70),
    ("Life expectancy table", 160, 160),
    ("Lifetime income streams", 110, 113),
    ("Maximizing the end benefit", 64, 66),
    ("Non-concessional contributions", 24, 28),
    ("Non-resident beneficiaries", 40, 42),
    ("Non-resident fund members", 94, 94),
    ("Pension phase – taxation of", 113, 115),
    ("Preservation rules", 95, 97),
    ("Re-contribution strategies", 47, 49),
    ("Relationship breakdown", 145, 146),
    ("Retirement income", 107, 115),
    ("Risk", 68, 70),
    ("Salary sacrifice", 51, 53),
    ("Self-managed super funds (SMSFs)", 78, 84),
    ("Sinking funds creating", 130, 132),
    ("Small business and super", 147, 150),
    ("SMSF – which assets to buy?", 84, 86),
    ("Spouse contributions", 140, 142),
    ("Spouse rebate", 140, 140),
    ("Super shortcut to a million", 136, 139),
    ("Superannuation – balance limits", 87, 90),
    ("Superannuation and death", 117, 124),
    ("Superannuation – history of", 14, 15),
    ("Superannuation – how much do I need?", 90, 91),
    ("Superannuation – splitting with spouse", 28, 29),
    ("Superannuation – tax on $3 million balances", 43, 46),
    ("Superannuation – what's the point?", 19, 20),
    ("Tax – on contributions", 30, 35),
    ("Tax – on earnings", 38, 39),
    ("Tax – on the end benefit", 38, 39),
    ("Tax-free retirement", 113, 115),
    ("Transfer balance cap", 88, 89),
    ("Transition-to-retirement pensions (TTRs)", 104, 107),
    ("Trustee – best for your SMSF", 82, 83),
    ("Trustees and control after death", 125, 126),
    ("Value of time", 67, 68),
    ("Withdrawals and lump sums", 99, 101),
    ("Work test exemption", 2, 2),
]

# Section mappings from chapter title prefix
SECTIONS = [
    "The fundamentals",
    "Contributions",
    "Taxes on super",
    "Types of funds",
    "Your own self-managed fund",
    "How much?",
    "Access to your superannuation",
    "When you retire",
    "What happens when you die?",
    "Strategies",
    "Gifts from the government",
    "Other issues",
    "Glossary",
    "Appendices",
    "Index",
]


def extract_section(chapter_title: str) -> str:
    """Extract the section name from a chapter title."""
    for section in SECTIONS:
        if chapter_title.lower().startswith(section.lower()):
            return section
    return "Other"


def get_content_type(chapter_title: str) -> str:
    """Determine content type from chapter title."""
    title_lower = chapter_title.lower()
    if "glossary" in title_lower:
        return "glossary"
    if "appendix" in title_lower or "appendices" in title_lower:
        return "appendix"
    if "index" in title_lower:
        return "index"
    return "chapter"


def get_topics_for_pages(page_start: int, page_end: int) -> List[str]:
    """Find all index topics that overlap with the given page range."""
    topics = []
    for topic, idx_start, idx_end in INDEX_ENTRIES:
        # Check if page ranges overlap
        if page_start <= idx_end and page_end >= idx_start:
            topics.append(topic)
    return topics


def parse_chapter_filename(filename: str) -> Tuple[str, int]:
    """Extract chapter title and starting page from filename."""
    # Format: 001_the_fundamentals_superannuation_a_money_paradise_p1.pdf
    match = re.match(r"\d+_(.+)_p(\d+)\.pdf", filename)
    if match:
        slug = match.group(1)
        page = int(match.group(2))
        # Convert slug back to readable title (approximate)
        title = slug.replace("_", " ").title()
        # Fix common patterns
        title = title.replace("'S", "'s").replace("'T", "'t")
        return title, page
    return filename, 1


def create_chunks(text: str, chunk_size: int, overlap: int) -> List[Tuple[str, int, int]]:
    """
    Split text into overlapping chunks.
    Returns list of (chunk_text, char_start, char_end).
    """
    char_chunk_size = chunk_size * CHARS_PER_TOKEN
    char_overlap = overlap * CHARS_PER_TOKEN

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + char_chunk_size, text_len)

        # Try to break at sentence or paragraph boundary
        if end < text_len:
            # Look for sentence end within last 20% of chunk
            search_start = start + int(char_chunk_size * 0.8)
            best_break = end

            for pattern in ["\n\n", ".\n", ". ", "?\n", "? ", "!\n", "! "]:
                pos = text.rfind(pattern, search_start, end)
                if pos > search_start:
                    best_break = pos + len(pattern)
                    break

            end = best_break

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append((chunk_text, start, end))

        # Move start position, accounting for overlap
        start = end - char_overlap
        if start >= text_len or start <= chunks[-1][1] if chunks else 0:
            break

    return chunks


def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, int]:
    """Extract all text from a PDF file. Returns (text, num_pages)."""
    reader = PdfReader(pdf_path)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n\n".join(text_parts), len(reader.pages)


def process_chapters() -> List[Dict[str, Any]]:
    """Process all chapter PDFs and return chunks with metadata."""
    chapters_dir = Path(CHAPTERS_DIR)
    all_chunks = []

    # Sort files to process in order
    pdf_files = sorted(chapters_dir.glob("*.pdf"))

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        # Parse filename for metadata
        chapter_title, page_start = parse_chapter_filename(pdf_path.name)

        # Extract text
        text, num_pages = extract_text_from_pdf(pdf_path)
        page_end = page_start + num_pages - 1

        if not text.strip():
            print(f"  Warning: No text extracted from {pdf_path.name}")
            continue

        # Get metadata
        section = extract_section(chapter_title)
        content_type = get_content_type(chapter_title)
        topics = get_topics_for_pages(page_start, page_end)

        # Chunk the text
        chunks = create_chunks(text, CHUNK_SIZE, CHUNK_OVERLAP)

        for i, (chunk_text, char_start, char_end) in enumerate(chunks):
            # Estimate page for this chunk (rough approximation)
            text_progress = char_start / max(len(text), 1)
            chunk_page = page_start + int(text_progress * num_pages)

            chunk_data = {
                "id": str(uuid.uuid4()),
                "text": chunk_text,
                "metadata": {
                    "source": "Super Made Simple 7th Ed",
                    "chapter_title": chapter_title,
                    "section": section,
                    "page_start": page_start,
                    "page_end": page_end,
                    "chunk_page": chunk_page,  # Approximate page for this chunk
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "topics": topics,
                    "content_type": content_type,
                    "char_start": char_start,
                    "char_end": char_end,
                }
            }
            all_chunks.append(chunk_data)

        print(f"  Created {len(chunks)} chunks (pages {page_start}-{page_end})")

    return all_chunks


def main():
    print("Chunking chapter PDFs for Qdrant...")
    print(f"Chunk size: ~{CHUNK_SIZE} tokens, Overlap: ~{CHUNK_OVERLAP} tokens\n")

    chunks = process_chapters()

    # Write output
    output_path = Path(OUTPUT_JSON)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Created {len(chunks)} chunks")
    print(f"Output saved to: {output_path}")

    # Summary stats
    content_types = {}
    sections = {}
    for chunk in chunks:
        ct = chunk["metadata"]["content_type"]
        sec = chunk["metadata"]["section"]
        content_types[ct] = content_types.get(ct, 0) + 1
        sections[sec] = sections.get(sec, 0) + 1

    print("\nChunks by content type:")
    for ct, count in sorted(content_types.items()):
        print(f"  {ct}: {count}")

    print("\nChunks by section:")
    for sec, count in sorted(sections.items(), key=lambda x: -x[1]):
        print(f"  {sec}: {count}")


if __name__ == "__main__":
    main()
