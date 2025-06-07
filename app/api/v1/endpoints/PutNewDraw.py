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
from app.schemas.reading_style import ReadingStyleSchema # Import ReadingStyleSchema

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
            "description": "Requisição inválida devido a dados de entrada inválidos, reading style inválido ou não acessível ao usuário.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_data": {
                            "summary": "Dados de entrada inválidos.",
                            "value": {"detail": "Dados de entrada inválidos."}
                        },
                        "invalid_reading_style": {
                            "summary": "Reading style does not exist or is not accessible to the user.",
                            "value": {"detail": "Reading style does not exist or is not accessible to the user."}
                        }
                    }
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
        # verifica se o reading style existe
        #tem que verificar se o cliente tem acesso ao reading style
        
            
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
        
        reading_style_exists = await UserTypeSchema.check_reading_style_belongs_to_user(
            db, 
            user_type_id= user_type_id, 
            reading_style_id=draw_data.reading_style
        )
        
        if draw_data.reading_style and not reading_style_exists:
            raise HTTPException(
                status_code=400, 
                detail="Reading style does not exist or is not accessible to the user."
            )
        
        reading_style_name = await ReadingStyleSchema.get_reading_style_name_by_id(db, draw_data.reading_style)
        if not reading_style_name:
            raise HTTPException(
                status_code=400, 
                detail="Reading style name does not exist."
            )        
        reading_style_description = await ReadingStyleSchema.get_reading_style_description_by_id(db, draw_data.reading_style)
        if not reading_style_description:
            raise HTTPException(
                status_code=400, 
                detail="Reading style description does not exist."
            )
        
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
        


        # aqui pegar as draws antigas com a mesma tag, usando o contexto
        
        

        prompt_analise_contexto = (
            f"O contexto fornecido é '{draw_data.context}'.\n"
            f"Os tópicos disponíveis são: {topic_name}.\n"
            f"Analise o contexto e retorne os dois tópicos que mais se encaixam no formato ['topic1', 'topic2']."
            f" o formato deve ser exatamente o seguinte: ['topic1', 'topic2'].\n"
            f"Se não houver tópicos correspondentes, retorne uma lista vazia [].\n"
            f"o formato deve ser respeitado, pois o restante da API depende disso.\n"
        )
        

        role_analise_contexto = (
            "Você é um especialista em análise de contexto e categorização. Sua tarefa é identificar os tópicos mais relevantes com base no contexto fornecido."
        )

        openai_service = OpenAIService()  # Initialize the OpenAIService
        matching_topics = await openai_service.gerar_texto(
            prompt_ajustado=prompt_analise_contexto,
            max_tokens=40,
            role=role_analise_contexto,
            temperature=0.95
        )
        
        

        print(f"Tópicos correspondentes: {matching_topics}")
        
        # return {'matching_topics': matching_topics}
        # Ensure matching_topics is parsed into a Python list
        if isinstance(matching_topics, str):
            import re
            import ast
            match = re.search(r"\[.*?\]", matching_topics, re.DOTALL)
            if match:
                matching_topics = ast.literal_eval(match.group(0))
            else:
                matching_topics = []
        
        list_id_topics = await TopicSchema.get_all_topics_ids_by_list_names(db, matching_topics)
        
        print(f"Lista de ids dos topicos: {list_id_topics}")

        #pega o nome do usuario
        user_name = await UserSchemaBase.get_user_name_by_id(db, user_id) 

        print(f"Nomes das cartas: {cards_names}")
        prompt_ajustado = (
            f"As cartas fornecidas estão na ordem especificada.\n\n"
            f"Realize uma leitura de tarot utilizando as cartas {cards_names}, considerando o contexto '{draw_data.context}', "
            f"o nome do consulente '{user_name}', o tipo de tiragem '{spreadname}' e o nome do baralho '{deckname}'.\n\n"
            f"É **OBRIGATÓRIO** aplicar o estilo de leitura '{reading_style_name}' de forma clara e perceptível durante toda a interpretação, "
            f"seguindo rigorosamente a seguinte descrição: '{reading_style_description}'.\n\n"
            f"A resposta deve ser dividida em três partes: **introdução**, **interpretação individual de cada carta**, e **conclusão**. "
            f"Seja direto e objetivo para que o consulente saiba exatamente como agir após a leitura.\n\n"
            f"O resultado **deve** ser retornado no seguinte formato de dicionário JSON:\n"
            f"```json\n{{'introducao': '...', 'carta_1': '...', 'carta_2': '...', ..., 'conclusao': '...'}}\n```\n\n"
            f"> ⚠️ **É EXTREMAMENTE IMPORTANTE que o formato seja seguido com exatidão, pois a API depende disso.**\n\n"
            f"Se a tiragem tiver aspectos negativos, forneça uma análise honesta e construtiva. "
            f"Todas as cartas fornecidas devem ser interpretadas, sem exceção."
        )

        role = (
            "Você é o melhor tarólogo do mundo, com profundo conhecimento em tarot, simbolismo e interpretações espirituais. "
            "Sua leitura é precisa e sensível, tanto para boas quanto para más notícias. "
            "Seus clientes se sentem confortáveis com você, pois mesmo diante de mensagens difíceis, você transmite tudo com empatia, clareza e acolhimento. "
            "Você não teme revelar verdades desafiadoras — pelo contrário, sabe que isso pode ajudar o consulente a crescer e tomar decisões melhores.\n\n"
            "Sua missão é realizar uma tiragem de tarot excepcionalmente detalhada, honesta e transformadora, mesmo quando as cartas trazem alertas ou desafios. "
            "Use uma linguagem acessível, evitando jargões técnicos. "
            "Fale de forma natural e humana, como um amigo sábio que está ali para apoiar e orientar. "
            "Não pareça robótico ou artificial — seja autêntico, gentil e inspirador.\n\n"
            "Certifique-se de que sua interpretação seja clara, valiosa e ofereça ao consulente reflexões e caminhos possíveis."
        )

        
        # openai_service = OpenAIService()  # Initialize the OpenAIService
        
        #pegar os tokens
        amount_tokens = await UserTypeSchema.get_token_amount_by_id(db, user_type_id)
        # print(f"Quantidade de tokens do usuário: {amount_tokens}")
        max_tokens = (amount_tokens) * (card_count + 2)
        # print(f"Quantidade de tokens: {max_tokens}")
        
        reading = await openai_service.gerar_texto(prompt_ajustado=prompt_ajustado, role=role, max_tokens=max_tokens, temperature=0.9)
         
        
        # if isinstance(reading, str):
        #     import ast
        #     reading= ast.literal_eval(reading)  
        
        # depois da leitura, atualiza o draw com as cartas e o contexto
        # e o status para (active)
        
        status_id = await StatusSchema.get_id_by_name(db, "completed")
        
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