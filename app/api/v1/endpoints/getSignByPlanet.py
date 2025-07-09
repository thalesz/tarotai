from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.personal_sign import PersonalSignSchemaBase  # Import PersonalSignSchemaBase
from app.schemas.zodiac import ZodiacSchemaBase  # Import ZodiacSignSchemaBase
from app.schemas.user_type import UserTypeSchemaBase, UserTypeSchema  # Import UserTypeSchemaBase and UserTypeSchema
from app.schemas.planet import PlanetSchemaBase  # Import PlanetSchemaBase
from app.schemas.mission_type import MissionTypeSchemaBase  # Import MissionTypeSchemaBase
from app.services.openai import OpenAIService
from app.services.confirmMissionService import ConfirmMissionService  # Import ConfirmMissionService


router = APIRouter()

@router.get(
    "/sign/{id_planet}",
    response_class=JSONResponse,
    summary="Recuperar todos o signo de um planeta de um usuario especifico",
    description="Busca todos os signos de um planeta de um usuário específico. A resposta inclui o ID e o nome do signo.",
    responses={
        200: {
            "description": "Resposta bem-sucedida o signo do planeta passado",
            "content": {
                "application/json": {
                    "example": {
                        "sign": [
                            {"id": 1, "name": "Signo 1", "description": "Descrição do Signo 1"},
                        ]
                    }
                }
            },
        },
        400: {
            "description": "Requisição inválida. Ocorreu um erro ao buscar os planetas.",
            "content": {
                "application/json": {
                    "example": {"error": "Ocorreu um erro"}
                }
            },
        },
    },
)
async def get_all_planets(
    request: Request,
    id_planet: int,
    db: AsyncSession = Depends(get_session),
):
    """
    Retrieve all planets.

    - **db**: Database session dependency.

    Returns a JSON response containing a list of planets with their IDs and names.
    """
    try:
        
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if not token_info or not getattr(token_info, "id", None):
            raise HTTPException(status_code=401, detail="Usuário não autenticado.")

        user_id = token_info.id

        # Verifica se o usuário existe
        if not await UserSchemaBase.user_exists(db, user_id):
            raise HTTPException(status_code=400, detail="Usuário não encontrado.")

        sign = await PersonalSignSchemaBase.get_sign_by_planet_id(db, id_planet, user_id)
        if not sign:
            raise HTTPException(status_code=400, detail="Nenhum signo encontrado para o planeta especificado.")
        name_sign = await ZodiacSchemaBase.get_zodiac_name_by_id(db, sign[0]["zodiac_sign"]) if sign else None
        print("Sign retrieved:", sign)  # Debugging line to check retrieved sign
        print("Zodiac name retrieved:", name_sign)  # Debugging line to check retrieved zodiac name
        
        # verifica se é premium 
        # se for premium, altera a descrição para descrever ainda mais
        
        user_type_id = await UserSchemaBase.get_user_type_by_id(db, user_id)
        print("User type ID:", user_type_id)  # Debugging line to check user type ID
        allowed_planets = await UserTypeSchemaBase.get_planets_by_user_type_id(db, user_type_id)
        print("Allowed planets:", allowed_planets)  # Debugging line to check allowed planets

        leitura = None  # Initialize leitura to avoid reference before assignment
        # se for um planeta permitido, altera a descrição
        if id_planet in allowed_planets and sign:
            max_tokens = int(await UserTypeSchema.get_token_amount_by_id(db, user_type_id))
            
            # cria uma descrição mais detalhada	
            
            #prompt 
            planet_name = await PlanetSchemaBase.get_planet_name_by_id(db, id_planet)
            prompt = (
                f"Explique de forma clara e objetiva o que o planeta {planet_name} representa e influencia na astrologia, detalhando suas áreas de atuação e impacto na personalidade e no destino do indivíduo. "
                f"Em seguida, explique o que significa ter o signo de {name_sign} (grau {float(sign[0]['degree'].replace('°', '')):.3f}°) nesse planeta, descrevendo como essa combinação específica afeta o usuário. "
                f"Resuma o significado desse planeta e do signo nele, focando em informações úteis e práticas. "
                f"Limite a resposta para não exceder {max_tokens} tokens. "
                f"Devolva um único parágrafo explicando o papel desse planeta, seu significado geral e a influência do signo nele para o usuário."
            )
            role = (
                "Você é um astrólogo profissional brasileiro. "
                "Forneça uma análise clara, objetiva e aprofundada, adequada para exibição em uma API, sem rodeios ou repetições. "
                "Evite termos vagos e foque em informações úteis para o usuário final."
            )
            openai_service = OpenAIService()
            leitura = await openai_service.gerar_texto(
                prompt_ajustado=prompt,
                role=role,
                max_tokens=max_tokens,
                temperature=0.9
            )

        # altera aqui sign[0]["zodiac_sign"]
        sign = [
            {
            "id": s["zodiac_sign"],
            "name": name_sign,
            "description": leitura if id_planet in allowed_planets and leitura else s["description"],
            "degree": f'{float(s["degree"].replace("°", "")):.3f}°'
            } for s in sign
        ] if sign else []
        #convert to a list of dictionaries
        
        # verifica se a pessoa usou o sol natal
        
        if planet_name == "Sun":
            confirm_service = ConfirmMissionService()
            mission_type_id = await MissionTypeSchemaBase.get_id_by_name(db, "Consultar o seu sol natal")
            await confirm_service.confirm_mission(db,  mission_type_id, user_id)
            
            
        
        return {"sign": sign} if sign else {"sign": []}
    except HTTPException as e:
        return {"error": e.detail}
