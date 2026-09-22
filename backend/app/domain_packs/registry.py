from typing import Dict, List, Optional, Any
from app.domain_packs.base import BaseDomainPack
from app.domain_packs.software_incident import SoftwareIncidentPack
from app.domain_packs.enterprise_crisis import EnterpriseCrisisPack
from app.domain_packs.startup_strategy import StartupStrategyPack
from app.domain_packs.supply_chain import SupplyChainPack
from app.domain_packs.university_operations import UniversityOperationsPack

class DomainPackRegistry:
    def __init__(self):
        self._packs: Dict[str, BaseDomainPack] = {}
        self._register_default_packs()

    def _register_default_packs(self):
        packs = [
            SoftwareIncidentPack(),
            EnterpriseCrisisPack(),
            StartupStrategyPack(),
            SupplyChainPack(),
            UniversityOperationsPack()
        ]
        for pack in packs:
            self._packs[pack.domain_id] = pack

    def get_pack(self, domain_id: str) -> Optional[BaseDomainPack]:
        return self._packs.get(domain_id) or self._packs.get("SOFTWARE_INCIDENT")

    def list_packs(self) -> List[Dict[str, Any]]:
        result = []
        for pack in self._packs.values():
            result.append({
                "domain_id": pack.domain_id,
                "display_name": pack.display_name,
                "description": pack.description,
                "icon": pack.icon,
                "category": pack.category,
                "default_capabilities": pack.get_required_capabilities(""),
                "sample_scenarios_count": len(pack.get_sample_scenarios())
            })
        return result

    def get_all_sample_scenarios(self) -> List[Dict[str, Any]]:
        all_scenarios = []
        for pack in self._packs.values():
            all_scenarios.extend(pack.get_sample_scenarios())
        return all_scenarios

domain_pack_registry = DomainPackRegistry()
