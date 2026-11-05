"""Offline fixture never impersonates Channel3, Gemini or payment providers."""
from decimal import Decimal
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import ProcurementRequest,User
from scripts.seed_judge_preview import seed_preview,SCENARIO
from app.procurement.policy import snapshot_recent


def test_seed_is_idempotent_and_never_creates_payable_provider_data():
    engine=create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user=User(id='sample-user-1',email='preview@example.com',
                  full_name='Preview',hashed_password='not-used-in-this-test')
        db.add(user)
        db.commit()
        first=seed_preview(db,user)
        second=seed_preview(db,user)
        assert first==second
        request=db.scalar(select(ProcurementRequest).where(ProcurementRequest.id==first))
        assert request.request_text==SCENARIO
        assert request.status=='sample_preview'
        assert request.analysis_json['source']=='offline_demo'
        assert request.analysis_json['ai_source']=='offline_example'
        assert snapshot_recent(request.analysis_json) is False
        assert len(request.analysis_json['results'])==3
        assert all(not item['policy']['eligible_offer_urls']
                   for item in request.analysis_json['results'])
        assert request.budget==Decimal('350.00')
    engine.dispose()
