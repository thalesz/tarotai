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

@router.get(
    "/all",
    summary="Lista todas as notificações do usuário autenticado",
    description="Retorna todas as notificações pertencentes ao usuário autenticado, incluindo status, data de criação, data de leitura e mensagem.",
    responses={
        200: {
            "description": "Lista de notificações retornada com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 5,
                                "status": "Lida",
                                "created_at": "2024-06-13T12:34:56.789000",
                                "read_at": "2024-06-13T13:00:00.000000",
                                "message": "Sua leitura está pronta."
                            },
                            {
                                "id": 6,
                                "status": "Pendente",
                                "created_at": "2024-06-13T14:00:00.000000",
                                "read_at": None,
                                "message": "Você tem uma nova notificação."
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Nenhuma notificação encontrada para o usuário ou usuário não encontrado.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Nenhuma notificação encontrada para o usuário."
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
async def get_all_notification_by_user(
    request: Request,
    db: AsyncSession = Depends(get_session)
) -> dict:
    """
    Retorna todas as notificações do usuário autenticado.

    - **Retorna**: Lista de notificações com status, datas e mensagem.
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
        
        # retorna todas as notificações do usuário
        notifications = await NotificationSchema.get_all_notifications_by_user_id(db, user_id)
        if not notifications:
            raise HTTPException(status_code=400, detail="Nenhuma notificação encontrada para o usuário.")
        
        
        
        #retorna em formato rest 
        notifications_list = []
        for notification in notifications:
            status_name = await StatusSchema.get_name_by_id(db, notification.status)
            if status_name == "pending_confirmation":
                status_name = "Pendente"
            elif status_name == "completed":
                status_name = "Lida"
            
            notifications_list.append({
                "id": notification.id,
                "status": status_name,
                "created_at": notification.created_at.isoformat(),
                "read_at": notification.read_at.isoformat() if notification.read_at else None,
                "message": notification.message
            })
        return {
            "data": notifications_list,
        }


    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
