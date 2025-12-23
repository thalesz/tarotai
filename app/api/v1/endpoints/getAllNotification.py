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
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter(

)


class NotificationItemSchema(BaseModel):
    id: int = Field(..., example=5)
    status: str = Field(..., example="Lida")
    created_at: datetime = Field(..., example="2024-06-13T12:34:56.789000")
    read_at: Optional[datetime] = Field(None, example="2024-06-13T13:00:00.000000")
    message: str = Field(..., example="Sua leitura está pronta.")


class PaginationSchema(BaseModel):
    current_page: int = Field(..., example=1)
    total_pages: int = Field(..., example=3)
    total_items: int = Field(..., example=13)
    items_per_page: int = Field(..., example=5)
    has_next: bool = Field(..., example=True)
    has_previous: bool = Field(..., example=False)


class NotificationsPaginatedResponse(BaseModel):
    data: List[NotificationItemSchema]
    pagination: PaginationSchema

@router.get(
    "/all/{count}",
    response_model=NotificationsPaginatedResponse,
    tags=["notifications"],
    summary="Listar notificações paginadas do usuário (5 por página)",
    description=(
        "Retorna as notificações do usuário autenticado paginadas em páginas de 5 itens. "
        "Cada item inclui status legível, data de criação, data de leitura (se houver) e mensagem."
    ),
    responses={
        200: {"description": "Lista de notificações retornada com sucesso."},
        400: {"description": "Usuário não encontrado ou requisição inválida."},
        401: {"description": "Token de autenticação ausente ou inválido."},
        404: {"description": "Página de notificações inexistente ou sem notificações."},
        500: {"description": "Erro interno do servidor."}
    }
)
async def get_all_notification_by_user(
    request: Request,
    count: int,
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

        # Pegar todas as notificações (schema atual expõe uma função que retorna todas)
        notifications = await NotificationSchema.get_all_notifications_by_user_id(db, user_id)

        # Ordenar da mais recente para a mais antiga (antes de paginar)
        if notifications:
            try:
                notifications.sort(key=lambda n: n.created_at, reverse=True)
            except Exception:
                # se os itens não tiverem atributo created_at ou não forem comparáveis,
                # ignore a ordenação para evitar quebrar a rota
                pass

        total_items = len(notifications) if notifications else 0

        if total_items == 0:
            raise HTTPException(status_code=404, detail="Nenhuma notificação encontrada para o usuário.")

        # Paginação: 5 itens por página
        items_per_page = 5
        total_pages = (total_items + items_per_page - 1) // items_per_page

        if count < 1 or count > total_pages:
            raise HTTPException(status_code=404, detail="Página de notificações inexistente.")

        start = (count - 1) * items_per_page
        end = start + items_per_page
        page_notifications = notifications[start:end]

        notifications_list = []
        for notification in page_notifications:
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
            "pagination": {
                "current_page": count,
                "total_pages": total_pages,
                "total_items": total_items,
                "items_per_page": items_per_page,
                "has_next": count < total_pages,
                "has_previous": count > 1
            }
        }


    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
