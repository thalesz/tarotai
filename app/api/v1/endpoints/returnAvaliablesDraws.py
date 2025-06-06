
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from app.services.token import TokenInfoSchema # Import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.spread_type import SpreadTypeSchemaBase  # Import SpreadTypeSchemaBase
from app.schemas.draw import DrawSchemaBase  # Import DrawSchemaBase
router = APIRouter()


@router.get(
    "/avaliable",
    summary="Obter tiragens disponíveis por tipo",
    description="Este endpoint retorna uma lista de tipos de tiragem com a quantidade de tiragens disponíveis para cada tipo, associadas ao usuário autenticado.",
    response_description="Uma lista contendo os IDs, nomes dos tipos de tiragem e a quantidade de tiragens disponíveis.",
    responses={
        200: {
            "description": "Lista de tiragens disponíveis retornada com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {"spread_type_id": 1, "spread_type_name": "Cruz Celta", "available_draws_count": 10},
                            {"spread_type_id": 2, "spread_type_name": "Três Cartas", "available_draws_count": 5}
                        ]
                    }
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
        400: {
            "description": "Erro de validação ou usuário não encontrado.",
            "content": {
                "application/json": {
                    "example": {"detail": "User does not exist."}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor.",
            "content": {
                "application/json": {
                    "example": {"detail": "Ocorreu um erro ao buscar as tiragens disponíveis."}
                }
            },
        },
    },
)

async def get_all_decks(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    try:
        # pegar id do usuario enviado pelo token
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(
                status_code=401, detail="token information is missing"
            )
        
        try:
            user_id = token_info.id
        except AttributeError:
            raise HTTPException(status_code=400, detail="User id not found in token")
        # verifica se o user existe
        userexists = await UserSchemaBase.user_exists(db, user_id)
        #print("userexists: ", userexists)
        if not userexists:
            raise HTTPException(
                status_code=400, 
                detail="User does not exist."
            )
        
        
        #ok, tem o id agora vc precisa pegar os tipos de tiragem
        # e a quantidade de tiragens disponiveis
        
        spread_types = await SpreadTypeSchemaBase.get_all_spread_types(session=db)
        # Agora que tem os tipos de tiragem, pegar a quantidade de tiragens disponíveis para cada tipo
        result = []
        for spread_type in spread_types:
            count = await DrawSchemaBase.get_pending_draw_count_by_user_and_spread_type(
            session=db, user_id=user_id, spread_type_id=spread_type.id
            )
            result.append({
            "spread_type_id": spread_type.id,
            "spread_type_name": spread_type.name,
            "available_draws_count": count
            })
        
        return {"data": result}  
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
