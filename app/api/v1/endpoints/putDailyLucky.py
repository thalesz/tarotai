from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.deps import get_session
from app.schemas.draw import DrawCreate
from app.schemas.user import UserSchemaBase
from app.schemas.spread_type import SpreadTypeSchema
from app.services.token import TokenInfoSchema
from app.schemas.daily_lucky import DailyLuckySchemaBase
from app.schemas.status import StatusSchemaBase, StatusSchema
from app.schemas.user_type import UserTypeSchema
from app.services.openai import OpenAIService
from app.services.extract import JsonExtractor  # Import JsonExtractor

from app.services.confirmMissionService import ConfirmMissionService
from app.basic.mission_type import mission_types
router = APIRouter()

@router.put(
    "/new",
    summary="Gera e edita a sorte diária ainda não utilizada de um usuário.",
    description=(
        "Realiza uma nova leitura de sorte para o usuário autenticado. "
        "A sorte é gerada usando um serviço de IA e associada a um registro existente de sorte diária "
        "com status de 'pendente de confirmação'. Caso não haja um registro pendente, retorna um erro."
    ),
    response_description="Mensagem de sucesso com a sorte gerada ou descrição de erro.",
    responses={
        201: {
            "description": "Leitura de sorte gerada com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "daily_lucky": {
                            "leitura": "Grandes mudanças vêm em pacotes pequenos."
                        }
                    }
                }
            },
        },
        400: {
            "description": "Erro na requisição por dados inválidos ou sorte já existente em andamento.",
            "content": {
                "application/json": {
                    "example": {"detail": "User already has a pending daily lucky."}
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
            "description": "Erro interno ao tentar criar ou atualizar a sorte.",
            "content": {
                "application/json": {
                    "example": {"detail": "Ocorreu um erro ao criar o sorteio."}
                }
            },
        },
    },
)
async def put_new_daily_lucky(
    request: Request,
    db: AsyncSession = Depends(get_session), 
    session: AsyncSession = Depends(get_session),
):
    try:
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(
                status_code=401, detail="token information is missing"
            )
        
        try:
            user_id = token_info.id
        except AttributeError:
            raise HTTPException(status_code=400, detail="User id not found in token")
        
        # verifica se o usuario existe
        userexists = await UserSchemaBase.user_exists(db, user_id)
        if not userexists:
            raise HTTPException(
                status_code=400, 
                detail="User does not exist."
            )
        
        # verifica se o usuário tem uma sorte pendente
        id_pending_confirmation = await StatusSchemaBase.get_id_by_name(
            db=session,
            name="pending_confirmation",
        )
        
        daily_lucky_id = await DailyLuckySchemaBase.get_daily_lucky_id_by_user_id_and_status_id(
            session=db, user_id=user_id, status_id=id_pending_confirmation
        )
        if not daily_lucky_id:
            raise HTTPException(
                status_code=400, 
                detail="User não tem sorte diaria pendente."
            )

        # prompt para gerar a sorte via IA
        role = (
            "Você é um biscoito da sorte de um restaurante chinês. Seu papel é entregar uma frase misteriosa, divertida ou reflexiva ao ser aberto. "
            "Pode conter conselhos, mensagens positivas ou até leves advertências com um toque de humor. "
            "Ajusta o prompt para que a IA gere uma frase de sorte. "
            f"Retorne no formato de um dicionário JSON.\n"
            f"Exemplo de resposta: ```json\n{{\"dailylucky\": \"...\"}}\n```\n"
            f"É MUITO IMPORTANTE ESTAR NO FORMATO DETERMINADO PORQUE O RESTANTE DA API DEPENDE DISSO.\n"
        )
            
        prompt_ajustado = "Em uma frase, retorne a sorte aleatória do dia. Pode ser algo positivo, negativo ou curioso, desde que pareça vindo de um biscoito da sorte. seja o mais original possivel"

        openai_service = OpenAIService()

        # pega quantidade de tokens permitida
        user_type_id = await UserSchemaBase.get_user_type_by_id(db, user_id)
        amount_tokens = await UserTypeSchema.get_token_amount_by_id(db, user_type_id)
        max_tokens = int(amount_tokens * 0.3)
        # print(f"Quantidade de tokens: {max_tokens}")
        
        # gera a leitura
        reading = await openai_service.gerar_texto(prompt_ajustado=prompt_ajustado, role=role, max_tokens=max_tokens, temperature=0.9)
        
        # print(f"Leitura gerada: {reading}")
        # Remove possíveis delimitadores de código como ```json ou ``` do início e fim
        status_id = await StatusSchemaBase.get_id_by_name(db, "completed")

        # atualiza no banco
        await DailyLuckySchemaBase.update_daily_lucky(
            session=db, daily_lucky_id=daily_lucky_id, reading=reading, status_id=status_id
        )
        
        reading = JsonExtractor.extract_json_from_reading(reading)

        print(f"Leitura extraída: {reading}")
        
        
        confirm_mission = ConfirmMissionService()
        await confirm_mission.confirm_mission(
            db=session,
            mission_type_id=mission_types[1]["id"],  # "Abrir um biscoito da sorte" é o segundo item,
            user_id=user_id,
        )
        
        return {
            "leitura": reading,
        }
        
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while creating the draw: {str(e)}"
        )
