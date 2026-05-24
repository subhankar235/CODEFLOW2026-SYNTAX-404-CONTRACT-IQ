from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class CounterOfferRequest(BaseModel):
    clause_text: str
    clause_type: str
    contract_type: str
    user_role: str
    risk_category: str


@router.post("/counter-offer")
async def generate_counter_offer(req: CounterOfferRequest):
    """
    Generate counter-offer language using the OpenRouter LLM.
    Uses favorable clause reference from AI data folder for context.
    """
    from app.models.openrouter_client import complete

    favorable_map = {
        "non_compete": "Any non-competition restriction shall be narrowly limited to direct solicitation of Client's named customers with whom Service Provider had documented, material contact during the engagement, and shall not exceed six (6) months from the date of termination. The restriction shall apply solely within the specific geographic markets where Service Provider actively performed services under this Agreement and shall not extend globally or nationally absent a separate written agreement.",
        "ip_assignment": "Service Provider retains full ownership of all pre-existing intellectual property, proprietary tools, frameworks, libraries, and methodologies developed independently of this Agreement. Client receives a non-exclusive, royalty-free, perpetual license to use Background IP solely to the extent embedded in the agreed deliverables. Only purpose-built, original work product created exclusively for Client under a signed Statement of Work shall be assigned to Client upon receipt of full payment.",
        "indemnity": "Each Party shall indemnify, defend, and hold harmless the other Party from and against any third-party claims arising solely out of the indemnifying Party's gross negligence or willful misconduct. This obligation shall not extend to claims caused by the indemnified Party's own acts, omissions, or breach of this Agreement. The indemnifying Party's liability under this section shall be subject to the aggregate cap set forth in the Limitation of Liability clause.",
        "auto_renewal": "This Agreement shall not renew automatically. Renewal requires Client's affirmative written election delivered to Service Provider no fewer than sixty (60) days before the end of the then-current term. Absent such written election, this Agreement shall expire at the conclusion of the current term with no further obligation on either Party. Service Provider shall issue a renewal reminder to Client ninety (90) days before the opt-in deadline.",
        "limitation_of_liability": "Neither Party shall be liable to the other for any indirect, incidental, special, punitive, exemplary, or consequential damages of any nature, including but not limited to loss of revenue, loss of profits, loss of business, loss of data, loss of goodwill, or cost of substitute services, even if such Party has been advised of the possibility of such damages.",
    }

    favorable_ref = favorable_map.get(req.risk_category, "")

    prompt = f"""You are an expert contract attorney. Generate counter-offer language for the following clause.

CLAUSE TYPE: {req.risk_category}
CONTRACT TYPE: {req.contract_type}

ORIGINAL CLAUSE:
\"\"\"{req.clause_text}\"\"\"

FAVORABLE REFERENCE (use as guidance for what good language looks like):
\"\"\"{favorable_ref}\"\"\"

Respond ONLY with valid JSON — no markdown, no explanation outside JSON.

JSON schema:
{{
  "aggressive": {{
    "clause": "<full replacement clause text, be specific and legally sound, 2-4 sentences>",
    "explanation": "<2-3 sentence explanation of what this version achieves>"
  }},
  "balanced": {{
    "clause": "<compromise replacement that protects key interests, 2-4 sentences>",
    "explanation": "<2-3 sentence explanation of the compromise>"
  }},
  "conservative": {{
    "clause": "<minimal change that still improves the clause, 2-4 sentences>",
    "explanation": "<2-3 sentence explanation of the minimal protection>"
  }},
  "negotiation_email": "<professional email (150-200 words) proposing this change. Be specific about what you want changed and why, include a reasonable ask that leaves room for compromise. Sign as [Your Name].>"
}}

Rules:
- Generate substantively different clauses (aggressive, balanced, conservative must all be meaningfully different).
- The aggressive version should give maximum protection to the employee/interested party's side.
- The balanced version should be a reasonable middle ground.
- The conservative version should offer minimal but meaningful protection.
- The negotiation email should propose the balanced version as the preferred compromise.
- Adapt language to the clause type: non_compete (focus on scope/duration), ip_assignment (focus on scope/exclusions), termination (focus on notice/severance), indemnity (focus on mutuality/limits), auto_renewal (focus on opt-in/cancellation), etc."""

    try:
        result = await complete(
            model="meta-llama/llama-3.3-70b-instruct",
            system_prompt="You are an expert contract attorney. Respond only with valid JSON as instructed.",
            user_prompt=prompt,
            max_tokens=2048,
            temperature=0.7,
            json_mode=True,
        )

        import json
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise HTTPException(status_code=500, detail="Empty response from LLM")

        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            inner = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(inner).strip()

        parsed = json.loads(cleaned)

        return {
            "aggressive_clause": parsed.get("aggressive", {}).get("clause", ""),
            "explanation_aggressive": parsed.get("aggressive", {}).get("explanation", ""),
            "balanced_clause": parsed.get("balanced", {}).get("clause", ""),
            "explanation_balanced": parsed.get("balanced", {}).get("explanation", ""),
            "conservative_clause": parsed.get("conservative", {}).get("clause", ""),
            "explanation_conservative": parsed.get("conservative", {}).get("explanation", ""),
            "negotiation_email": parsed.get("negotiation_email", ""),
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON from LLM: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")