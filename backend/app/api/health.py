from fastapi import APIRouter
router=APIRouter(tags=['health'])

@router.get('/health',summary='Application health check')
def health_check():
    return {'status':'ok','service':'procurepilot-api'}
