from typing import List, Dict, Any

def build_supply_chain_executive_report(
    prompt: str,
    consensus: Dict[str, Any],
    selected_strategy: str,
    simulations: List[Dict[str, Any]],
    agent_findings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    return {
        "title": "🚚 SUPPLY CHAIN & LOGISTICS RECOVERY REPORT",
        "domain": "SUPPLY_CHAIN",
        "situation": prompt,
        "severity": "🔴 CRITICAL LOGISTICS DISRUPTION",
        "recommended_strategy": consensus.get("selected_strategy", "PLAN B: Secondary Sourcing Split + Automated Inland Rail Bypass"),
        "estimated_recovery": "~7-12 Days Lead Time",
        "confidence": f"{int(consensus.get('consensus_score', 0.91) * 100)}%",
        "why_this_strategy": "Splits procurement 60/40 between certified secondary regional suppliers while rerouting container freight through inland rail junctions to circumvent port strike bottlenecks with 88% cost savings vs air cargo.",
        "affected_operations": [
            "Manufacturing Assembly Line 3 (Components: Power Harness & Control Microcontrollers)",
            "Finished Goods Delivery SLAs for 14 Tier-1 OEM Customers",
            "Warehouse Buffer Depleted to 4.5 Days of Buffer Stock"
        ],
        "alternative_options": [
            {
                "option": "PLAN A: Emergency Heavy Fleet Expedited Trucking",
                "lead_time": "3-5 Days",
                "cost_premium": "+$18,000 / shipment",
                "risk": "High (Highway choke points & driver shortages)"
            },
            {
                "option": "PLAN B: Secondary Supplier Dual-Allocation & Rail Corridor",
                "lead_time": "7 Days",
                "cost_premium": "+$4,500 / shipment",
                "risk": "Low (Verified secondary tooling and rail capacity)"
            },
            {
                "option": "PLAN C: Air Freight Emergency Cargo Airlift",
                "lead_time": "24 Hours",
                "cost_premium": "+$65,000 / shipment",
                "risk": "Extreme (Prohibitive cost per unit margin)"
            }
        ],
        "cost_comparison": {
            "baseline_ocean_freight": "$3,200 / TEU",
            "plan_b_rail_secondary": "$5,400 / TEU (+$2.2k premium)",
            "plan_c_air_airlift": "$28,500 / TEU (+$25.3k premium)",
            "projected_cost_variance": "Within 8% of emergency reserve budget"
        },
        "timeline_days": 7,
        "supply_risks": [
            "Secondary vendor tooling calibration variance (+/- 0.2mm tolerance check required)",
            "Rail freight junction congestion at regional transfer terminal",
            "Supplier solvency dispute resulting in legal lien on in-transit raw materials"
        ],
        "recommended_recovery_plan": "Execute Plan B: Immediately issue purchase orders for 60% volume to secondary qualified supplier in Michigan and 40% to Ontario facility; transfer in-transit containers from port to electrified inland rail hub.",
        "dissenting_opinions": consensus.get("dissenting_agents", ["Operational Impact Agent: Urged 100% air freight for 1st batch to prevent line stoppage"]),
        "red_team_findings": [
            "Identified risk: Single secondary supplier could encounter capacity limits if volume exceeds 8,000 units.",
            "Mitigation: 60/40 dual vendor split enforces competitive redundancy."
        ],
        "lessons_learned": [
            "Mandate active dual-sourcing contracts for all single-source BOM components.",
            "Enforce real-time IoT GPS telemetry on multi-modal freight shipments."
        ]
    }
