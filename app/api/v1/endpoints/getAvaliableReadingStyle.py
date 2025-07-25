
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from app.services.token import TokenInfoSchema # Import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.spread_type import SpreadTypeSchemaBase  # Import SpreadTypeSchemaBase
from app.schemas.draw import DrawSchemaBase  # Import DrawSchemaBase
from app.schemas.reading_style import ReadingStyleSchemaBase  # Import ReadingStyleSchemaBase
from app.schemas.user_type import UserTypeSchemaBase  # Import UserTypeSchemaBase
router = APIRouter()


@router.get(
    "/all",
    summary="Obter os estilos de leitura disponíveis para um usuário",
    description="Este endpoint retorna uma lista de estilos de leitura disponíveis para o usuário autenticado.",
    response_description="Uma lista contendo os IDs, nomes dos estilos de leitura disponíveis.",
    responses={
        200: {
            "description": "Lista de estilos de leitura disponíveis retornada com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "name": "Direto",
                                "description": "Leitura direta e objetiva, sem complicações.",
                                "available": True
                            },
                            {
                                "id": 2,
                                "name": "Intuitivo",
                                "description": "Leitura baseada na intuição e sentimentos do leitor.",
                                "available": False
                            },
                            {
                                "id": 3,
                                "name": "Analítico",
                                "description": "Leitura detalhada e minuciosa, com foco em cada aspecto.",
                                "available": False
                            },
                            {
                                "id": 4,
                                "name": "Mistico",
                                "description": "Leitura com uma abordagem mística e espiritual.",
                                "available": True
                            },
                            {
                                "id": 5,
                                "name": "Poético",
                                "description": "Leitura que utiliza a linguagem poética e simbólica.",
                                "available": True
                            },
                            {
                                "id": 6,
                                "name": "Psicológico",
                                "description": "Leitura focada em aspectos psicológicos e autoconhecimento.",
                                "available": False
                            },
                            {
                                "id": 7,
                                "name": "Pragmático",
                                "description": "Leitura prática, voltada para soluções e ações concretas.",
                                "available": False
                            }
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
async def get_all_reading_styles(
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
        if not userexists:
            raise HTTPException(
                status_code=400, 
                detail="User does not exist."
            )
        
        # pega o cliente do usuario
        id_user_type = await UserSchemaBase.get_user_type_by_id(db, user_id)

        reading_styles_avaliable = await UserTypeSchemaBase.get_reading_styles_by_user_type_id(db, id_user_type)
        all_reading_styles = await ReadingStyleSchemaBase.get_all_reading_styles(db)
        
        reading_styles_response = []
        for style in all_reading_styles:
            available = style.id in reading_styles_avaliable
            reading_styles_response.append({
                "id": style.id,
                "name": style.name,
                "description": style.description,
                "available": available
            })
        return {"data": reading_styles_response}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
