from services.ai.app.parser.docx_parser import parse_docx

def test_docx():
    text = parse_docx("data/sample.docx")
    print(text)