from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.domain_packs.registry import domain_pack_registry

router = APIRouter(prefix="/domain-packs", tags=["Domain Packs"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_domain_packs():
    """Returns all registered adaptive domain packs."""
    return domain_pack_registry.list_packs()

@router.get("/{domain_id}", response_model=Dict[str, Any])
async def get_domain_pack(domain_id: str):
    """Returns detailed domain pack configuration, agents, risk framework, and scenarios."""
    pack = domain_pack_registry.get_pack(domain_id.upper())
    if not pack or pack.domain_id != domain_id.upper():
        raise HTTPException(status_code=404, detail=f"Domain pack '{domain_id}' not found.")
    
    return {
        "domain_id": pack.domain_id,
        "display_name": pack.display_name,
        "description": pack.description,
        "icon": pack.icon,
        "category": pack.category,
        "agent_profiles": pack.get_agent_profiles(),
        "risk_framework": [r.model_dump() for r in pack.get_risk_framework()],
        "sample_scenarios": pack.get_sample_scenarios()
    }

@router.get("/{domain_id}/scenarios", response_model=List[Dict[str, Any]])
async def get_domain_scenarios(domain_id: str):
    """Returns sample demo scenarios for domain."""
    pack = domain_pack_registry.get_pack(domain_id.upper())
    if not pack:
        raise HTTPException(status_code=404, detail=f"Domain pack '{domain_id}' not found.")
    return pack.get_sample_scenarios()
