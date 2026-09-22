from typing import Dict, List, Optional
from app.agents.runtime import LyzrAgentRuntimeAdapter

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, LyzrAgentRuntimeAdapter] = {}
        self._init_default_registry()

    def _init_default_registry(self):
        all_agents_def = [
            # Cross-Domain & Core Command Agents
            ("commander_01", "Mission Commander", "Strategy", "Mission Lifecycle Coordination & Adaptive Leadership", ["mission_coordination", "command", "operational_containment"], 0.99, 0.95, 0.7),
            ("architect_01", "Organization Architect", "Strategy", "AI Team Dynamic Selection & Topology Formation", ["agent_selection", "restructuring", "planning"], 0.96, 0.94, 0.7),
            ("memory_01", "Qdrant Memory Indexer", "Intelligence", "Vector Memory, HNSW & RAG Retrieval", ["memory_lookup", "vector_search"], 0.97, 0.98, 0.6),
            ("comms_01", "Communications Agent", "Strategy", "Stakeholder Communication & Crisis PR Protocol", ["stakeholder_communication"], 0.94, 0.95, 0.7),
            ("risk_01", "Risk Strategist Agent", "Risk & Operations", "Cross-Domain Adversarial Risk & Dependency Audit", ["risk_assessment", "dependency_analysis"], 0.95, 0.90, 0.8),
            ("red_team_01", "Adversarial Red Team Auditor", "Risk & Operations", "Stress-Testing, Vulnerability Injection & Plan Hardening", ["adversarial_analysis", "red_teaming", "adversarial_red_teaming"], 0.96, 0.93, 0.8),
            ("reflection_01", "Reflection Agent", "Intelligence", "Post-Mission Learning, Reputation Scoring & Memory Induction", ["post_mission_reflection", "reputation"], 0.97, 0.94, 0.6),
            ("resource_01", "Operations & Resource Manager", "Risk & Operations", "Resource Scheduling & Infrastructure Bandwidth Allocation", ["resource_planning", "resource_allocation", "infrastructure"], 0.95, 0.92, 0.75),

            # Software Incident Response Domain Agents
            ("root_cause_01", "Root Cause Analyst Agent", "Intelligence", "Log Inspection, Stack Tracing & Regression Triaging", ["root_cause_analysis", "incident_analysis", "system_analysis"], 0.96, 0.92, 0.75),
            ("infra_sw_01", "Infrastructure Agent", "Infrastructure", "Kubernetes Cluster, Load Balancer & Database Health Audit", ["infrastructure_analysis", "infrastructure_recovery"], 0.95, 0.91, 0.8),
            ("dep_sw_01", "Dependency Agent", "Intelligence", "Downstream Microservice & Third-Party API Mapping", ["dependency_analysis", "incident_intelligence"], 0.93, 0.90, 0.7),
            ("rollback_sw_01", "Rollback Agent", "Strategy", "Canary Rollback, Blue-Green Switch & Release Recovery", ["rollback_planning", "recovery_strategy"], 0.97, 0.96, 0.85),

            # Enterprise Crisis Domain Agents
            ("intel_01", "Incident Intelligence Agent", "Intelligence", "Threat Triage, Anomaly Telemetry & Forensic Impact Quantification", ["incident_intelligence", "incident_analysis"], 0.96, 0.93, 0.75),
            ("ops_ec_01", "Operations Containment Agent", "Infrastructure", "Disaster Recovery, Air-Gap Containment & Secondary Gateway Switchover", ["operational_containment", "infrastructure_recovery"], 0.95, 0.92, 0.8),
            ("compliance_ec_01", "Regulatory Compliance Agent", "Risk & Operations", "Regulatory Sanctions, Legal Exposure & Financial Liability Audit", ["regulatory_compliance", "risk_assessment"], 0.94, 0.88, 0.8),
            ("scada_01", "SCADA Security Specialist", "Cyber Security", "Substation PLC & Air-Gap Hardware Defense", ["cyber_defense", "grid_isolation", "incident_intelligence"], 0.98, 0.94, 0.85),
            ("grid_01", "Grid Frequency Balancer", "Infrastructure", "Power Distribution & Feeder Load Balancing", ["failover_planning", "infrastructure_recovery", "operational_containment"], 0.95, 0.93, 0.8),

            # Startup Strategy Domain Agents
            ("strategy_su_01", "Startup Strategy Agent", "Strategy", "Venture Capital Strategy, Business Model Pivots & Runway Extension", ["product_strategy", "recovery_strategy", "planning"], 0.97, 0.94, 0.7),
            ("market_su_01", "Market Analysis Agent", "Intelligence", "Competitive Landscape, TAM Estimation & ICP Validation", ["market_analysis", "incident_intelligence"], 0.95, 0.91, 0.75),
            ("financial_su_01", "Financial Modeling Agent", "Risk & Operations", "Cash Burn Modeling, Unit Economics (CAC/LTV) & Bridge Round Structuring", ["financial_modeling", "resource_allocation", "cost_optimization"], 0.98, 0.95, 0.8),
            ("growth_su_01", "Growth Acceleration Agent", "Strategy", "Go-to-Market Velocity, Sales Funnel Conversion & Outbound Traction", ["growth_acceleration", "stakeholder_communication"], 0.93, 0.92, 0.75),

            # Supply Chain Disruption Domain Agents
            ("supplier_sc_01", "Supplier Analysis Agent", "Intelligence", "Vendor Solvency Audit, OEM Contract Feasibility & Single Point of Failure Triage", ["supplier_analysis", "incident_intelligence"], 0.96, 0.92, 0.75),
            ("impact_sc_01", "Operational Impact Agent", "Risk & Operations", "Inventory Stockout Modeling, Assembly Line Halts & SLA Breach Quantification", ["impact_assessment", "risk_assessment"], 0.95, 0.91, 0.8),
            ("alt_source_sc_01", "Alternative Sourcing Agent", "Intelligence", "Secondary Vendor Qualification, Spot Market Procurement & Dual Sourcing", ["alternative_sourcing", "resource_allocation"], 0.94, 0.93, 0.75),
            ("cost_sc_01", "Cost Optimization Agent", "Risk & Operations", "Freight Demurrage Mitigation, Rail/Air Tariff Analysis & Unit Margins", ["cost_optimization", "financial_modeling", "logistics_rerouting"], 0.94, 0.90, 0.7),

            # University Operations Domain Agents
            ("tech_rec_univ_01", "Technical Recovery Agent", "Infrastructure", "LMS Exam Portal, Database Replicas, SSO Auth & Cloud Scalability", ["technical_recovery", "infrastructure_recovery", "infrastructure_analysis"], 0.96, 0.93, 0.8),
            ("student_univ_01", "Student Impact Agent", "Intelligence", "Academic Fairness, Special Accommodations, Stress Mitigation & Exam Integrity", ["student_impact_mitigation", "incident_intelligence"], 0.95, 0.91, 0.75),
            ("sched_univ_01", "Scheduling Coordinator Agent", "Strategy", "Exam Timetable Slot Reallocation, Hall Proctoring & Retake Staggering", ["scheduling_coordination", "resource_allocation"], 0.94, 0.92, 0.7)
        ]

        for agent_id, name, div, spec, caps, rep, speed, cost in all_agents_def:
            agent = LyzrAgentRuntimeAdapter(
                agent_id=agent_id,
                name=name,
                division=div,
                specialization=spec,
                capabilities=caps
            )
            agent.reputation_score = rep
            agent.speed_score = speed
            agent.cost_weight = cost
            self._agents[agent_id] = agent

    def get_all_agents(self) -> List[LyzrAgentRuntimeAdapter]:
        return list(self._agents.values())

    def get_agent_by_id(self, agent_id: str) -> Optional[LyzrAgentRuntimeAdapter]:
        return self._agents.get(agent_id)

    def find_agents_by_capability(self, capability: str) -> List[LyzrAgentRuntimeAdapter]:
        return [a for a in self._agents.values() if capability in a.capabilities]

agent_registry = AgentRegistry()
