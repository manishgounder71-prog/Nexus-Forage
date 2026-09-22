from typing import List, Dict, Any
from app.domain_packs.base import WorkflowTaskTemplate

def generate_startup_strategy_workflow(prompt: str, agents: List[Dict[str, Any]]) -> List[WorkflowTaskTemplate]:
    lowered = prompt.lower()
    
    if "competitor" in lowered or "free tier" in lowered or "pricing" in lowered:
        task_1_name = "Competitor Pricing & Moat Vulnerability Analysis"
        task_1_desc = "Evaluate competitor free-tier cost structure, pricing pressure, and customer retention metrics."
        task_3_name = "Enterprise Workflow & Feature Moat Audit"
        task_3_desc = "Isolate proprietary high-ACV workflows that cannot be replicated by basic free competitor tiers."
    elif "expansion" in lowered or "europe" in lowered or "international" in lowered or "gdpr" in lowered:
        task_1_name = "Regional Market Sizing & Regulatory Compliance Audit"
        task_1_desc = "Evaluate target territory compliance (e.g. GDPR), localization needs, and channel partner landscape."
        task_3_name = "Lighthouse Customer Pipeline & GTM Infrastructure"
        task_3_desc = "Structure pilot contracts, localized pricing, and regional deployment infrastructure."
    elif "founder" in lowered or "cto" in lowered or "resigned" in lowered or "engineer" in lowered:
        task_1_name = "Codebase Architecture & Technical Context Audit"
        task_1_desc = "Map critical system dependencies, access keys, and knowledge transfer checkpoints."
        task_3_name = "Engineering Pod Restructuring & Retention Equity Plan"
        task_3_desc = "Design internal lead promotion path, fractional domain advisory, and refreshed retention equity pool."
    else:
        task_1_name = "Runway & Cash Burn Financial Modeling"
        task_1_desc = "Calculate exact zero-cash date, scenario burn curves, and cost reduction levers."
        task_3_name = "Product Engagement & Retention Feature Audit"
        task_3_desc = "Isolate sticky core features vs vanity roadmap items to prepare high-leverage pivot."

    return [
        WorkflowTaskTemplate(
            task_id="su_task_01",
            name=task_1_name,
            preferred_capability="financial_modeling",
            role_title="Financial Agent",
            dependencies=[],
            description=task_1_desc
        ),
        WorkflowTaskTemplate(
            task_id="su_task_02",
            name="Market Demand & Strategic Positioning Analysis",
            preferred_capability="market_analysis",
            role_title="Market Agent",
            dependencies=[],
            description="Evaluate ICP willingness-to-pay, market dynamics, and customer segmentation."
        ),
        WorkflowTaskTemplate(
            task_id="su_task_03",
            name=task_3_name,
            preferred_capability="product_strategy",
            role_title="Product Agent",
            dependencies=[],
            description=task_3_desc
        ),
        WorkflowTaskTemplate(
            task_id="su_task_04",
            name="GTM Funnel Redirection & Sales Pipeline Modeling",
            preferred_capability="growth_acceleration",
            role_title="Growth Agent",
            dependencies=["su_task_01", "su_task_02", "su_task_03"],
            description="Model conversion timelines, pilot customer velocity, and unit economics."
        ),
        WorkflowTaskTemplate(
            task_id="su_task_05",
            name="Parliament Venture Deliberation & Adversarial Red Team Stress-Test",
            preferred_capability="adversarial_red_teaming",
            role_title="Strategy Agent",
            dependencies=["su_task_04"],
            description="Deliberate core strategic options under adversarial Red Team stress-testing."
        )
    ]
