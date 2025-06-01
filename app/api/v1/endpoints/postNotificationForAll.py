from fastapi import APIRouter, Depends, Body, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from app.schemas.notification import NotificationSchema
from app.schemas.user import UserSchemaBase
from app.schemas.status import StatusSchemaBase
from app.services.websocket import ws_manager
from pydantic import BaseModel, Field

router = APIRouter()

# ✅ Pydantic Schema para o corpo da requisição
class NotificationRequest(BaseModel):
    message: str = Field(..., description="Mensagem da notificação", example="Sua mensagem de notificação")

@router.post(
    "/post",
    status_code=status.HTTP_200_OK,
    summary="Enviar notificação para usuários ativos ou pendentes",
    description="""
    Envia uma notificação para todos os usuários com status "active" ou "pending_confirmation".  
    Cria uma notificação no banco de dados e envia via WebSocket.
    """,
    responses={
        200: {
            "description": "Notificação enviada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Notificação enviada para todos os usuários."
                    }
                }
            }
        },
        400: {"description": "Entrada inválida ou nenhum usuário encontrado"},
        500: {"description": "Erro interno do servidor"}
    },
)
async def notify_user(
    payload: NotificationRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Cria e envia uma notificação para todos os usuários ativos ou pendentes.

    - **message**: Conteúdo da notificação (via body)
    """
    try:
        id_active = await StatusSchemaBase.get_id_by_name(db, "active")
        id_pending = await StatusSchemaBase.get_id_by_name(db, "pending_confirmation")
        all_users = await UserSchemaBase.get_all_id_by_status(db, [id_active, id_pending])

        if not all_users:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Nenhum usuário ativo ou pendente encontrado."}
            )

        for user in all_users:
            notification = await NotificationSchema.create_notification(db, user, payload.message)
            await ws_manager.send_notification(str(user), payload.message, notification.id)

        return {"detail": "Notificação enviada para todos os usuários."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")
