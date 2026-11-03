from fastapi import APIRouter, Depends
from app.api.deps import current_admin
router=APIRouter(prefix="/admin",tags=["admin"])
@router.get("/health")
async def health(_: object=Depends(current_admin)): return {"ok":True}
