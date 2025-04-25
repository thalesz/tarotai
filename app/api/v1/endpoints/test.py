from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.core.deps import get_session

router = APIRouter()


@router.get("/test-db")
async def test_db(session: AsyncSession = Depends(get_session)):
    try:
        result = await session.execute(text("SELECT 1"))
        return {
            "message": "Conexão com o banco bem-sucedida!",
            "result": result.scalar(),
        }
    except Exception as e:
        return {"error": str(e)}
