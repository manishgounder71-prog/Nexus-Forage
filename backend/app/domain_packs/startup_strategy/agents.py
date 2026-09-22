from typing import List, Dict, Any

def get_startup_strategy_agents() -> List[Dict[str, Any]]:
    return [
        {
            "agent_id": "strategy_su_01",
            "name": "Strategy Agent",
            "division": "Strategy",
            "specialization": "Venture Capital Strategy, Business Model Pivots & Board Alignment",
            "capabilities": ["mission_coordination", "command", "product_strategy"],
            "reputation_score": 0.98,
            "speed_score": 0.94,
            "cost_weight": 0.7
        },
        {
            "agent_id": "market_su_01",
            "name": "Market Agent",
            "division": "Intelligence",
            "specialization": "Competitive Landscape, TAM Estimation & ICP Persona Validation",
            "capabilities": ["market_analysis", "incident_intelligence"],
            "reputation_score": 0.95,
            "speed_score": 0.91,
            "cost_weight": 0.75
        },
        {
            "agent_id": "financial_su_01",
            "name": "Financial Agent",
            "division": "Risk & Operations",
            "specialization": "Cash Burn Modeling, Unit Economics (CAC/LTV) & Bridge Round Structuring",
            "capabilities": ["financial_modeling", "resource_allocation"],
            "reputation_score": 0.97,
            "speed_score": 0.95,
            "cost_weight": 0.8
        },
        {
            "agent_id": "product_su_01",
            "name": "Product Agent",
            "division": "Intelligence",
            "specialization": "Feature Retention Analysis, Roadmap Pruning & MVP Scoping",
            "capabilities": ["product_strategy", "system_analysis"],
            "reputation_score": 0.94,
            "speed_score": 0.90,
            "cost_weight": 0.7
        },
        {
            "agent_id": "growth_su_01",
            "name": "Growth Agent",
            "division": "Strategy",
            "specialization": "Go-to-Market Velocity, Sales Funnel Conversion & Outbound Traction",
            "capabilities": ["growth_acceleration", "stakeholder_communication"],
            "reputation_score": 0.93,
            "speed_score": 0.92,
            "cost_weight": 0.75
        },
        {
            "agent_id": "redteam_su_01",
            "name": "Adversarial Red Team Agent",
            "division": "Risk & Operations",
            "specialization": "Assumption Stress-Testing, Downside Risk Audit & Counter-Thesis Formulation",
            "capabilities": ["adversarial_red_teaming", "risk_assessment"],
            "reputation_score": 0.96,
            "speed_score": 0.93,
            "cost_weight": 0.8
        }
    ]
