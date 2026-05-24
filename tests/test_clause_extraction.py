# file → detect type

# if PDF → pdf_parser
# if DOCX → docx_parser

# if text bad → fallback_parser

# → clean text → clause extraction


from services.ai.app.pipelines.clause_extraction import segment_clauses

def test_clauses():
    with open("data/contract.txt", "r", encoding="utf-8") as f:
        text = f.read()

    clauses = segment_clauses(text)

    print("\nTOTAL CLAUSES:", len(clauses))

    for c in clauses[:3]:
        print("\n---CLAUSE---")
        print(c)

    assert len(clauses) > 0