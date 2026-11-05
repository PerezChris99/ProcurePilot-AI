import uuid
from datetime import datetime,timezone
from decimal import Decimal
from sqlalchemy import DateTime,ForeignKey,Integer,JSON,Numeric,String,Text,Index
from sqlalchemy.orm import Mapped,mapped_column
from app.core.database import Base

class ProcurementRequest(Base):
    __tablename__='procurement_requests'
    __table_args__=(
        Index('ix_procurement_requests_user_created','user_id','created_at'),
        Index('ix_procurement_requests_user_status_created','user_id','status','created_at'),
    )
    id: Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    user_id: Mapped[str]=mapped_column(ForeignKey('users.id',ondelete='CASCADE'),index=True,nullable=False)
    request_text: Mapped[str]=mapped_column(Text,nullable=False)
    quantity: Mapped[int]=mapped_column(Integer,default=1,nullable=False)
    budget: Mapped[Decimal | None]=mapped_column(Numeric(14,2),nullable=True)
    currency: Mapped[str]=mapped_column(String(3),default='USD',nullable=False)
    status: Mapped[str]=mapped_column(String(32),default='draft',nullable=False,index=True)
    analysis_json: Mapped[dict | None]=mapped_column(JSON,nullable=True)
    policy_json: Mapped[dict]=mapped_column(JSON,default=dict,nullable=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),onupdate=lambda:datetime.now(timezone.utc),nullable=False)
