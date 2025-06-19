from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.deps import get_session
from app.schemas.draw import DrawCreate
from app.schemas.user import UserSchemaBase  # Import UserSchemaBase
from app.schemas.spread_type import SpreadTypeSchema  # Import SpreadTypeSchema
from app.schemas.draw import DrawSchemaBase  # Import DrawSchemaBase
from app.services.token import TokenInfoSchema # Import TokenInfoSchema
from app.services.extract import JsonExtractor  # Import JsonExtractor
from app.services.openai import OpenAIService  # Import OpenAIService
from app.schemas.user_type import UserTypeSchema  # Import UserTypeSchema


router = APIRouter()

@router.get(
        "/all",
    summary="Retornar cinco perguntas recomendadas com base no historico do usuário e tipo de tiragem",
    description="Retorna cinco perguntas recomendadas com base no historico do usuário e tipo de tiragem.",
    response_description="Detalhes das perguntas recomendadas.",
    responses={
        200: {
            "description": "Requisição bem-sucedida.",
            "content": {
                "application/json": {
                    "example": {
                        "perguntas": {
                            "pergunta_1": "Qual é o meu futuro profissional?",
                            "pergunta_2": "Como posso melhorar minha vida amorosa?",
                            "pergunta_3": "Quais são os desafios que enfrentarei nos próximos meses?",
                            "pergunta_4": "O que devo fazer para alcançar meus objetivos financeiros?",
                            "pergunta_5": "Como posso fortalecer minhas relações pessoais?"
                        }
                    }
                }
            },
        },
        400: {
            "description": "Requisição inválida devido a dados de entrada inválidos.",
            "content": {
                "application/json": {
                    "example": {"detail": "Dados de entrada inválidos."}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor.",
            "content": {
                "application/json": {
                    "example": {"detail": "Ocorreu um erro ao criar o sorteio."}
                }
            },
        },
    },
)
async def post_new_draw(
    request: Request,
    draw_data: DrawCreate,
    db: AsyncSession = Depends(get_session)
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
        # verifica se o tipo de spread existe
        spreadexists = await SpreadTypeSchema.spread_type_exists(db, draw_data.spread_type_id)
        
        # spread_type_exists(db, draw_data.spread_type_id)
        if not spreadexists:
            raise HTTPException(
                status_code=400, 
                detail="Spread type does not exist."
            )
            
        # pega o nome do tipo de spread
        spread_type_name = await SpreadTypeSchema.get_spread_type_name_by_id(db, draw_data.spread_type_id)
        
        context_avaliable = await UserTypeSchema.get_context_amount_by_id(db, user_id)
        
        
        # tem que pegar todos os contextos ja dados para o usuario
        user_contexts = await DrawSchemaBase.get_user_contexts(db, user_id, count=context_avaliable)
        
        role = (
            "Você é um especialista em tarô. "
            "Com base no histórico de perguntas do usuário e no tipo de tiragem escolhido, "
            "formule cinco perguntas personalizadas e relevantes para a próxima leitura."
        )

        if not user_contexts:
            prompt = (
            f"O usuário escolheu o tipo de tiragem '{spread_type_name}'. "
            "Não há histórico de perguntas anteriores. "
            "Sugira cinco perguntas recomendadas para esse tipo de tiragem. "
            "Se o tipo de tiragem for 'amor', por exemplo, as perguntas devem ser relacionadas a amor, relacionamentos e sentimentos. "

            "O resultado deve ser retornado exatamente no seguinte formato, dentro de um bloco de código markdown com a linguagem 'json':\n"
            "```json\n"
            "{\"pergunta_1\": \"...\", \"pergunta_2\": \"...\", \"pergunta_3\": \"...\", \"pergunta_4\": \"...\", \"pergunta_5\": \"...\"}\n"
            "```\n"
            "Não inclua explicações, comentários ou qualquer texto fora do bloco de código. "
            "Use aspas duplas em todas as chaves e valores."
            )
        else:
            prompt = (
            f"O usuário escolheu o tipo de tiragem '{spread_type_name}'. "
            "Histórico de perguntas anteriores do usuário: "
            f"{user_contexts}. "
            "Com base nesse histórico e no tipo de tiragem, sugira cinco perguntas novas e relevantes. "
            "Se o tipo de tiragem for 'amor', por exemplo, as perguntas devem ser relacionadas a amor, relacionamentos e sentimentos. "
            "O resultado deve ser retornado exatamente no seguinte formato, dentro de um bloco de código markdown com a linguagem 'json':\n"
            "```json\n"
            "{\"pergunta_1\": \"...\", \"pergunta_2\": \"...\", \"pergunta_3\": \"...\", \"pergunta_4\": \"...\", \"pergunta_5\": \"...\"}\n"
            "```\n"
            "Não inclua explicações, comentários ou qualquer texto fora do bloco de código. "
            "Use aspas duplas em todas as chaves e valores."
            )
        # chama o openai para gerar as perguntas
        openai_service = OpenAIService()
        user_type_id = await UserSchemaBase.get_user_type_by_id(db, user_id)
        amount_tokens = await UserTypeSchema.get_token_amount_by_id(db, user_type_id)

        questions = await openai_service.gerar_texto(
                    prompt_ajustado=prompt,
                    role=role,
                    max_tokens=amount_tokens* 2,  # Multiplica por 2 para garantir que o modelo tenha espaço suficiente para gerar as perguntas
                    temperature=0.9
                )
        
        print(f"Perguntas geradas: {questions}")
        
        # Extrai o JSON do texto gerado
        json_extractor = JsonExtractor()
        extracted_json = json_extractor.extract_json_from_reading(reading=questions)
        # agora retorna o json extraido
        if not extracted_json:  
            raise HTTPException(
                status_code=400, 
                detail="Failed to extract valid JSON from the generated text."
            )
        #retorna pro user
        return {"perguntas": extracted_json}
        

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while creating the draw: {str(e)}"
        )