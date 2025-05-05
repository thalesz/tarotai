from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from fastapi.responses import JSONResponse

from app.core.deps import get_session
from app.schemas.draw import DrawUpdate  # Import DrawUpdate schema
from app.schemas.spread_type import SpreadTypeSchema  # Import SpreadTypeSchema
from app.schemas.user import UserSchemaBase  # Import UserSchemaBase
from app.schemas.draw import DrawSchemaBase  # Import DrawSchemaBase
from app.schemas.card import CardSchema  # Import CardSchema
from app.schemas.deck import DeckSchema  # Import DeckSchema
from app.schemas.user_type import UserTypeSchema  # Import ClientSchema
from app.services.token import TokenInfoSchema # Import TokenInfoSchema
from app.services.openai import OpenAIService  # Import OpenAIService
from app.schemas.topic import TopicSchema  # Import TopicSchema
from app.schemas.status import StatusSchema  # Import StatusSchema

from app.services.extract import JsonExtractor  # Import JsonExtractor

router = APIRouter()



@router.put(
    "/update",
    summary="Atualizar uma tiragem existente",
    description="Atualiza as cartas, contexto e outros detalhes de uma tiragem de tarot existente. "
                "Este endpoint valida os dados de entrada, verifica permissões de usuário e baralho, "
                "e realiza uma leitura de tarot usando serviços de IA.",
    response_description="Detalhes da tiragem atualizada, incluindo a leitura e os tópicos associados.",
    responses={
        200: {
            "description": "Atualização bem-sucedida da tiragem.",
            "content": {
                "application/json": {
                    "example": {
                        "leitura": {
                            "introducao": "Esta é a introdução da leitura de tarot.",
                            "carta_1": "Interpretação da primeira carta.",
                            "carta_2": "Interpretação da segunda carta.",
                            "conclusao": "Esta é a conclusão da leitura de tarot."
                        }
                    }
                }
            },
        },
        400: {
            "description": "Requisição inválida devido a dados de entrada inválidos ou ausentes.",
            "content": {
                "application/json": {
                    "example": {"detail": "Dados de entrada inválidos."}
                }
            },
        },
        401: {
            "description": "Acesso não autorizado devido a token ausente ou inválido.",
            "content": {
                "application/json": {
                    "example": {"detail": "Informações do token estão ausentes."}
                }
            },
        },
        404: {
            "description": "Recurso não encontrado, como uma tiragem inexistente.",
            "content": {
                "application/json": {
                    "example": {"detail": "Draw not found."}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor devido a problemas no banco de dados ou outros.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while updating the draw."}
                }
            },
        },
    },
)



async def update_draw(
    request: Request,
    draw_data: DrawUpdate,
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
        # verifica se o user existe
        userexists = await UserSchemaBase.user_exists(db, user_id)
        #print("userexists: ", userexists)
        if not userexists:
            raise HTTPException(
                status_code=400, 
                detail="User does not exist."
            )
        # verifica se o tipo de spread existe
        spreadexists = await SpreadTypeSchema.spread_type_exists(db, draw_data.spread_type_id)
        #print("spreadexists: ", spreadexists)
        
        # pega o nome pelo id
        spreadname = await SpreadTypeSchema.get_spread_type_name_by_id(db, draw_data.spread_type_id)
        
        # spread_type_exists(db, draw_data.spread_type_id)
        if not spreadexists:
            raise HTTPException(
                status_code=400, 
                detail="Spread type does not exist."
            )
            
        #verifica se o usuario tem um draw pendente do mesmo tipo de spread e pegar esse id
        id_draw = await DrawSchemaBase.get_pending_draw_id_by_user_and_spread_type(db, user_id, draw_data.spread_type_id)
        if not id_draw:
            raise HTTPException(
            status_code=400,
            detail="User does not have any pending draws available."
            )
        
        #print(f"ID do draw pendente: {id_draw}")
        
        #verifica se o deck existe
        deckexists = await DeckSchema.deck_exists(db, draw_data.deck_id)
        if draw_data.deck_id and not deckexists:
            raise HTTPException(
                status_code=400, 
                detail="Deck does not exist."
                
            )
        #print(f"ID do deck: {draw_data.deck_id}")
        
        # pega o nome do deck pelo id
        deckname = await DeckSchema.get_deck_name_by_id(db, draw_data.deck_id)
            
        #pega o id do tipo de usuario
        user_type_id = await UserSchemaBase.get_user_type_by_id(db, user_id)
        
        
        
        
        #print(f"ID do tipo de usuario: {user_type_id}")
        # verifica se o cliente tem o deck
        client_check = await UserTypeSchema.check_deck_belongs_to_user(db, user_type_id, draw_data.deck_id)
        if draw_data.deck_id and not client_check:
            raise HTTPException(
                status_code=400, 
                detail="User does not have access to this deck."
            )
        
        # verifica se a quantidade de cartas é igual ao tipo de spread
        card_count = await SpreadTypeSchema.get_card_count(db, draw_data.spread_type_id)
        #print(f"Quantidade de cartas do tipo de spread: {card_count}")
        if draw_data.cards and len(draw_data.cards) != card_count:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid number of cards. Expected {card_count}."
            )   
            
        # verifica se a as cartas estão duplicadas
        if draw_data.cards and len(draw_data.cards) != len(set(draw_data.cards)):
            raise HTTPException(
                status_code=400, 
                detail="Duplicate cards found."
            )
            
        #verifica se as cartas são todas do mesmo deck
        deck_check = await CardSchema.check_cards_belong_to_deck(db,  draw_data.deck_id, draw_data.cards,)
        #print("deck_check: ", deck_check)
        if not deck_check:
            raise HTTPException(
                status_code=400, 
                detail="Cards do not belong to the same deck."
            )

        #pegar o nome das cartas que é uma lista de strings        
        cards_names = await CardSchema.get_cards_names_by_group_ids(db, draw_data.cards)
        
        #retorna uma lista de strings com os nomes das cartas
        #print(f"Nome das cartas: {cards_names}")
        # return {'cards_names' : cards_names}
        
        #verifica se o contexto foi enviado 
        # se o contexto for None retorna erro pq nesse precisa
        # do contexto para fazer a tiragem de cartas
        if draw_data.context is None:
            raise HTTPException(
                status_code=400, 
                detail="Context is required for the draw."
            )
        
        # se ele tiver, temos que fazer a tiragem de cartas usando o servico de ia da azure 
        
        topic_name = await TopicSchema.get_all_topics_names(db)
        
        prompt_analise_contexto = (
            f"O contexto fornecido é '{draw_data.context}'.\n"
            f"Os tópicos disponíveis são: {topic_name}.\n"
            f"Analise o contexto e retorne os dois tópicos que mais se encaixam no formato ['topic1', 'topic2']."
        )
        

        role_analise_contexto = (
            "Você é um especialista em análise de contexto e categorização. Sua tarefa é identificar os tópicos mais relevantes com base no contexto fornecido."
        )

        openai_service = OpenAIService()  # Initialize the OpenAIService
        matching_topics = await openai_service.gerar_texto(
            prompt_ajustado=prompt_analise_contexto,
            max_tokens=30,
            role=role_analise_contexto,
            temperature=0.95
        )

        #print(f"Tópicos correspondentes: {matching_topics}")
        
        # return {'matching_topics': matching_topics}
        # Ensure matching_topics is parsed into a Python list
        if isinstance(matching_topics, str):
            import ast
            matching_topics = ast.literal_eval(matching_topics)
        
        list_id_topics = await TopicSchema.get_all_topics_ids_by_list_names(db, matching_topics)
        #print(f"Lista de ids dos topicos: {list_id_topics}")

        #pega o nome do usuario
        user_name = await UserSchemaBase.get_user_name_by_id(db, user_id) 
        
        
        prompt_ajustado = (
            f"As cartas fornecidas estão na ordem especificada.\n"
            f"Faça uma tiragem de tarot com as cartas {cards_names}, o contexto '{draw_data.context}', o nome do usuário '{user_name}', "
            f"o tipo de tiragem '{spreadname}', e o nome do deck '{deckname}'.\n"
            f"Separe a resposta em introdução, tiragem para cada carta, e conclusão, e tem que ser objetivo ou seja no final o consultante tem que saber o que fazer "
            f" Retorne no formato de um dicionário JSON.\n"
            f"Exemplo de resposta: ```json\n{{'introducao': '...', 'carta_1': '...', 'carta_2': '...', 'conclusao': '...'}}\n```\n"
            f" É MUITO IMPORTANTE ESTAR NO FORMATO DETERMINADO POR QUE O RESTANTE DA API DEPENDE DISSO.\n"
        )
        role = (
            "Você é o melhor tarólogo do mundo, com vasto conhecimento em tarot, simbolismo e consegue interpretar cartas de forma precisa tanto para noticias boas quanto ruins."
            "Seus clientes se sente confortavel, voce consegue ser agradavel mesmo com noticias ruins que as vezes tem voce o ajuda. Vocenão tem medo de dar noticias ruins" 
            "Sua missão é realizar uma tiragem de tarot excepcionalmente detalhada e precisa mesmo que a tiragem seja negativa. "
            "Você deve usar uma linguagem clara e acessível, evitando jargões técnicos. Sem soar robótico ou artificial, "
            "você deve se esforçar para ser o mais humano possível. como um amigo que está ajudando o outro."
            "Certifique-se de que a interpretação seja precisa, inspiradora e ofereça insights valiosos ao consulente."
        )
        
        # openai_service = OpenAIService()  # Initialize the OpenAIService
        
        #pegar os tokens
        amount_tokens = await UserTypeSchema.get_token_amount_by_id(db, user_type_id)
        max_tokens = (amount_tokens + 2) * card_count
        print(f"Quantidade de tokens: {max_tokens}")
        
        reading = await openai_service.gerar_texto(prompt_ajustado=prompt_ajustado, role=role, max_tokens=max_tokens, temperature=0.9)
         
        
        # if isinstance(reading, str):
        #     import ast
        #     reading= ast.literal_eval(reading)  
        
        # depois da leitura, atualiza o draw com as cartas e o contexto
        # e o status para (active)
        
        status_id = await StatusSchema.get_id_by_name(db, "active")
        
        draw = await DrawSchemaBase.update_draw_after_standard_reading(
            db, 
            draw_id=id_draw, 
            user_id=user_id, 
            spread_type_id=draw_data.spread_type_id,
            deck_id=draw_data.deck_id,
            cards=draw_data.cards,
            context=draw_data.context,
            status_id=status_id,  # Assuming 1 is the ID for 'active'
            reading=reading,
            topics=list_id_topics
        )
        
        # Split the reading into introduction, individual card readings, and conclusion

        reading = JsonExtractor.extract_json_from_reading(reading)
        #print(f"Prompt ajustado: {prompt_ajustado}")
        #print(f"Leitura: {reading}")
        return {"leitura": reading}

        
    except SQLAlchemyError as e:
        print(f"SQLAlchemyError: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while updating the draw: {str(e)}") from e