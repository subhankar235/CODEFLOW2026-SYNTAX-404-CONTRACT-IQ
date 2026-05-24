"""
Chat Endpoint — POST /api/v1/chat/{contractId}
Implements STEP 8.2: Q&A chat with streaming SSE response.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.api.deps import get_current_user, get_db
from app.models.user import User

from app.services.chat_service import (
    verify_contract_and_get_id,
    check_embeddings_exist,
    stream_chat_response,
)

router = APIRouter()


@router.post("/{contract_id}")
async def chat_with_contract(
    contract_id: str,
    request: Dict[str, Any],
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream chat response for a contract Q&A.

    - Verifies JWT and ownership
    - Checks that embeddings exist for the contract (graceful fallback)
    - Streams the answer token-by-token via SSE
    
    SSE event format:
      data: {"type": "token", "content": "<text>"}\n\n
      data: {"type": "citation", "clause_id": "<id>"}\n\n
      data: {"type": "error", "content": "<message>"}\n\n
    """
    # Special case for demo contract
    if contract_id == "demo-contract":
        async def demo_stream():
            import json
            import asyncio

            # Real demo responses based on actual demo contract clauses
            demo_responses = {
                "competitor": """Based on the contract analysis, you CANNOT work for a competitor after leaving. 

**Section 4.1 — Non-Compete Clause** states: "The Employee agrees that during the term of employment and for a period of two (2) years following termination, the Employee shall not engage in any business that competes directly or indirectly with the Employer within a radius of fifty (50) miles of any of the Employer's offices."

**Key Risks:**
- This clause prohibits you from working for ANY competing business within 50 miles for 2 years after leaving
- Courts frequently enforce such clauses, meaning you could be sued if you take a job with a competitor
- This effectively traps you in your current role or forces you to leave the area

**Financial Exposure:** Up to $250,000 in potential damages

**Negotiable?** YES — This clause can be modified. Consider negotiating: (1) reduce scope to 25 miles, (2) limit duration to 6 months, (3) restrict to direct competitors only.""",

                "ip": """Based on the contract analysis, the company CLAIMS ownership over ALL intellectual property you create during employment.

**Section 4.2 — IP Assignment Clause** states: "All intellectual property, including but not limited to inventions, discoveries, improvements, designs, works of authorship, and trade secrets, conceived, developed, or reduced to practice by the Employee during the term of employment, whether during working hours or using company resources or not, shall be the sole and exclusive property of the Company."

**Key Risks:**
- You lose all rights to apps, products, or inventions you create — even ones created entirely on your own time
- This could strip you of rights to personal projects, side businesses, or code you write on weekends
- California law limits such broad clauses, but other states may enforce them

**Financial Exposure:** Potentially $2,000,000 or more in lost IP value

**Negotiable?** YES — This clause can be modified. Push for: (1) IP on your own time without company resources belongs to you, (2) company waives claims to work unrelated to business.""",

                "terminat": """Based on the contract analysis, the company CAN fire you immediately with NO notice or severance.

**Section 4.3 — Termination Clause** states: "The Company may terminate this Agreement at any time, with or without cause, without prior notice, and without any severance obligation. The Employee hereby waives any right to advance notice, severance pay, or any other compensation upon termination."

**Key Risks:**
- You could be terminated today with no warning, no severance, and no explanation
- Leaving you suddenly without income
- You have no legal recourse even if fired unfairly

**Financial Exposure:** Approximately $75,000 in lost severance/notice

**Negotiable?** NO — This is a hard at-will provision. However, you can push for severance as a separate negotiation during hiring.""",

                "intellectual": """Based on the contract analysis, there are SEVERAL unusual intellectual property clauses:

**Section 4.2 — Full IP Assignment (HIGH RISK):** Claims ownership over ALL work created during employment, even on your own time with your own equipment.

**Section 4.4 — Company Resources Clause (MEDIUM RISK):** States that IP created using company resources belongs to the company, and they can even claim pre-existing work you incorporated.

**Key Concern:** If you occasionally check personal email on your work laptop or use company WiFi for a side project, those projects could be claimed as company IP.

**Financial Exposure:** Unknown — could be unlimited depending on value of your personal projects

**Negotiable?** YES — Push for clear language that IP created on your own time without company resources belongs to you.""",

                "notice": """Based on the contract analysis, the termination clause does NOT provide any notice period protection.

**Section 4.3 — Termination Clause** states: "The Company may terminate this Agreement at any time, with or without cause, without prior notice."

**Key Points:**
- The company can fire you immediately without any advance notice
- You have waived all rights to advance notice or severance pay
- Employment at-will is standard in most states, but explicitly waiving severance is aggressive

**Financial Exposure:** Up to $75,000 in lost severance based on your salary and tenure

**What You Can Do:**
1. Negotiate for at least 2 weeks notice requirement
2. Request severance based on tenure (2 weeks per year of employment)
3. Keep copies of all performance reviews and communications
4. Document your contributions to the company""",

                "default": """Based on the contract analysis, here are the key concerns I found:

**HIGH RISK Clauses:**

1. **Non-Compete Clause (Section 4.1):** Prohibits working for competitors within 50 miles for 2 years after leaving. Risk Score: HIGH. Financial Exposure: $250,000.

2. **Full IP Assignment (Section 4.2):** Claims ownership over ALL work created during employment, including personal projects on your own time. Risk Score: HIGH. Financial Exposure: $2,000,000.

3. **Termination at Will (Section 4.3):** Company can fire you immediately with no notice or severance. You waive all rights. Risk Score: HIGH. Financial Exposure: $75,000.

**MEDIUM RISK Clauses:**

4. **Company Resources IP (Section 4.4):** Can claim personal projects if you use company resources. Risk Score: MEDIUM.

5. **Indemnification (Section 4.5):** You pay company's legal costs if sued. Risk Score: MEDIUM. Financial Exposure: $500,000.

**Recommendation:** You should definitely negotiate the non-compete and IP assignment clauses before signing. These are highly negotiable and can be significantly improved."""
            }

            # Determine which response to give based on question keywords
            question_lower = ""
            async for chunk in asyncio.as_completed([]):
                pass
            
            response_text = demo_responses["default"]
            question = request.get("question", request.get("message", "")).lower()
            
            if "competitor" in question or "compete" in question:
                response_text = demo_responses["competitor"]
            elif "ip" in question or "intellectual" in question or "code" in question or "invention" in question or "work" in question:
                if "notice" in question or "period" in question or "advance" in question:
                    response_text = demo_responses["notice"]
                else:
                    response_text = demo_responses["ip"]
            elif "terminat" in question or "fired" in question or "fire" in question or "notice" in question:
                response_text = demo_responses["terminat"]
            elif "intellectual" in question or "unusual" in question:
                response_text = demo_responses["intellectual"]

            for word in response_text.split(" "):
                yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
                await asyncio.sleep(0.02)
            
            # Add citation based on question
            if "competitor" in question or "compete" in question:
                yield f"data: {json.dumps({'type': 'citation', 'clause_id': 'clause-001'})}\n\n"
            elif "ip" in question or "intellectual" in question or "code" in question:
                yield f"data: {json.dumps({'type': 'citation', 'clause_id': 'clause-002'})}\n\n"
            elif "terminat" in question or "fired" in question:
                yield f"data: {json.dumps({'type': 'citation', 'clause_id': 'clause-003'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'citation', 'clause_id': 'clause-001'})}\n\n"

        return StreamingResponse(
            demo_stream(),
            media_type="text/event-stream",
        )

    # Verify contract and ownership
    contract_uuid = await verify_contract_and_get_id(
        db, contract_id, current_user
    )
    if not contract_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found or access denied",
        )

    question = request.get("question") or request.get("message", "")
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question or message is required",
        )

    # Check embeddings — pass db for async query (won't block if table missing)
    await check_embeddings_exist(db, contract_uuid)

    conversation_history = request.get("conversation_history", [])

    # Stream the response
    return StreamingResponse(
        stream_chat_response(str(contract_uuid), question, conversation_history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
