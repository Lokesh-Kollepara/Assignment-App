#!/usr/bin/env python3
"""
Test script to check PDF extraction for assignment PDFs.
Usage: python test_pdf_extraction.py <path_to_pdf>
"""

import sys
from pathlib import Path
from app.services.advanced_pdf_extractor import AdvancedPDFExtractor


def test_pdf_extraction(pdf_path: str):
    """Test PDF extraction and display results."""

    print("=" * 80)
    print(f"TESTING PDF EXTRACTION: {Path(pdf_path).name}")
    print("=" * 80)

    # Initialize extractor
    extractor = AdvancedPDFExtractor()

    # Extract structured content
    print("\n[1/3] Extracting structured content from PDF...")
    try:
        structured_content = extractor.extract_structured_content(pdf_path)
        print("✓ Extraction successful")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return

    # Display summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)

    print(f"\n📄 Total Pages: {len(structured_content['pages'])}")
    print(f"📝 Total Characters: {len(structured_content['full_text'])}")
    print(f"❓ Questions Found: {len(structured_content['questions'])}")
    print(f"📋 Scenarios Found: {len(structured_content['scenarios'])}")

    # Count tables and images
    total_tables = sum(len(page['tables']) for page in structured_content['pages'])
    total_images = sum(len(page['images']) for page in structured_content['pages'])

    print(f"📊 Tables Found: {total_tables}")
    print(f"🖼️  Images Found: {total_images}")

    # Display scenarios
    if structured_content['scenarios']:
        print("\n" + "=" * 80)
        print("SCENARIOS DETECTED")
        print("=" * 80)
        for i, scenario in enumerate(structured_content['scenarios'], 1):
            print(f"\n[Scenario {i}] (Page {scenario['page']})")
            print(f"Text preview: {scenario['text'][:200]}...")

    # Display tables
    if total_tables > 0:
        print("\n" + "=" * 80)
        print("TABLES DETECTED")
        print("=" * 80)
        for page_num, page in enumerate(structured_content['pages'], 1):
            if page['tables']:
                for table_num, table in enumerate(page['tables'], 1):
                    print(f"\n[Table {table_num}] on Page {page_num}")
                    if table['data']:
                        print("Table preview (first 3 rows):")
                        for row in table['data'][:3]:
                            print("  | " + " | ".join(str(cell) for cell in row))

    # Display images
    if total_images > 0:
        print("\n" + "=" * 80)
        print("IMAGES DETECTED")
        print("=" * 80)
        for page_num, page in enumerate(structured_content['pages'], 1):
            if page['images']:
                print(f"\nPage {page_num}: {len(page['images'])} image(s) found")

    # Display questions
    print("\n" + "=" * 80)
    print("QUESTIONS EXTRACTED")
    print("=" * 80)

    if not structured_content['questions']:
        print("\n⚠️  No questions found!")
        print("\nFull text preview (first 500 chars):")
        print(structured_content['full_text'][:500])
    else:
        for i, question in enumerate(structured_content['questions'], 1):
            print(f"\n{'─' * 80}")
            print(f"Question {i}: {question['id']}")
            print(f"{'─' * 80}")
            print(f"Text: {question['text'][:150]}..." if len(question['text']) > 150 else f"Text: {question['text']}")

            # Display badges
            badges = []
            if question['has_scenario']:
                badges.append("🔵 SCENARIO")
            if question['has_table']:
                badges.append("🟢 TABLE")
            if question['has_image']:
                badges.append("🟡 IMAGE")

            if badges:
                print(f"Badges: {' | '.join(badges)}")
            else:
                print("Badges: None")

    # Display chunks that would be stored
    print("\n" + "=" * 80)
    print("CHUNKS FOR VECTOR STORE")
    print("=" * 80)

    chunks = extractor.create_question_chunks(structured_content)
    print(f"\nTotal chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks, 1):
        print(f"\n[Chunk {i}] Type: {chunk['metadata']['type'].upper()}")
        print(f"Text preview: {chunk['text'][:150]}...")
        if chunk['metadata']['type'] == 'question':
            print(f"Metadata: Question ID={chunk['metadata'].get('question_id', 'N/A')}, "
                  f"Scenario={chunk['metadata']['has_scenario']}, "
                  f"Table={chunk['metadata']['has_table']}, "
                  f"Image={chunk['metadata']['has_image']}")

    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pdf_extraction.py <path_to_pdf>")
        print("\nExample:")
        print("  python test_pdf_extraction.py data/pdfs/assignments/my_assignment.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    test_pdf_extraction(pdf_path)
