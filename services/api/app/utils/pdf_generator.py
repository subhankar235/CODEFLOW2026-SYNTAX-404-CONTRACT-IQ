import os
import json
from datetime import datetime
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from pathlib import Path

# Paths
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
I18N_DIR = TEMPLATES_DIR / "i18n"
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "reports"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_i18n(language: str) -> Dict[str, str]:
    """Load i18n labels for the report."""
    file_path = I18N_DIR / f"{language}.json"
    if not file_path.exists():
        file_path = I18N_DIR / "en.json"
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

async def generate_contract_report(
    contract_data: Dict[str, Any],
    language: str = "en"
) -> str:
    """
    Generate a PDF report for a contract.
    Returns the file path to the generated PDF.
    """
    # 1. Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    
    # 2. Prepare context
    i18n_labels = load_i18n(language)
    
    context = {
        "language": language,
        "i18n": i18n_labels,
        "title": f"Analysis Report - {contract_data['original_filename']}",
        "logo_url": "https://raw.githubusercontent.com/soumojit-D48/Legal-Tech/main/docs/assets/logo.png", # Placeholder
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        **contract_data
    }

    # 3. Render HTML components
    # We combine templates manually to have better control over structure
    base_template = env.get_template("base.html")
    
    # Render sections
    cover_html = env.get_template("cover.html").render(context)
    summary_html = env.get_template("summary.html").render(context)
    clauses_html = env.get_template("clauses.html").render(context)
    
    # Conditional sections
    power_html = ""
    if contract_data.get("power"):
        power_html = env.get_template("power.html").render(context)
        
    precedent_html = ""
    if contract_data.get("precedents"):
        precedent_html = env.get_template("precedent.html").render(context)
        
    counter_offers_html = ""
    if contract_data.get("counter_offers"):
        counter_offers_html = env.get_template("counter_offers.html").render(context)

    # Final combined content
    main_content = f"{cover_html}{summary_html}{clauses_html}{power_html}{precedent_html}{counter_offers_html}"
    
    final_html = base_template.render({**context, "content": main_content})

    # 4. Convert to PDF
    report_filename = f"report_{contract_data['contract_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    report_path = OUTPUT_DIR / report_filename
    
    HTML(string=final_html).write_pdf(str(report_path))
    
    return str(report_path)
