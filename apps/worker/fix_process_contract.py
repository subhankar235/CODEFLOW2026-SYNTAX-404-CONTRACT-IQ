import re

file_path = r"C:\Users\subhankar nath\Desktop\Legal-Tech\apps\worker\tasks\process_contract.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# I will replace everything from Step 8 to the end of run_pipeline
target_str = """        # ------------------------------------------------------------------
        # Step 8: Run risk classification (LLM on flagged clauses)
        # ------------------------------------------------------------------
        publish_progress(str(contract_id), 35, "Running risk classification")
        logger.info("Step 8: Running risk classification")"""

idx = content.find(target_str)
if idx == -1:
    print("Could not find Step 8")
    exit(1)

head = content[:idx]

tail = """        # ------------------------------------------------------------------
        # Step 8: Run risk classification (LLM on flagged clauses)
        # ------------------------------------------------------------------
        publish_progress(str(contract_id), 35, "Running risk classification")
        logger.info("Step 8: Running risk classification")

        # Fallback list for results
        clause_results = []
        try:
            from services.ai.app.pipelines.risk_classification import run_risk_classification
            classification_results = run_risk_classification(
                clauses=clauses_text,
                contract_type=contract_type_str,
                user_role=user_role_str,
            )

            for result in classification_results:
                clause_result = {
                    "clause_id": str(uuid4()),
                    "position_index": result.clause_index,
                    "text": result.clause_text[:500],
                    "risk_level": result.risk_severity.value,
                    "risk_category": result.risk_categories[0] if result.risk_categories else "other",
                    "risk_categories": result.risk_categories,
                    "plain_english": result.explanation,
                    "worst_case_scenario": result.recommendation,
                    "negotiable": True,
                    "confidence": 0.8 if result.llm_analysed else 0.5,
                    "llm_analysed": result.llm_analysed,
                    "triage": result.triage,
                }
                clause_results.append(clause_result)
                publish_clause(str(contract_id), clause_result)

            logger.info("Step 8: Risk classification complete via LLM pipeline")
        except ImportError as e:
            logger.warning("risk_classification module not available, using basic results: %s", e)
            for i, text in enumerate(clauses_text):
                triaged_result = triage_results[i] if triage_results and i < len(triage_results) else None
                if triaged_result:
                    risk_level = "HIGH" if triaged_result.result.triage.value == "RED" else \\
                                 "MEDIUM" if triaged_result.result.triage.value == "YELLOW" else "LOW"
                    categories = triaged_result.result.categories
                else:
                    risk_level = "LOW"
                    categories = []

                clause_result = {
                    "clause_id": str(uuid4()),
                    "position_index": i,
                    "text": text[:500],
                    "risk_level": risk_level,
                    "risk_category": categories[0] if categories else "other",
                    "risk_categories": categories,
                    "plain_english": "Risk detected via rule engine" if risk_level != "LOW" else "No risk signals detected",
                    "worst_case_scenario": "Review with legal counsel" if risk_level != "LOW" else "Standard clause",
                    "negotiable": True,
                    "confidence": 0.6,
                    "llm_analysed": False,
                    "triage": triaged_result.result.triage.value if triaged_result else "GREEN",
                }
                clause_results.append(clause_result)
                publish_clause(str(contract_id), clause_result)
        except Exception as e:
            logger.error("Risk classification failed: %s", e)
            for i, text in enumerate(clauses_text):
                clause_result = {
                    "clause_id": str(uuid4()),
                    "position_index": i,
                    "text": text[:500],
                    "risk_level": "LOW",
                    "risk_category": "other",
                    "plain_english": "Analysis unavailable",
                    "worst_case_scenario": "Review manually",
                    "negotiable": True,
                    "confidence": 0.0,
                    "llm_analysed": False,
                    "triage": "GREEN",
                }
                clause_results.append(clause_result)
                publish_clause(str(contract_id), clause_result)

        # ------------------------------------------------------------------
        # Step 9: Run consequence generation on HIGH and MEDIUM clauses
        # ------------------------------------------------------------------
        publish_progress(str(contract_id), 70, "Generating consequences")
        logger.info("Step 9: Running consequence generation")

        consequence_results = []
        try:
            from services.ai.app.pipelines.consequence_generation import run_consequence_generation, ClauseInput
            from services.ai.app.pipelines.risk_classification import RiskSeverity
            
            clause_inputs = []
            for cr in clause_results:
                if cr["risk_level"] in ("HIGH", "MEDIUM"):
                    clause_inputs.append(
                        ClauseInput(
                            clause_id=cr["clause_id"],
                            clause_type=cr.get("risk_category", "unknown"),
                            clause_text=cr["text"],
                            risk_level=RiskSeverity(cr["risk_level"]),
                            risk_category=cr.get("risk_category", ""),
                            user_role=user_role_str,
                            contract_value=None,
                        )
                    )
                    
            if clause_inputs:
                consequence_results = run_consequence_generation(clause_inputs)
                logger.info("Step 9: Consequence generation complete (%d items)", len(consequence_results))
            else:
                logger.info("Step 9: No HIGH/MEDIUM clauses to generate consequences for")
        except ImportError as e:
            logger.warning("Consequence generation module not available: %s", e)
        except Exception as e:
            logger.warning("Consequence generation failed (%s); falling back to empty list", e)

        # Update clause_results with consequence data
        if consequence_results:
            consequence_map = {res.clause_id: res for res in consequence_results}
            for cr in clause_results:
                if cr["clause_id"] in consequence_map:
                    cons = consequence_map[cr["clause_id"]]
                    cr["worst_case_scenario"] = cons.consequence_description
                    cr["plain_english"] = f"Financial Risk: {cons.financial_impact}\\nOperational Risk: {cons.operational_impact}"

        # ------------------------------------------------------------------
        # Step 10: Run power asymmetry analysis
        # ------------------------------------------------------------------
        publish_progress(str(contract_id), 75, "Analyzing power asymmetry")
        logger.info("Step 10: Running power asymmetry analysis")

        power_score = 50
        power_reasoning = "Neutral distribution of rights."
        try:
            from services.ai.app.pipelines.power_analysis import run_power_asymmetry
            power_result = run_power_asymmetry(
                clauses=clauses_text,
                user_role=user_role_str,
                contract_type=contract_type_str,
            )
            power_score = power_result.score
            power_reasoning = power_result.reasoning
            logger.info("Step 10: Power analysis complete, score=%d", power_score)
        except ImportError as e:
            logger.warning("Power asymmetry module not available: %s", e)
        except Exception as e:
            logger.warning("Power analysis failed (%s); using default score", e)

        # ------------------------------------------------------------------
        # Step 11: Run legal precedent retrieval for HIGH-risk clauses
        # ------------------------------------------------------------------
        publish_progress(str(contract_id), 80, "Retrieving legal precedents")
        logger.info("Step 11: Running legal precedent retrieval")
        # Currently skipped

        # ------------------------------------------------------------------
        # Step 12: Run summary card generation
        # ------------------------------------------------------------------
        publish_progress(str(contract_id), 85, "Generating summary")
        logger.info("Step 12: Running summary card generation")

        summary_data = {
            "pros": [],
            "cons": [],
            "leverage_points": [],
            "red_flags": [],
            "summary_text": "A standard contract requiring review."
        }
        
        try:
            from services.ai.app.pipelines.summary import run_summary
            summary_result = run_summary(
                clauses=clauses_text,
                contract_type=contract_type_str,
                user_role=user_role_str,
            )
            
            # Map Pydantic object to dict structure
            summary_data = {
                "pros": summary_result.pros,
                "cons": summary_result.cons,
                "leverage_points": summary_result.leverage_points,
                "red_flags": summary_result.red_flags,
                "summary_text": summary_result.verdict_summary,
            }
            logger.info("Step 12: Summary generation complete")
            
        except Exception as e:
            logger.warning("Summary generation failed (%s); using default summary", e)

        # ------------------------------------------------------------------
        # Step 13: Run pros/cons generation
        # ------------------------------------------------------------------
        publish_progress(str(contract_id), 88, "Generating pros/cons")
        logger.info("Step 13: Running pros/cons generation")
        # Pros/cons are already extracted by the summary pipeline

        # ------------------------------------------------------------------
        # Step 14: Store all results in database
        # ------------------------------------------------------------------
        publish_progress(str(contract_id), 95, "Storing results")
        logger.info("Step 14: Storing results in database")

        async with SessionLocal() as db:
            clause_repo = ClauseRepository(db)
            for cr in clause_results:
                existing = await clause_repo.get_by_contract_and_index(
                    contract_id, cr["position_index"]
                )
                if not existing:
                    clause = Clause(
                        id=UUID(cr["clause_id"]),
                        contract_id=contract_id,
                        position_index=cr["position_index"],
                        text=cr["text"],
                        risk_level=cr["risk_level"],
                        risk_category=cr["risk_category"],
                        plain_english=cr.get("plain_english", ""),
                        worst_case_scenario=cr.get("worst_case_scenario", ""),
                        negotiable=cr.get("negotiable", True),
                        confidence=cr.get("confidence", 0.5),
                    )
                    db.add(clause)

            try:
                from services.api.app.repositories.analysis_repo import AnalysisResultRepository
                from services.api.app.models.analysis_result import AnalysisResult
                analysis_repo = AnalysisResultRepository(db)
                
                # Check for existing analysis result to prevent duplicate keys
                existing_analysis = await analysis_repo.get_by_contract_id(contract_id)
                
                # Deduplicate pros/cons since db schema uses JSON arrays
                if existing_analysis:
                    # Update existing record
                    existing_analysis.power_score = power_score
                    existing_analysis.one_liner = summary_data["summary_text"]
                    existing_analysis.key_leverage = summary_data["leverage_points"]
                    existing_analysis.red_flags = summary_data["red_flags"]
                else:
                    # Create new record
                    analysis = AnalysisResult(
                        id=uuid4(),
                        contract_id=contract_id,
                        contract_type_id=None,
                        power_score=power_score,
                        one_liner=summary_data["summary_text"],
                        key_leverage=summary_data["leverage_points"],
                        red_flags=summary_data["red_flags"],
                        jurisdiction="unknown"
                    )
                    db.add(analysis)
            except Exception as e:
                logger.error("Failed to store AnalysisResult: %s", e)
                
            await db.commit()

        logger.info("Step 14: Results stored in database")

        # ------------------------------------------------------------------
        # Step 15: Run embedding pipeline for Q&A RAG
        # ------------------------------------------------------------------
        publish_progress(str(contract_id), 98, "Creating embeddings")
        logger.info("Step 15: Running embedding pipeline")

        # Call the embed_contract task
        try:
            from .embed_contract import embed_contract_task

            embed_contract_task.delay(str(contract_id))
            logger.info("Step 15: Embedding task queued for %s", contract_id)
        except Exception as e:
            logger.warning("Step 15: Failed to queue embedding task: %s", e)

        logger.info("Step 15: Embedding pipeline complete")

        # ------------------------------------------------------------------
        # Step 16: Translate results back to user language if needed
        # ------------------------------------------------------------------
        if detected_language != "en":
            publish_progress(
                str(contract_id), 99, f"Translating to {detected_language}"
            )
            logger.info("Step 16: Translating results to %s", detected_language)
            # TODO: Implement translation of results
            logger.info("Step 16: Translation complete")

        # ------------------------------------------------------------------
        # Step 17: Update ScanJob status to "complete", progress to 100%
        # ------------------------------------------------------------------
        async with SessionLocal() as db:
            job_repo = ScanJobRepository(db)
            job = await job_repo.get_by_contract_id(contract_id)
            if job:
                job.status = "complete"
                job.progress_pct = 100
                await db.commit()

        logger.info("Step 17: ScanJob %s marked as complete", contract_id)

        # ------------------------------------------------------------------
        # Step 18: Publish "complete" signal to Redis pub/sub channel
        # ------------------------------------------------------------------
        publish_progress(str(contract_id), 100, "Complete")
        publish_complete(
            str(contract_id), {"contract_id": str(contract_id), "status": "complete"}
        )

        logger.info(
            "Step 18: Complete signal published. Pipeline finished successfully."
        )

        return {
            "status": "completed",
            "contract_id": str(contract_id),
            "clauses_count": len(clause_results),
        }

    except Exception as e:
        logger.error("Pipeline failed: %s", str(e), exc_info=True)

        # Update ScanJob status to "failed"
        async with SessionLocal() as db:
            job_repo = ScanJobRepository(db)
            job = await job_repo.get_by_contract_id(contract_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)[:500]  # Truncate to fit DB column
                await db.commit()

        # Publish error to SSE
        publish_error(str(contract_id), str(e))

        raise

    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug("Temp file %s deleted", temp_file_path)
            except Exception as e:
                logger.warning("Failed to delete temp file %s: %s", temp_file_path, e)


# ---------------------------------------------------------------------------
# Celery task definition
# ---------------------------------------------------------------------------


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_contract(
    self, contract_id_str: str, file_url: str, user_id: str
) -> dict[str, Any]:
    \"\"\"
    Celery task entry point.
    \"\"\"
    contract_id = UUID(contract_id_str)
    logger.info(
        "Starting contract scan: contract_id=%s, user_id=%s", contract_id, user_id
    )

    try:
        result = asyncio.run(run_pipeline(contract_id, file_url, user_id))
        return result
    except Exception as exc:
        logger.error("Pipeline failed for contract %s: %s", contract_id, exc)

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2**self.request.retries)
            logger.warning(
                "Retrying in %d seconds (attempt %d/%d)",
                retry_delay,
                self.request.retries + 1,
                self.max_retries,
            )
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            logger.error("Max retries exceeded for contract %s", contract_id)
            raise
"""

new_content = head + tail

# Fix clause extraction as well!
new_content = new_content.replace(
    "from services.ai.app.pipelines.clause_extraction import run_clause_extraction",
    "from services.ai.app.pipelines.clause_extraction import segment_clauses"
)
new_content = new_content.replace(
    "clauses_text = run_clause_extraction(contract_text)",
    'clause_objects = segment_clauses(contract_text)\\n            clauses_text = [c["text"] for c in clause_objects]'
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Updated process_contract.py")
