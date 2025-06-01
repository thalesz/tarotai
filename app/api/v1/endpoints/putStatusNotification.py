from fastapi import APIRouter, Depends, Body, HTTPException, Request, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from app.models.notification import Notification
from datetime import datetime
from app.schemas.notification import NotificationSchema
from app.schemas.status import StatusSchema
from app.services.websocket import ws_manager
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase

router = APIRouter(

)

@router.put(
    "/confirmation/{notification_id}",
    summary="Confirma notificação como lida",
    description="Atualiza o status de uma notificação para 'completed' se ela estiver pendente e pertencer ao usuário autenticado.",
    responses={
        200: {
            "description": "Status alterado com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Status alterado para 'completed' na notificação de ID 5"
                    }
                }
            }
        },
        400: {
            "description": "Notificação inválida, já confirmada ou não pertence ao usuário.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Notificação inexistente ou não pertence ao usuário."
                    }
                }
            }
        },
        401: {
            "description": "Token de autenticação ausente ou inválido.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Token de autenticação ausente."
                    }
                }
            }
        },
        500: {
            "description": "Erro interno do servidor.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Erro interno: <mensagem de erro>"
                    }
                }
            }
        }
    }
)
async def confirm_status_reading(
    request: Request,
    notification_id: int = Path(
        ...,
        description="ID da notificação a ser confirmada.",
        example=5
    ),
    db: AsyncSession = Depends(get_session)
) -> dict:
    """
    Marca a notificação como 'completed' se ela estiver em status de 'pending_confirmation' e pertencer ao usuário autenticado.

    - **notification_id**: ID da notificação a ser confirmada.
    - **Retorna**: Mensagem de sucesso ou erro.
    """
    try:
        # 1. Recuperar informações do token
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(status_code=401, detail="Token de autenticação ausente.")

        try:
            user_id = token_info.id
        except AttributeError:
            raise HTTPException(status_code=400, detail="ID do usuário não encontrado no token.")

        # 2. Verificar se o usuário existe
        userexists = await UserSchemaBase.user_exists(db, user_id)
        if not userexists:
            raise HTTPException(status_code=400, detail="Usuário não encontrado.")

        # 3. Verificar se a notificação pertence ao usuário
        notification_exists = await NotificationSchema.notification_exists(db, notification_id, user_id)
        if not notification_exists:
            raise HTTPException(status_code=400, detail="Notificação inexistente ou não pertence ao usuário.")

        # 4. Validar status atual da notificação
        pending_status = await StatusSchema.get_id_by_name(db=db, name="pending_confirmation")
        status_notification = await NotificationSchema.get_status_by_id(db, notification_id)
        
        if status_notification != pending_status:
            raise HTTPException(status_code=400, detail="Notificação já confirmada ou em status inválido.")

        # 5. Atualizar para 'completed'
        status_confirmed = await StatusSchema.get_id_by_name(db=db, name="completed")
        await NotificationSchema.modify_status_by_id(db, notification_id, status_confirmed)
        await NotificationSchema.modify_read_at_by_id(db, notification_id)
        
        return {
            "message": f"Notificação com o id {notification_id} confirmada como lida.",
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
