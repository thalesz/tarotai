from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from pydantic import BaseModel

from app.core.deps import get_session
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.planet import PlanetSchemaBase
from app.schemas.user_type import UserTypeSchema, UserTypeSchemaBase
from app.services.openai import OpenAIService
from app.services.extract import JsonExtractor
from app.schemas.personal_sign import PersonalSignSchema
from app.schemas.zodiac import ZodiacSchemaBase
from app.services.planet import  PlanetSignCalculator
from app.services.descricao_astrologica import DescricaoAstrologicaService
from app.schemas.daily_zodiac import DailyZodiacSchemaBase

from app.services.zodiac import DailyZodiacService
router = APIRouter()


# faz um schema pra receber as informações de nascimento do usuário
# e atualiza as informações de nascimento do usuário

class UserBirthInfoSchema(BaseModel):
    birth_date: str
    birth_time: str
    birth_place: str


@router.put(
    "/birth-info",
    summary="Atualiza informações de nascimento do usuário",
    description="""
Atualiza as informações de nascimento do usuário.

- O usuário deve estar autenticado.
- As informações devem incluir a data de nascimento, hora e local.
""",
    response_description="Detalhes das informações de nascimento atualizadas",
    status_code=status.HTTP_200_OK,
    responses={
        201: {
            "description": "Informações atualizadas com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Informações de nascimento atualizadas com sucesso.",
                    
                    }
                }
            }
        },
        400: {"description": "Erro de validação ou dados inválidos"},
        401: {"description": "Token inválido ou ausente"},
        500: {"description": "Erro interno do servidor"}
    }
)
async def put_birth_info(
    payload: UserBirthInfoSchema,
    request: Request,
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    try:
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(status_code=401, detail="Token ausente")

        user_id = getattr(token_info, "id", None)
        if not user_id:
            raise HTTPException(status_code=400, detail="ID do usuário não encontrado")

        userexists = await UserSchemaBase.user_exists(db, user_id)
        if not userexists:
            raise HTTPException(status_code=400, detail="Usuário não encontrado")

        # Usa as informações de nascimento do corpo da requisição (payload)
        await UserSchemaBase.atualizar_info_nascimento(
            db, user_id, payload.birth_date, payload.birth_time, payload.birth_place
        )

        all_planets = await PlanetSchemaBase.get_all_planet_ids_and_names(db)
        user_type_id = await UserSchemaBase.get_user_type_by_id(db, user_id)
        max_tokens = int(await UserTypeSchema.get_token_amount_by_id(db, user_type_id))
        allowed_planets = await UserTypeSchemaBase.get_planets_by_user_type_id(db, user_type_id)

        planet_results = []

        for planet in all_planets:
            planet_id = planet["id"]
            planet_name = planet["name"]

            planet_sign_calculator = PlanetSignCalculator()
            signo, grau = await planet_sign_calculator.planet_sign(
                payload.birth_date,
                payload.birth_time,
                payload.birth_place,
                planet_name.upper()
            )
            
            

            acesso_premium = planet_id in allowed_planets
            descricao_service = DescricaoAstrologicaService()
            result = await descricao_service.gerar_e_salvar_descricao(
                db=db,
                user_id=user_id,
                birth_date=payload.birth_date,
                birth_time=payload.birth_time,
                birth_place=payload.birth_place,
                planet_id=planet_id,
                planet_name=planet_name,
                acesso_premium=acesso_premium,
                max_tokens=max_tokens,
                signo=signo,
                grau=grau
            )

            planet_results.append(result)

        daily_zodiac_service = DailyZodiacService()
        
        
        # tem que apagar todos os zodiacos diários do usuário antes de criar novos
        await daily_zodiac_service.create_daily_zodiac_for_user(
            db=db,
            user_id=user_id,
        )
        await DailyZodiacSchemaBase.delete_old_entries(session=db, user_id=user_id, count=1)


        return {
            "message": "Informações de nascimento atualizadas com sucesso.",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao processar a solicitação: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno do servidor: {str(e)}"
        )
