from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/test-jwt")
async def test_jwt():
    try:
        return {"message": "Token de acesso válido!"} 
    except Exception as e:
        return {"error": str(e)}