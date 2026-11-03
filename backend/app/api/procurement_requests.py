from fastapi import APIRouter,Depends,HTTPException,Query,status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.agents import runtime
from app.agents.runtime import AgentConfigurationError,AgentExecutionError
from app.core.database import get_db
from app.integrations.channel3.client import Channel3Client,Channel3ConfigurationError,Channel3Unavailable
from app.integrations.channel3.schemas import Channel3Product
from app.models.procurement_request import ProcurementRequest
from app.models.user import User
from app.procurement.schemas import ProcurementRequirements
from app.procurement.scoring import rank_products
from app.schemas.procurement_request import ProcurementRequestCreate,ProcurementRequestResponse
from app.security.tokens import get_current_user

router=APIRouter(prefix='/procurement-requests',tags=['procurement'])

def _owned_request(request_id: str,user: User,db: Session) -> ProcurementRequest:
    request=db.scalar(select(ProcurementRequest).where(ProcurementRequest.id==request_id,ProcurementRequest.user_id==user.id))
    if request is None: raise HTTPException(status_code=404,detail='Procurement request not found')
    return request

@router.post('',response_model=ProcurementRequestResponse,status_code=status.HTTP_201_CREATED)
def create_request(payload: ProcurementRequestCreate,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    request=ProcurementRequest(user_id=user.id,request_text=payload.request_text,quantity=payload.quantity,budget=payload.budget,currency=payload.currency)
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

@router.get('',response_model=list[ProcurementRequestResponse])
def list_requests(limit: int=Query(default=50,ge=1,le=100),db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    return db.scalars(select(ProcurementRequest).where(ProcurementRequest.user_id==user.id).order_by(ProcurementRequest.created_at.desc()).limit(limit)).all()

@router.get('/{request_id}',response_model=ProcurementRequestResponse)
def get_request(request_id: str,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    return _owned_request(request_id,user,db)

@router.post('/{request_id}/discover')
async def discover_products(request_id: str,next_page: bool=False,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    request=_owned_request(request_id,user,db)
    current=request.analysis_json or {}
    page_token=current.get('next_page_token') if next_page else None
    if next_page and not page_token: raise HTTPException(status_code=409,detail='There is no additional catalogue page to load')
    requirements=ProcurementRequirements(query=request.request_text,quantity=request.quantity,budget=request.budget,currency=request.currency)
    try:
        response=await Channel3Client().search_products(requirements.query,limit=20,user_id=user.id,page_token=page_token)
    except Channel3ConfigurationError as exc:
        raise HTTPException(status_code=503,detail='Product discovery is not configured yet') from exc
    except Channel3Unavailable as exc:
        raise HTTPException(status_code=502,detail='The product catalogue is temporarily unavailable') from exc
    page_products=[item['product'] for item in current.get('results',[])] if next_page else []
    merged={item['id']:item for item in page_products}
    merged.update({product.id:product.model_dump(mode='json') for product in response.products})
    all_products=[Channel3Product.model_validate(item) for item in merged.values()]
    scores=rank_products(all_products,requirements)
    products={product.id:product for product in all_products}
    results=[{'ranking':score.model_dump(mode='json'),'product':products[score.product_id].model_dump(mode='json')} for score in scores]
    request.analysis_json={'source':'Channel3','results':results,'next_page_available':response.next_page_token is not None,'next_page_token':response.next_page_token}
    request.status='products_discovered'
    db.add(request)
    db.commit()
    db.refresh(request)
    return request.analysis_json

@router.post('/{request_id}/analyze')
async def analyze_request(request_id: str,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    request=_owned_request(request_id,user,db)
    prompt=(f'Analyze this business procurement request and use your Channel3 discovery tool to find and rank real catalogue options. '
            f'Request: {request.request_text}\nQuantity: {request.quantity}\nBudget: {request.budget if request.budget is not None else "Not specified"} {request.currency}. '
            'Explain the strongest options, show evidence for prices and availability, identify missing or unverified requirements, '
            'and clearly state that delivery suitability is unknown unless verified. Do not create a purchase order or initiate payment.')
    try:
        explanation=await runtime.run_procurement_agent(user.id,prompt)
    except AgentConfigurationError as exc:
        raise HTTPException(status_code=503,detail='The AI procurement agent is not configured yet') from exc
    except AgentExecutionError as exc:
        raise HTTPException(status_code=502,detail=str(exc)) from exc
    request.analysis_json={**(request.analysis_json or {}),'ai_explanation':explanation}
    if request.status=='draft': request.status='analyzed'
    db.add(request)
    db.commit()
    return {'request_id':request.id,'explanation':explanation,'status':request.status}
