from services.ai.app.parser.pdf_parser import parse_pdf


def run():
    file_path = "sample.pdf"
    text = parse_pdf("data/sample.pdf")
    print("OUTPUT:\n", text[:500])
    print("LENGTH:", len(text))


run()