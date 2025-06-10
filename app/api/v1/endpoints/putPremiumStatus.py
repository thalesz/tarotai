from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta  # Para adicionar 1 mês corretamente

from app.core.deps import get_session
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.status import StatusSchemaBase
from app.schemas.event import EventSchemaBase
from app.schemas.mission import MissionSchemaBase
from app.schemas.user_type import UserTypeSchema, UserTypeSchemaBase
from app.schemas.subscription import SubscriptionSchemaBase
from app.schemas.notification import NotificationSchema
from app.services.websocket import ws_manager  # Certifique-se de que o caminho está correto
from app.services.subscription import Subscription  # Certifique-se de que o caminho está correto
from app.schemas.planet import PlanetSchemaBase  # Certifique-se de que o caminho está correto
from app.services.descricao_astrologica import DescricaoAstrologicaService  # Certifique-se de que o caminho está correto
from app.schemas.personal_sign import PersonalSignSchema  # Certifique-se de que o caminho está correto
from app.schemas.zodiac import ZodiacSchemaBase  # Certifique-se de que o caminho está correto

router = APIRouter()

@router.put(
    "/premium/{user_id}",
    summary="Atualizar status do usuário para premium",
    description="Atualiza o status de um usuário específico para premium, com base no ID fornecido na URL.",
    response_description="Status do usuário atualizado com sucesso.",
    responses={
        200: {
            "description": "Status do usuário atualizado com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "detail": "Status do usuário atualizado para premium com sucesso."
                            }
                        ]
                    }
                }
            },
        },
        400: {
            "description": "Usuário inválido ou não encontrado.",
            "content": {
                "application/json": {
                    "example": {"detail": "User does not exist."}
                }
            },
        },
        401: {
            "description": "Token de autenticação ausente ou inválido.",
            "content": {
                "application/json": {
                    "example": {"detail": "token information is missing"}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor.",
            "content": {
                "application/json": {
                    "example": {"detail": "Ocorreu um erro ao buscar os eventos."}
                }
            },
        },
    },
)
async def update_user_status(
    user_id: int,
    # request: Request,
    db: AsyncSession = Depends(get_session)
):
    try:
        # token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        # if token_info is None:
        #     raise HTTPException(status_code=401, detail="token information is missing")

        # Aqui você pode colocar lógica extra de permissão se quiser restringir ao ADM
        # Por exemplo: if token_info.role != 'ADMIN': raise HTTPException(...)

        if not await UserSchemaBase.user_exists(db, user_id):
            raise HTTPException(status_code=400, detail="User does not exist.")
        
        
        # tem que ver se o user esta ativo, se não estiver ativo não pode ser atualizado para premium
        user_status_id = await UserSchemaBase.get_status_by_id(db=db, id=user_id)
        active_status_id = await StatusSchemaBase.get_id_by_name(db=db, name="active")

        print(f"User status ID: {user_status_id}, Active status ID: {active_status_id}")
        if user_status_id != active_status_id:
            raise HTTPException(status_code=400, detail="User is not active.")

        current_user_type_id = await UserSchemaBase.get_user_type_by_id(db=db, id=user_id)
        premium_user_type_id = await UserTypeSchema.get_id_by_name(session=db, name="PREMIUM")
        standard_user_type_id = await UserTypeSchema.get_id_by_name(session=db, name="STANDARD")
        admin_user_type_id = await UserTypeSchema.get_id_by_name(session=db, name="ADM")
        
        print(f"Current user type ID: {current_user_type_id}, Premium user type ID: {premium_user_type_id}, Standard user type ID: {standard_user_type_id}")
        if current_user_type_id == premium_user_type_id:
            raise HTTPException(status_code=400, detail="User is already premium.")
        
        if current_user_type_id == admin_user_type_id:
            raise HTTPException(status_code=400, detail="User is an admin and cannot be updated to premium.")
        
        if current_user_type_id == standard_user_type_id:
            print("User is standard, updating to premium...")
            await UserSchemaBase.update_user_type(db=db, user_id=user_id, new_user_type=premium_user_type_id)

            subscription = await SubscriptionSchemaBase.create_subscription(
                db,
                user_id=user_id,
                status=active_status_id,
                created_at=datetime.now(timezone.utc),
                expired_at=datetime.now(timezone.utc) + relativedelta(months=1)  # adiciona 1 mês corretamente
            )

            if not subscription:
                raise HTTPException(status_code=500, detail="Failed to create subscription.")
            
            
            # atualizar a descricao dos planetas
            
            # tem que pegar os planetas que o usuario tem acesso
            all_planets = await PlanetSchemaBase.get_all_planet_ids_and_names(db)
            allowed_planets = await UserTypeSchemaBase.get_planets_by_user_type_id(db, premium_user_type_id)
            
            max_tokens = int(await UserTypeSchema.get_token_amount_by_id(db, premium_user_type_id))
            #pegar o birth info do usuario
            user_birth_info = await UserSchemaBase.get_birth_info_by_id(db, user_id)
            print(f"User birth info: {user_birth_info}")
            for planet in all_planets:
                
                print(f"Processing planet: {planet['name']} (ID: {planet['id']})")
                planet_id = planet["id"]
                print(f"Planet ID: {planet_id}, Name: {planet['name']}")
                planet_name = planet["name"]
                acesso_premium = planet_id in allowed_planets
                descricao_service = DescricaoAstrologicaService()
                signo, grau = await PersonalSignSchema.get_sign_and_degree_by_user_and_planet(
                    db, user_id, planet_id
                )
                
                # pega o nome do signo
                nome_signo = await ZodiacSchemaBase.get_zodiac_name_by_id(db, signo)
                
                await descricao_service.gerar_e_salvar_descricao(
                    db=db,
                    user_id=user_id,
                    birth_date=user_birth_info['birth_date'],
                    birth_time=user_birth_info['birth_time'],
                    birth_place=user_birth_info['birth_place'],
                    planet_id=planet_id,
                    planet_name=planet_name,
                    acesso_premium=acesso_premium,
                    max_tokens=max_tokens,
                    signo=nome_signo,
                    grau=grau
                )


            await Subscription.create_daily_gift_for_user(user_id=user_id, db=db)
            message = f"Parabéns! Você agora é um usuário premium. Aproveite todos os benefícios exclusivos!"
            notification = await NotificationSchema.create_notification(db, user_id, message)

            # Envia via WebSocket
            await ws_manager.send_notification(str(user_id), message, notification.id)
            
            
            
            

            return {
                "data": [
                    {
                        "detail": "Status do usuário atualizado para premium com sucesso."
                    }
                ]
            }
            

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro ao atualizar usuário: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao atualizar o status do usuário.")
