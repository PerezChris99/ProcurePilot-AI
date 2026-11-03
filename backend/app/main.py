from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.procurement_requests import router as procurement_router
from app.core.config import get_settings

settings=get_settings()
app=FastAPI(title=settings.app_name,version='0.1.0',description='AI-assisted procurement workflow API.',docs_url='/docs' if settings.app_env!='production' else None,redoc_url='/redoc' if settings.app_env!='production' else None)
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_url],allow_credentials=True,allow_methods=['GET','POST','PUT','PATCH','DELETE','OPTIONS'],allow_headers=['Authorization','Content-Type','Idempotency-Key'])
app.include_router(health_router,prefix=settings.api_v1_prefix)
app.include_router(auth_router,prefix=settings.api_v1_prefix)
app.include_router(procurement_router,prefix=settings.api_v1_prefix)

@app.get('/',include_in_schema=False)
def root():
    return {'name':settings.app_name,'status':'running'}
