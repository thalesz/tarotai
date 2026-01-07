from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.dependencies.verifyjwt import verify_jwt
from app.schemas.user import UserSchemaBase
from app.schemas.wallet import WalletSchemaBase
from app.schemas.status import StatusSchema  # Import StatusSchema
from app.schemas.notification import NotificationSchema  # Import NotificationSchema
from app.schemas.confirmation import ConfirmationResponse, ErrorResponse
from app.core.configs import settings
from app.services.email import EmailConfirmationSchema
from app.services.token import TokenConfirmationSchema
from app.services.subscription import Subscription

# Import DailyPathService for creating daily path
from app.services.daily_path import DailyPathService

# Import ConfirmMissionService for mission confirmation
from app.services.confirmMissionService import ConfirmMissionService
from app.schemas.mission_type import MissionTypeSchemaBase  # Import MissionTypeSchemaBase

# Import ws_manager from its module (update the import path as needed)
from app.services.websocket import ws_manager
from app.services.subscription import Subscription

router = APIRouter()


@router.get(
    "/receive/{token}",
    response_class=JSONResponse,
    response_model=ConfirmationResponse,
    summary="Recebe o token de confirmação por e-mail",
    description="Recebe um token de confirmação enviado anteriormente para o e-mail do usuário.",
    responses={
        200: {"description": "Conta confirmada com sucesso."},
        400: {"model": ErrorResponse, "description": "Requisição inválida ou usuário já confirmado."},
        404: {"model": ErrorResponse, "description": "Usuário ou recurso não encontrado."},
        500: {"description": "Erro interno no servidor."},
    },
)
async def receive_confirmation_token_by_email(
    token: str, db: AsyncSession = Depends(get_session)
):
    try:
        token_info: TokenConfirmationSchema = TokenConfirmationSchema.decode_token(
            token=token,
            secret_key=settings.CONFIRMATION_SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        print(f"Token decodificado: {token_info}")
    except HTTPException as e:
        return JSONResponse(content={"message": str(e.detail)}, status_code=e.status_code)

    try:
        
        user_id = (
            token_info.get("id") if isinstance(token_info, dict) else token_info.id
        )
        user_exists = await UserSchemaBase.user_exists(db=db, id=user_id)
        # se n existir lance exceção
        if not user_exists:
            return JSONResponse(content={"message": "Usuário não encontrado."}, status_code=404)

        status_atual = await UserSchemaBase.get_status_by_id(id=user_id, db=db)
        pending_confirmation_status = await StatusSchema.get_id_by_name(
            db=db, name="pending_confirmation"
        )
        if status_atual != pending_confirmation_status:
            return JSONResponse(content={"message": "Usuário já confirmado."}, status_code=400)
        confirmation_status = await UserSchemaBase.confirm_user_using_id(
            id=user_id, db=db
        )
        wallet_confirmation_status = (
            await WalletSchemaBase.confirm_wallet_status_using_id(
                user_id=user_id, session=db
            )
        )

        if not confirmation_status or not wallet_confirmation_status:
            return JSONResponse(content={"message": "Usuário ou carteira não encontrada."}, status_code=404)
        user_email = await UserSchemaBase.get_user_email_by_id(db=db, user_id=user_id)
        try:
            await EmailConfirmationSchema.send_active_email(email=user_email)
            print(f"Email de ativação enviado para {user_email}")
        except Exception as e:
            print(f"Erro ao enviar email de ativação para {user_email}: {e}")
        
        # message = "Conta confirmada com sucesso! Agora você pode acessar todos os recursos da plataforma."

        # cria o daily path para o usuário
        daily_path_service = DailyPathService()
        try:
            await daily_path_service.create_daily_path_for_user(db=db, user_id=user_id)
            print(f"Daily path criado para usuário {user_id}")
        except Exception as e:
            print(f"Erro ao criar daily path para usuário {user_id}: {e}")

        subscription_service = Subscription()
        try:
            await subscription_service.create_daily_gift_for_user(db=db, user_id=user_id)
            print(f"Presentes diários criados para usuário {user_id}")
        except Exception as e:
            print(f"Erro ao criar presentes diários para usuário {user_id}: {e}")

        # cumpre a missão
        confirm_service = ConfirmMissionService()
        mission_type_id = await MissionTypeSchemaBase.get_id_by_name(db, "Confirmar conta de usuário")
        try:
            mission_result = await confirm_service.confirm_mission(db, mission_type_id, user_id)
            if mission_result:
                print(f"Missão de confirmação cumprida para usuário {user_id}")
            else:
                print(f"Missão de confirmação NÃO foi cumprida para usuário {user_id}")
        except Exception as e:
            print(f"Erro ao confirmar missão para usuário {user_id}: {e}")
        
        
        # notification = await NotificationSchema.create_notification(db, user_id, message)
        # # Envia via WebSocket
        # await ws_manager.send_notification(str(user_id), message, notification.id)

        return JSONResponse(content={"message": "Conta confirmada com sucesso!", "email": user_email}, status_code=200)
    except AttributeError as e:
        return JSONResponse(content={"message": "Erro interno", "detail": str(e)}, status_code=400)
