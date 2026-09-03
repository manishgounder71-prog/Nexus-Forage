from typing import Dict, List, Any, Optional
from app.domain_packs.registry import domain_pack_registry

class SimulationEngine:
    """
    Monte-Carlo Strategy Simulation Engine:
    Evaluates alternative strategy trajectories based on domain pack heuristics,
    Qdrant vector memory historical outcomes, and agent stochastic modeling.
    """
    def simulate_strategies(
        self,
        mission_type: str = "critical_system_failure",
        domain_id: Optional[str] = None,
        mission_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        context = mission_context or {"mission_type": mission_type}
        
        # If domain_id provided, query domain pack
        if domain_id:
            pack = domain_pack_registry.get_pack(domain_id)
            if pack:
                return pack.get_simulation_strategies(context)

        # Fallback domain detection by mission_type keyword
        if "power_grid" in mission_type or "cyber_attack" in mission_type:
            pack = domain_pack_registry.get_pack("ENTERPRISE_CRISIS")
            return pack.get_simulation_strategies({"prompt": "power grid cyber-attack"})
        elif "supply" in mission_type or "logistics" in mission_type:
            pack = domain_pack_registry.get_pack("SUPPLY_CHAIN")
            return pack.get_simulation_strategies(context)
        elif "startup" in mission_type or "runway" in mission_type:
            pack = domain_pack_registry.get_pack("STARTUP_STRATEGY")
            return pack.get_simulation_strategies(context)
        elif "exam" in mission_type or "university" in mission_type:
            pack = domain_pack_registry.get_pack("UNIVERSITY_OPERATIONS")
            return pack.get_simulation_strategies(context)

        # Default to software incident pack
        pack = domain_pack_registry.get_pack("SOFTWARE_INCIDENT")
        return pack.get_simulation_strategies(context)

simulation_engine = SimulationEngine()
