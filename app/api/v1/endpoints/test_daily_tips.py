from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from app.services.dailyTips import DailyTipsService
import traceback

router = APIRouter()


@router.post(
    "/daily-tips/test/user/{user_id}",
    summary="Criar dicas diárias para um usuário (rota de teste)",
    description="Rota de desenvolvimento para disparar a geração de dicas diárias e retornar erros completos para depuração.",
)
async def test_create_daily_tips(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_session),
):
    try:
        service = DailyTipsService()
        # executa a criação (internamente já faz logs). Capturamos exceções para retornar stack trace.
        await service.create_daily_tips_for_user(db=db, user_id=user_id)
        return JSONResponse(content={"status": "ok", "detail": f"Daily tips triggered for user {user_id}"}, status_code=200)
    except Exception as e:
        tb = traceback.format_exc()
        # Retorna a mensagem e o stacktrace para depuração local
        return JSONResponse(
            content={"status": "error", "error": str(e), "traceback": tb},
            status_code=500,
        )


@router.post(
    "/daily-tips/test/all",
    summary="Criar dicas diárias para todos os usuários (rota de teste)",
    description="Rota de desenvolvimento para disparar a geração de dicas diárias para todos os usuários ativos e retornar um resumo com erros.",
)
async def test_create_daily_tips_for_all(
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    try:
        service = DailyTipsService()
        result = await service.create_daily_tips_for_all_users()
        return JSONResponse(content={"status": "ok", "result": result}, status_code=200)
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(
            content={"status": "error", "error": str(e), "traceback": tb},
            status_code=500,
        )
