import asyncio
import os
import sys

# Setup environment
os.environ["PYTHONPATH"] = "."
sys.path.insert(0, ".")

async def main():
    try:
        from services.ai.app.pipelines.risk_classification import run_risk_classification
        clauses = ["This is a test clause.", "Another test clause."]
        print("Running run_risk_classification...")
        results = run_risk_classification(clauses, "Employment", "employee")
        for r in results:
            print(r)
        print("Success")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
