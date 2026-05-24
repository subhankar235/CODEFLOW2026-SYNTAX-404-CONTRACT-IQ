import asyncio
import os
import sys

# Setup environment
os.environ["PYTHONPATH"] = "."
sys.path.insert(0, ".")

async def main():
    print("Testing Spacy...")
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print("Spacy loaded successfully.")
    except Exception as e:
        print(f"Spacy failed: {e}")
        return

    print("Testing RuleEngine...")
    try:
        from services.ai.app.rules.regex_rules import RuleEngine
        engine = RuleEngine()
        result = engine.evaluate_clause("This is a non-compete clause.", "Employment")
        print(f"RuleEngine success: {result}")
    except Exception as e:
        print(f"RuleEngine failed: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(main())
