from typing import List, Dict, Any

def get_supply_chain_agents() -> List[Dict[str, Any]]:
    return [
        {
            "agent_id": "commander_sc",
            "name": "Supply Chain Commander",
            "division": "Strategy",
            "specialization": "Global Logistics Operations, Freight Orchestration & Tier-1 Vendor Management",
            "capabilities": ["mission_coordination", "command", "supplier_analysis"],
            "reputation_score": 0.98,
            "speed_score": 0.94,
            "cost_weight": 0.7
        },
        {
            "agent_id": "supplier_sc_01",
            "name": "Supplier Analysis Agent",
            "division": "Intelligence",
            "specialization": "Vendor Solvency Audit, OEM Contract Feasibility & Single Point of Failure Triage",
            "capabilities": ["supplier_analysis", "incident_intelligence"],
            "reputation_score": 0.96,
            "speed_score": 0.92,
            "cost_weight": 0.75
        },
        {
            "agent_id": "impact_sc_01",
            "name": "Operational Impact Agent",
            "division": "Risk & Operations",
            "specialization": "Inventory Stockout Modeling, Assembly Line Halts & SLA Breach Quantification",
            "capabilities": ["impact_assessment", "risk_assessment"],
            "reputation_score": 0.95,
            "speed_score": 0.91,
            "cost_weight": 0.8
        },
        {
            "agent_id": "alt_source_sc_01",
            "name": "Alternative Sourcing Agent",
            "division": "Intelligence",
            "specialization": "Secondary Vendor Qualification, Spot Market Procurement & Dual Sourcing",
            "capabilities": ["alternative_sourcing", "resource_allocation"],
            "reputation_score": 0.94,
            "speed_score": 0.93,
            "cost_weight": 0.75
        },
        {
            "agent_id": "cost_sc_01",
            "name": "Cost Optimization Agent",
            "division": "Risk & Operations",
            "specialization": "Freight Demurrage Mitigation, Air/Rail Expedited Tariff Analysis & Unit Margins",
            "capabilities": ["cost_optimization", "financial_modeling"],
            "reputation_score": 0.93,
            "speed_score": 0.90,
            "cost_weight": 0.7
        },
        {
            "agent_id": "risk_sc_01",
            "name": "Supply Risk Agent",
            "division": "Risk & Operations",
            "specialization": "Geopolitical Choke Point Audit, Customs Tariff Exposure & Lead-Time Variance",
            "capabilities": ["risk_assessment", "logistics_rerouting"],
            "reputation_score": 0.96,
            "speed_score": 0.91,
            "cost_weight": 0.8
        }
    ]
