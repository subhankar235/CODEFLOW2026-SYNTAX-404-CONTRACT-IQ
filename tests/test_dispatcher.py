from services.ai.app.parser import parse_document

def test_dispatcher():
    print("TEST STARTED")

    text = parse_document("data/sample.pdf")

    print("AFTER PARSE")
    print("LENGTH:", len(text))

    assert text is not None