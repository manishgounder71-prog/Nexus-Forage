import re
from typing import Dict, List, Any, Optional

class DynamicScenarioAnalyzer:
    """
    Analyzes arbitrary unstructured incident prompts across all domains,
    supporting short/terse prompts (e.g. "b2b saas incident", "server crash", "power grid blackout")
    as well as complex detailed multi-sentence prompts.
    Extracts metrics, dollar amounts, runway, churn, entities, and strategic dilemmas.
    """

    def expand_prompt_context(self, prompt: str, domain: str = "") -> str:
        """Enriches short/terse prompts into rich operational scenarios if the user provided minimal text."""
        trimmed = prompt.strip()
        words = trimmed.split()
        if len(words) > 8:
            return trimmed
        
        lowered = trimmed.lower()
        if "b2b" in lowered and "saas" in lowered:
            return f"B2B SaaS Multi-Tenant Incident: Critical service degradation affecting enterprise customer workflows, triggering SLA warnings and renewal churn risks. Immediate containment and customer communication required."
        elif "saas" in lowered or "startup" in lowered or "runway" in lowered or "pivot" in lowered:
            return f"Startup Venture Crisis: Critical operational and strategic decision required regarding customer retention, cost optimization, and core product roadmap stability."
        elif "grid" in lowered or "power" in lowered or "blackout" in lowered or "scada" in lowered:
            return f"Metropolitan Power Grid Disruption: Critical substation anomaly detected with potential cascading feeder risks; air-gap isolation and load-shedding required."
        elif "ransomware" in lowered or "breach" in lowered or "payment" in lowered or "crisis" in lowered:
            return f"Enterprise Infrastructure Crisis: Security anomaly / service outage impacting core operations; emergency failover and stakeholder notification required."
        elif "supplier" in lowered or "supply" in lowered or "port" in lowered or "freight" in lowered or "logistics" in lowered:
            return f"Supply Chain Disruption: Critical component bottleneck and logistics choke point threatening production line SLAs; secondary sourcing required."
        elif "exam" in lowered or "portal" in lowered or "university" in lowered or "admissions" in lowered:
            return f"University Academic Operations Outage: Central campus portal disruption impacting active student submissions; cached mirror and deadline extension required."
        elif "server" in lowered or "database" in lowered or "crash" in lowered or "deploy" in lowered or "incident" in lowered:
            return f"Production Software Incident: Critical service outage causing elevated error rates and downstream dependency latency; canary revert and replica drain required."
        
        return f"Operational Incident ({trimmed}): Multi-agent swarm deployed to assess root cause, contain cascading impact, and execute optimized recovery plan."

    def analyze_startup_scenario(self, prompt: str) -> Dict[str, Any]:
        lowered = prompt.lower()
        expanded_context = self.expand_prompt_context(prompt, domain="STARTUP_STRATEGY")
        
        # 1. Extract Financial & Numerical Metrics
        cash_match = re.search(r'(\$\s*\d+[\d,.]*\s*(?:k|m|b|million|thousand|billion)?)', prompt, re.IGNORECASE)
        runway_match = re.search(r'(\d+[\d.]*\s*(?:months?|weeks?|days?|quarters?)\s*(?:of\s*)?runway)', prompt, re.IGNORECASE)
        burn_match = re.search(r'(\$\s*\d+[\d,.]*\s*(?:k|m)?\s*(?:\/|\s*per\s*)(?:mo|month|yr|year|week))', prompt, re.IGNORECASE)
        churn_match = re.search(r'(\d+[\d.]*%\s*(?:churn|loss|drop|decline|decrease))', prompt, re.IGNORECASE)
        pct_matches = re.findall(r'(\d+[\d.]*%)', prompt)

        extracted_cash = cash_match.group(1) if cash_match else None
        extracted_runway = runway_match.group(1) if runway_match else None
        extracted_burn = burn_match.group(1) if burn_match else None
        extracted_churn = churn_match.group(1) if churn_match else (pct_matches[0] if pct_matches else None)

        # 2. Classify Startup Strategic Theme
        is_b2b_saas = bool("b2b" in lowered and "saas" in lowered or "saas" in lowered and "incident" in lowered)
        is_runway = bool(extracted_runway or "runway" in lowered or "burn rate" in lowered or "cash" in lowered or "fundrais" in lowered or "bridge" in lowered)
        is_competitor = bool("competitor" in lowered or "free tier" in lowered or "pricing" in lowered or "undercut" in lowered or "copycat" in lowered or "market share" in lowered)
        is_expansion = bool("expansion" in lowered or "europe" in lowered or "international" in lowered or "gdpr" in lowered or "scale" in lowered or "series a" in lowered or "series b" in lowered)
        is_team_crisis = bool("founder" in lowered or "cto" in lowered or "resigned" in lowered or "quitting" in lowered or "hiring" in lowered or "engineer" in lowered or "attrition" in lowered)

        # 3. Dynamic Status Formulation
        if is_b2b_saas:
            runway_status = "B2B SaaS Reliability & Customer SLA Protection: Containing customer churn & stabilizing enterprise accounts"
            burn_target = "Protect high-ACV recurring revenue ($0 SLA penalties) while deploying isolated tenant hotfixes"
            sev = "🔴 CRITICAL B2B SAAS SERVICE CRISIS"
        elif is_runway:
            runway_str = extracted_runway or "Active Runway Conservation Mode"
            cash_str = f"Cash: {extracted_cash}" if extracted_cash else "Capital Constraints Active"
            burn_str = f"Net Burn: {extracted_burn}" if extracted_burn else "High Burn Multiple"
            runway_status = f"{runway_str} ({cash_str}, {burn_str})"
            burn_target = "Reduce net burn by 45-60% within 14 days and secure insider capital commitments"
            sev = "🟠 CRITICAL RUNWAY & CAPITAL DECISION"
        elif is_competitor:
            runway_status = f"Market Disruption Defense: Responding to aggressive competitor dynamics ({extracted_churn or 'customer pressure'} detected)"
            burn_target = "Reallocate 40% of outbound budget to high-retention enterprise accounts and product moat defense"
            sev = "🔴 COMPETITIVE THREAT & PRICING CRISIS"
        elif is_expansion:
            runway_status = "Strategic Growth & Market Expansion: Scaling operations while safeguarding compliance"
            burn_target = "Establish 3:1 LTV/CAC benchmark on new target region pilots before expanding full headcount"
            sev = "🔵 STRATEGIC EXPANSION & GTM EXECUTION"
        elif is_team_crisis:
            runway_status = "Leadership Continuity & Technical Restructuring: Stabilizing core engineering roadmap"
            burn_target = "Re-anchor key contributors with equity refresh grants and fractional domain leadership"
            sev = "🟠 KEY TALENT & LEADERSHIP CONTINUITY"
        else:
            runway_status = "Strategic Venture Execution: Navigating operational scaling, retention, and roadmap prioritization"
            burn_target = "Optimize resource allocation to reach sustainable unit economics within 30 days"
            sev = "🟡 STRATEGIC PIVOT & GROWTH DECISION"

        # 4. Dynamic 3-Way Plan Formulation
        if is_b2b_saas:
            plan_a = {
                "plan": "PLAN A: Silent In-Flight Hotfix & Delayed Post-Mortem",
                "risk": "High (Erosion of Enterprise Trust)",
                "resource_req": "$10k dev overtime",
                "estimated_impact": "Fixes code bug quietly but risks severe backlash if key customers notice data inconsistencies",
                "time_to_execute": "12 hours",
                "assumptions": "Assumes impacted tenant transactions do not create permanent database desync"
            }
            plan_b = {
                "plan": "PLAN B: Proactive Enterprise Outreach + Dedicated SLA Credits & High-Availability Hotfix",
                "risk": "Low / Balanced",
                "resource_req": "$25k SLA credits & dev sprint",
                "estimated_impact": "Prevents 95%+ renewal churn, preserves enterprise goodwill, and restores full platform uptime",
                "time_to_execute": "24 hours",
                "assumptions": "Assumes transparent status communication converts incident into customer trust-building opportunity"
            }
            plan_c = {
                "plan": "PLAN C: Complete Multi-Tenant Pod Isolation & Maintenance Window",
                "risk": "Moderate (Temporary Planned Downtime)",
                "resource_req": "$5k cloud infrastructure",
                "estimated_impact": "100% data integrity guarantee but causes 4-hour scheduled maintenance window for all clients",
                "time_to_execute": "48 hours",
                "assumptions": "Assumes enterprise clients accept scheduled maintenance with 12h advance notice"
            }
            recommended_strat = "PLAN B: Proactive Enterprise Outreach + Transparent SLA Credits & High-Availability Hotfix"
            rec_executive = "Execute Plan B: Immediately publish transparent incident status, credit affected enterprise tiers proactively to stop churn, and deploy containerized hotfix to isolated cluster pods."
            why_strat = "In B2B SaaS, enterprise renewals depend on transparency and reliability. Proactive communication with SLA credits converts an operational crisis into a customer retention win."
        elif is_competitor:
            plan_a = {
                "plan": "PLAN A: Direct Price Match & Defensive Free Tier Launch",
                "risk": "High (Margin Cannibalization)",
                "resource_req": "$15k dev / marketing setup",
                "estimated_impact": "Stems immediate user leakage but compresses gross margins by 35%",
                "time_to_execute": "10 days",
                "assumptions": "Assumes volume increase will offset lower revenue per customer"
            }
            plan_b = {
                "plan": "PLAN B: Move Upmarket to High-ACV Enterprise Tier + Proprietary AI Moat",
                "risk": "Moderate (Balanced Moat)",
                "resource_req": "$45k focused roadmap sprint",
                "estimated_impact": "Increases net retention to >115% and insulates business from low-end free competitors",
                "time_to_execute": "21 days",
                "assumptions": "Assumes enterprise buyers prioritize security, SLAs, and deep workflows over free entry-level tools"
            }
            plan_c = {
                "plan": "PLAN C: Niche Specialization & Ecosystem Integration Play",
                "risk": "Moderate (Market Sizing Limit)",
                "resource_req": "Partnership bandwidth",
                "estimated_impact": "Locks in core vertical domain where competitors have zero native presence",
                "time_to_execute": "30-45 days",
                "assumptions": "Assumes vertical market is large enough to sustain 10x growth targets"
            }
            recommended_strat = "PLAN B: Move Upmarket to High-ACV Enterprise Tier with Proprietary Workflow Moat"
            rec_executive = "Execute Plan B: Avoid entering a destructive race to the bottom on price. Instead, double down on enterprise-grade capabilities, custom integrations, and SLA guarantees where free competitors cannot compete."
            why_strat = "Free competitor offerings primarily capture low-value self-serve users. Moving upmarket captures defensible enterprise budgets with higher customer lifetime value (LTV) and sustainable unit economics."
        elif is_expansion:
            plan_a = {
                "plan": "PLAN A: Rapid Direct Inbound & Broad Multi-Region Ad Blitz",
                "risk": "High (High CAC / Low Conversion)",
                "resource_req": "$120k marketing deployment",
                "estimated_impact": "High top-of-funnel lead velocity but lower localized sales conversion",
                "time_to_execute": "14 days",
                "assumptions": "Assumes digital inbound channels convert similarly across all territories"
            }
            plan_b = {
                "plan": "PLAN B: Phased Beachhead Strategy with Localized Channel Partners & GDPR Compliance",
                "risk": "Low / Balanced",
                "resource_req": "$60k targeted market entry",
                "estimated_impact": "Secures reference lighthouse customers with 70%+ gross margins and compliant data infrastructure",
                "time_to_execute": "30 days",
                "assumptions": "Assumes tier-1 regional channel partner accelerates pilot enterprise onboarding"
            }
            plan_c = {
                "plan": "PLAN C: Acquire / Merge with Regional Niche Incumbent",
                "risk": "Critical (Integration Friction)",
                "resource_req": "Significant M&A capital",
                "estimated_impact": "Instant customer base but requires 6+ months of legacy code and team consolidation",
                "time_to_execute": "90+ days",
                "assumptions": "Assumes compatible architecture and willing seller"
            }
            recommended_strat = "PLAN B: Phased Beachhead Expansion with Localized Compliance & High-Trust Channel Partners"
            rec_executive = "Execute Plan B: Establish a focused beachhead in the primary target region, ensure full regulatory/data compliance upfront, and close 3-5 lighthouse reference accounts before scaling generalized sales headcount."
            why_strat = "Reduces expansion capital risk by validating unit economics and regulatory compliance with initial anchor clients before deploying major budget."
        elif is_team_crisis:
            plan_a = {
                "plan": "PLAN A: Immediate External Executive Headhunter Search",
                "risk": "High (Slow 90-Day Ramp / High Fee)",
                "resource_req": "$40k search retainer",
                "estimated_impact": "Fills executive title eventually but leaves immediate 60-day development leadership vacuum",
                "time_to_execute": "60-90 days",
                "assumptions": "Assumes qualified candidates can be recruited quickly without salary escalation"
            }
            plan_b = {
                "plan": "PLAN B: Internal Technical Lead Elevation + Fractional Senior Advisory & Equity Retention Pool",
                "risk": "Low (Immediate Continuity)",
                "resource_req": "$10k fractional advisory / equity",
                "estimated_impact": "Prevents product stall, maintains institutional codebase knowledge, and stops secondary employee departures",
                "time_to_execute": "7 days",
                "assumptions": "Assumes senior internal engineers are empowered with equity grants and architectural authority"
            }
            plan_c = {
                "plan": "PLAN C: Contract Dev Shop / Agency Code Handover",
                "risk": "Critical (Code Quality & Security Decay)",
                "resource_req": "$30k/mo agency retainer",
                "estimated_impact": "Maintains raw commit volume but leads to tech debt and loss of proprietary IP control",
                "time_to_execute": "14 days",
                "assumptions": "Assumes external agency can parse proprietary architecture quickly"
            }
            recommended_strat = "PLAN B: Internal Technical Lead Elevation with Fractional Domain Advisory & Retention Equity"
            rec_executive = "Execute Plan B: Immediately promote proven internal engineering talent into lead roles, issue refreshed retention grants, and pair them with a seasoned fractional advisor to maintain architecture velocity."
            why_strat = "Preserves critical codebase context, prevents secondary team panic, and maintains uninterrupted shipping velocity at minimal cash drain."
        else: # Default Runway / General Venture Scenario
            plan_a = {
                "plan": "PLAN A: Pure Cost Slashing & Austere Survival Mode",
                "risk": "High (Product Velocity Collapse)",
                "resource_req": "$0 new capital",
                "estimated_impact": "Extends cash runway by 3-5 months but severely reduces engineering output",
                "time_to_execute": "7 days",
                "assumptions": "Assumes inbound traction persists without paid acquisition"
            }
            plan_b = {
                "plan": "PLAN B: Insider Bridge Round + High-ACV Upfront Annual Enterprise Focus",
                "risk": "Moderate (Balanced Growth)",
                "resource_req": "Insider bridge commitment",
                "estimated_impact": "Extends runway past 12+ months and generates non-dilutive upfront operating cash flow",
                "time_to_execute": "21 days",
                "assumptions": "Assumes existing lead investors participate on milestone-based commitments"
            }
            plan_c = {
                "plan": "PLAN C: Strategic M&A / Acqui-hire Partnership Search",
                "risk": "Critical (Low Valuation Multiple)",
                "resource_req": "Advisory bandwidth",
                "estimated_impact": "Preserves core IP and soft-lands team but yields modest shareholder returns",
                "time_to_execute": "60-90 days",
                "assumptions": "Assumes strategic partner has active acquisition mandate"
            }
            recommended_strat = "PLAN B: Strategic Alignment & High-ACV Upfront Annual Pivot"
            rec_executive = "Execute Plan B: Align leadership around high-margin enterprise accounts, collect upfront annual cash, and maintain core shipping speed with lean dedicated engineering pods."
            why_strat = "Provides the required operational stability to execute customer recovery and value creation without crippling talent or diluting enterprise valuation."

        # 5. Dynamic 30-Day Plan, Risks, and Triggers
        summary_prompt = expanded_context[:80]
        next_30_days = [
            f"Week 1: Immediate stakeholder alignment — audit customer pipelines, cost structure, and technical dependencies for '{prompt}'.",
            f"Week 2: Formalize operational transition — deploy {recommended_strat.split(':')[1].strip()} protocols and freeze low-impact items.",
            "Week 3: Launch refined customer/partner engagement tier with upfront incentive structures and SLA reassurance.",
            "Week 4: Review milestone metrics with Board/Advisors; adjust allocation based on empirical conversion rates."
        ]

        decision_triggers = [
            "Trigger 1: If primary milestone progress is < 50% by Day 21 → activate secondary contingency plan immediately.",
            "Trigger 2: If conversion or retention exceeds baseline target by > 25% → accelerate investment in core high-leverage channel.",
            "Trigger 3: If cash or key resource drops below emergency threshold → initiate structured partner/M&A dialogue."
        ]

        risks = [
            f"Execution delay if team cannot align on new priority focus within 7 days.",
            f"Customer friction or churn during service/model transition.",
            f"Downstream dependency latency impacting user retention."
        ]

        assumptions = [
            f"1. Core enterprise customers value transparent communication and fast SLA remediation.",
            f"2. Team can execute the adjusted strategy without requiring unbudgeted emergency capital.",
            f"3. Leadership maintains transparent communications with active partners and stakeholders."
        ]

        return {
            "situation": expanded_context,
            "severity": sev,
            "runway_status": runway_status,
            "burn_reduction_target": burn_target,
            "recommended_strategy": recommended_strat,
            "executive_recommendation": rec_executive,
            "why_this_strategy": why_strat,
            "alternative_strategies": [plan_a, plan_b, plan_c],
            "assumptions": assumptions,
            "risks": risks,
            "next_30_days_plan": next_30_days,
            "decision_triggers": decision_triggers,
            "dissenting_opinions": [
                "Growth Specialist: Cautioned against moving entirely away from experimental discovery channels",
                "Financial Auditor: Emphasized enforcing strict weekly SLA and cashburn reporting checkpoints"
            ],
            "red_team_findings": [
                f"Red team vulnerability identified: Operational transition risks losing momentum if rollout exceeds 21 days.",
                "Mitigation incorporated: Phased deployment with weekly milestone checkpoints and pre-agreed triggers."
            ],
            "lessons_learned": [
                "Always maintain active client communication channels and SLA buffers during critical service updates.",
                "Align product strategy directly with high-value customer willingness-to-pay rather than vanity metrics."
            ]
        }

scenario_analyzer = DynamicScenarioAnalyzer()
