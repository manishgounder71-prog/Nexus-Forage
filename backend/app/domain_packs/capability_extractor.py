from typing import List, Set, Dict

CAPABILITY_KEYWORDS: Dict[str, List[str]] = {
    # Software Incident capabilities
    "root_cause_analysis": ["root cause", "stack trace", "crash", "bug", "regression", "log", "exception", "error code", "segfault", "memory leak"],
    "infrastructure_analysis": ["server", "cluster", "kubernetes", "pod", "cloud", "aws", "gcp", "azure", "docker", "cpu", "ram", "network", "substation", "scada", "plc", "switchboard", "grid"],
    "dependency_analysis": ["dependency", "microservice", "downstream", "upstream", "database", "redis", "kafka", "queue", "api", "integration", "third-party", "vendor"],
    "rollback_planning": ["rollback", "revert", "deployment", "deploy", "release", "commit", "ci/cd", "pipeline", "hotfix", "patch", "blue-green", "canary"],
    "risk_assessment": ["risk", "blackout", "data loss", "security", "vulnerability", "breach", "exploit", "compliance", "audit", "failure"],
    "stakeholder_communication": ["communication", "notification", "status page", "executive", "press", "pr", "customer update", "students", "faculty", "board", "investors"],
    
    # Enterprise Crisis capabilities
    "incident_intelligence": ["crisis", "investigation", "threat", "anomaly", "cyber-attack", "ransomware", "ddos", "breach", "payment failure", "billing"],
    "operational_containment": ["operations", "containment", "isolation", "air-gap", "switchover", "failover", "business continuity", "disaster recovery"],
    "resource_allocation": ["resource", "budget", "bandwidth", "capacity", "personnel", "emergency team", "backup", "server keys"],
    "regulatory_compliance": ["legal", "compliance", "gdpr", "sec", "audit", "liability", "sanction", "fine"],
    
    # Startup Strategy capabilities
    "market_analysis": ["market", "competitor", "tam", "customer demand", "product-market fit", "positioning", "pricing", "churn"],
    "financial_modeling": ["runway", "cash burn", "burn rate", "fundraising", "valuation", "seed", "series a", "unit economics", "cac", "ltv", "revenue"],
    "product_strategy": ["pivot", "feature", "roadmap", "mvp", "product redesign", "tech stack", "user retention"],
    "growth_acceleration": ["growth", "sales", "go-to-market", "gtm", "acquisition", "conversion", "marketing", "pipeline"],
    "adversarial_red_teaming": ["red team", "stress test", "worst case", "flaw", "assumption", "blindspot", "counter-thesis"],
    
    # Supply Chain capabilities
    "supplier_analysis": ["supplier", "vendor", "distributor", "oem", "factory", "procurement", "source", "single point of failure"],
    "logistics_rerouting": ["freight", "port", "shipment", "cargo", "vessel", "customs", "strike", "transit", "rail", "trucking", "air cargo", "warehouse"],
    "impact_assessment": ["inventory", "stockout", "delay", "sla breach", "backorder", "production halt", "lead time"],
    "alternative_sourcing": ["secondary supplier", "alternative sourcing", "dual vendor", "spot market", "emergency contract"],
    "cost_optimization": ["tariffs", "expedited shipping", "demurrage", "freight cost", "unit margin", "contract renegotiation"],
    
    # University Operations capabilities
    "technical_recovery": ["portal", "lms", "moodle", "canvas", "exam portal", "registration", "student database", "sis", "wifi", "authentication", "sso"],
    "student_impact_mitigation": ["student", "examination", "exam", "grade", "assessment", "proctoring", "reschedule", "fairness", "academic integrity"],
    "scheduling_coordination": ["schedule", "timetable", "hall", "proctor", "semester", "deadline", "extension", "session"]
}

class CapabilityExtractor:
    def extract_capabilities(self, prompt: str, domain_hint: str = "") -> List[str]:
        lowered = prompt.lower()
        extracted: Set[str] = set()

        for cap, keywords in CAPABILITY_KEYWORDS.items():
            for kw in keywords:
                if kw in lowered:
                    extracted.add(cap)
                    break

        # Fallback baseline capabilities if too few extracted
        if len(extracted) < 3:
            if domain_hint == "SOFTWARE_INCIDENT":
                extracted.update(["root_cause_analysis", "infrastructure_analysis", "rollback_planning", "risk_assessment"])
            elif domain_hint == "ENTERPRISE_CRISIS":
                extracted.update(["incident_intelligence", "operational_containment", "risk_assessment", "stakeholder_communication"])
            elif domain_hint == "STARTUP_STRATEGY":
                extracted.update(["financial_modeling", "product_strategy", "market_analysis", "adversarial_red_teaming"])
            elif domain_hint == "SUPPLY_CHAIN":
                extracted.update(["supplier_analysis", "logistics_rerouting", "impact_assessment", "alternative_sourcing"])
            elif domain_hint == "UNIVERSITY_OPERATIONS":
                extracted.update(["technical_recovery", "student_impact_mitigation", "scheduling_coordination", "stakeholder_communication"])
            else:
                extracted.update(["incident_intelligence", "risk_assessment", "stakeholder_communication", "operational_containment"])

        return sorted(list(extracted))

capability_extractor = CapabilityExtractor()
