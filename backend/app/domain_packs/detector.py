import re
from typing import List, Dict, Any, Tuple
from app.domain_packs.capability_extractor import capability_extractor

DOMAIN_WEIGHTS: Dict[str, Dict[str, float]] = {
    "SOFTWARE_INCIDENT": {
        "production": 3.0, "deployment": 3.5, "deploy": 3.0, "outage": 3.0, "database": 2.5,
        "server": 2.5, "bug": 2.5, "exception": 2.0, "crash": 3.0, "commit": 2.0,
        "ci/cd": 3.0, "rollback": 3.5, "latency": 2.5, "500 error": 3.5, "service down": 3.5,
        "microservice": 2.5, "kubernetes": 2.5, "cluster": 2.0, "api gateway": 2.5,
        "memory leak": 3.0, "segfault": 3.0, "regression": 2.5, "hotfix": 2.5,
        "incident": 2.5, "kafka": 3.0, "postgres": 2.5, "down": 2.5, "error": 2.0
    },
    "ENTERPRISE_CRISIS": {
        "payment": 3.5, "billing": 3.0, "stripe": 3.0, "revenue loss": 3.0, "financial loss": 3.0,
        "cyber-attack": 3.5, "power grid": 3.5, "substation": 3.5, "scada": 3.5, "ransomware": 4.0,
        "breach": 3.5, "blackout": 3.5, "security incident": 3.5, "compliance": 2.5, "regulator": 2.5,
        "sec": 2.5, "lawsuit": 2.5, "reputation": 2.0, "board": 2.0, "disaster recovery": 3.0,
        "infrastructure disruption": 3.0, "executive": 2.0, "operational crisis": 3.0,
        "hospital": 3.5, "ehr": 3.5, "hack": 3.5, "extortion": 3.5
    },
    "STARTUP_STRATEGY": {
        "runway": 4.0, "burn rate": 3.5, "cash": 2.5, "fundraising": 3.5, "pivot": 3.5,
        "seed": 3.0, "series a": 3.5, "investors": 3.0, "venture": 3.0, "cac": 3.0,
        "ltv": 3.0, "unit economics": 3.5, "product-market fit": 3.5, "growth": 2.5,
        "reduce costs": 3.0, "founder": 2.5, "startup": 3.5, "valuation": 3.0,
        "competitor": 2.5, "go-to-market": 3.0, "gtm": 3.0, "pricing": 2.5,
        "b2b": 3.5, "saas": 3.5, "churn": 3.5, "mrr": 3.5, "arr": 3.5, "retention": 3.0
    },
    "SUPPLY_CHAIN": {
        "supply chain": 4.5, "supply": 3.5, "supplier": 4.0, "vendor": 3.0, "deliveries": 3.5, "delivery": 2.5, "port": 3.5,
        "cargo": 3.5, "freight": 3.5, "shipment": 3.0, "warehouse": 3.0, "logistics": 3.5,
        "sourcing": 3.5, "procurement": 3.0, "container": 3.0, "demurrage": 3.5,
        "vessel": 3.0, "customs": 3.0, "stockout": 3.5, "inventory": 3.0, "choke point": 3.0,
        "manufacturing": 2.5, "factory": 2.5, "shortage": 3.5, "lead time": 3.0,
        "wafer": 3.5, "semiconductor": 3.5, "foundry": 3.5, "delay": 3.0, "delays": 3.0
    },
    "UNIVERSITY_OPERATIONS": {
        "exam": 4.0, "examination": 4.0, "portal": 3.0, "students": 3.5, "student": 3.0,
        "faculty": 3.0, "campus": 3.5, "semester": 3.0, "grades": 3.0, "grading": 3.0,
        "timetable": 3.0, "proctor": 3.5, "hall": 2.5, "university": 4.0, "college": 3.5,
        "academic": 3.0, "canvas": 3.5, "moodle": 3.5, "blackboard": 3.5, "admissions": 4.0,
        "course": 2.5, "registrar": 3.0, "applicant": 3.5, "ddos": 3.0
    }
}

class DomainDetector:
    def detect_domain(self, prompt: str) -> Dict[str, Any]:
        lowered = prompt.lower()
        scores: Dict[str, float] = {d: 0.1 for d in DOMAIN_WEIGHTS}

        for domain, kw_map in DOMAIN_WEIGHTS.items():
            for kw, weight in kw_map.items():
                if kw in lowered:
                    scores[domain] += weight

        sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_domain, top_score = sorted_domains[0]
        second_domain, second_score = sorted_domains[1]

        # Calculate softmax-like confidence
        total = sum(s for _, s in sorted_domains)
        if total > 0:
            confidence = round(min(0.98, max(0.65, top_score / total * 1.5)), 2)
        else:
            confidence = 0.70

        # Hybrid detection: if second domain is also strong (> 45% of top score)
        is_hybrid = False
        secondary_domains = []
        if second_score >= 3.0 and second_score >= (top_score * 0.45):
            is_hybrid = True
            secondary_domains.append(second_domain)

        # Domain explanation summary
        reasoning_map = {
            "SOFTWARE_INCIDENT": "Production and software infrastructure failure detected with immediate stability risks.",
            "ENTERPRISE_CRISIS": "Critical enterprise operations disruption, payment platform, or security crisis detected.",
            "STARTUP_STRATEGY": "Strategic venture decisions regarding runway, fundraising, market viability, or business pivot.",
            "SUPPLY_CHAIN": "Supply chain, freight logistics, vendor disruption, or critical inventory bottleneck detected.",
            "UNIVERSITY_OPERATIONS": "Academic operational crisis involving examination systems, campus logistics, or student impact."
        }

        # Dynamic reasoning summary
        reasoning_summary = reasoning_map.get(top_domain, "Complex operational mission requiring autonomous multi-agent orchestration.")
        if is_hybrid:
            reasoning_summary += f" Cross-domain impact identified with {second_domain.replace('_', ' ').title()}."

        extracted_capabilities = capability_extractor.extract_capabilities(prompt, domain_hint=top_domain)

        # If hybrid, merge secondary domain capabilities
        if is_hybrid:
            secondary_caps = capability_extractor.extract_capabilities(prompt, domain_hint=second_domain)
            for cap in secondary_caps:
                if cap not in extracted_capabilities:
                    extracted_capabilities.append(cap)

        return {
            "primary_domain": top_domain,
            "confidence": confidence,
            "is_hybrid": is_hybrid,
            "secondary_domains": secondary_domains,
            "all_scores": {k: round(v, 2) for k, v in sorted_domains},
            "reasoning_summary": reasoning_summary,
            "required_capabilities": extracted_capabilities
        }

domain_detector = DomainDetector()
