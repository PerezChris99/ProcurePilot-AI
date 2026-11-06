"""Authenticated, read-only policy laboratory with no remote service calls."""
from fastapi import APIRouter, Depends

from app.models.user import User
from app.procurement.trust_lab import trust_lab_scenarios
from app.security.tokens import get_current_user

router = APIRouter(tags=["purchase verification"])


@router.get("/trust-lab/scenarios")
def run_policy_lab(_user: User = Depends(get_current_user)):
    """Execute deterministic scenario fixtures through real PO policy logic."""
    return trust_lab_scenarios()
