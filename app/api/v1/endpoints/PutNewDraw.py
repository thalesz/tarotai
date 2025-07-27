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
# from app.schemas.user_type import UserTypeSchemaBase  # Import UserTypeSchemaBase
from app.services.token import TokenInfoSchema # Import TokenInfoSchema
from app.services.openai import OpenAIService  # Import OpenAIService
from app.schemas.topic import TopicSchema  # Import TopicSchema
from app.schemas.status import StatusSchema  # Import StatusSchema
from app.schemas.reading_style import ReadingStyleSchema # Import ReadingStyleSchema
from app.schemas.review import ReviewSchema  # Import ReviewSchema
from app.schemas.mission_type import MissionTypeSchemaBase  # Import MissionTypeSchemaBase
from app.services.confirmMissionService import ConfirmMissionService

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
            
        #verifica se as cartas estão em mesma quantidade que o is_reversed
        
        #is reversed é opcional, se não for enviado, não verifica
        if draw_data.is_reversed is not None and len(draw_data.cards) != len(draw_data.is_reversed):
            raise HTTPException(
                status_code=400, 
                detail="The number of cards and the number of is_reversed values must match."
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
            f"Analise o contexto e retorne todos os tópicos que se encaixam, no formato ['topic1', 'topic2', ...].\n"
            f"O formato deve ser exatamente o seguinte: ['topic1', 'topic2', ...].\n"
            f"Se não houver tópicos correspondentes, retorne uma lista vazia []. Mande no máximo tres topicos, não ultrapasse.\n"
            f"O formato deve ser respeitado, pois o restante da API depende disso.\n"
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
        
        

        # print(f"Tópicos correspondentes: {matching_topics}")
        
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
        
        # print(f"Lista de ids dos topicos: {list_id_topics}")
        
        # tem que pegar o limite de draw por tipo de usuario

        context_amount = await UserTypeSchema.get_context_amount_by_id(db, user_type_id)
        # pegar o id de todas as tiragens que tem pelo menos um dos topicos
        draws_with_topics = await DrawSchemaBase.get_draw_ids_by_topics(
            db,
            user_id=user_id,
            spread_type_id=draw_data.spread_type_id,
            topics=list_id_topics
        )
        # print(f"IDs de draws com tópicos correspondentes: {draws_with_topics}")
        # variavel para salvar o contexto
        preview_context = []
        # lista para armazenar similaridades e detalhes
        similar_draws = []

        # para cada um dos ids vamos comparar o contexto passado com o contexto do id
        for id in draws_with_topics:
            context = await DrawSchemaBase.get_context_by_id(db, id)

            prompt_comparador = (
                f"Compare os dois contextos a seguir, considerando que podem ser diferentes facetas ou perspectivas da mesma história. "
                f"Mesmo que usem palavras diferentes, avalie se tratam essencialmente do mesmo tema ou situação central:\n"
                f"Contexto 1: '{draw_data.context}'\n"
                f"Contexto 2: '{context}'\n"
                f"Retorne um valor numérico de similaridade entre 0 e 1, onde 1 indica que são essencialmente o mesmo contexto (mesmo que descritos de formas diferentes), "
                f"e 0 indica que não têm relação. "
                f"Seja objetivo e considere o significado central dos contextos, não apenas as palavras. "
                f"Retorne apenas o número decimal, sem explicações ou texto adicional."
            )

            role_comparador = (
                "Você é um especialista em análise semântica de textos em português. "
                "Sua tarefa é comparar dois contextos fornecidos, avaliando se, mesmo com palavras diferentes, tratam essencialmente do mesmo tema ou situação central. "
                "Considere diferentes facetas ou perspectivas da mesma história. "
                "Retorne apenas um número decimal entre 0 e 1, onde 1 indica contextos essencialmente iguais e 0 indica contextos sem relação. "
                "Não forneça explicações, comentários ou qualquer texto adicional — apenas o valor numérico. "
                "Seja rigoroso e objetivo, considerando o significado central dos contextos, não apenas as palavras."
            )

            token_comparador = 10
            similaridade = await openai_service.gerar_texto(prompt_ajustado=prompt_comparador, role=role_comparador, max_tokens=token_comparador, temperature=0.9)

            try:
                similaridade_float = float(similaridade)
            except Exception:
                similaridade_float = 0.0

            if similaridade and similaridade_float > 0.5:
                previous_draw = await DrawSchemaBase.get_draw_details_by_id(db, id)
                # print(f"Draw anterior: {previous_draw}")

                previous_reading = previous_draw.get('reading')
                if isinstance(previous_reading, str):
                    try:
                        previous_reading = JsonExtractor.extract_json_from_reading(previous_reading)
                    except Exception:
                        pass

                prompt_resumo_leitura = (
                    f"Resuma a leitura de tarot a seguir em uma frase curta e objetiva:\n"
                    f"Contexto: {previous_draw.get('context')}\n"
                    f"Nome do Baralho: {await DeckSchema.get_deck_name_by_id(db, previous_draw.get('deck_id'))}\n"
                    f"Tipo de Spread: {await SpreadTypeSchema.get_spread_type_name_by_id(db, previous_draw.get('spread_type_id'))}\n"
                    f"Carta(s): {previous_draw.get('cards')}\n"
                    f"Leitura: {previous_reading}\n"
                )
                role_resumo_leitura = (
                    "Você é um especialista em síntese de informações."
                    "Sua tarefa é resumir a leitura de tarot fornecida, mantendo os pontos mais importantes e relevantes."
                )

                resumo_leitura = await openai_service.gerar_texto(
                    prompt_ajustado=prompt_resumo_leitura,
                    role=role_resumo_leitura,
                    max_tokens=50,
                    temperature=0.9
                )
                # print(f"Resumo da leitura anterior: {resumo_leitura}")
                
                #pegar a avaliação da tiragem somente se existir avaliação
                review = await ReviewSchema.get_rating_and_comment_by_draw_id(db, id)
                
                if review:
                    rating, comment = review
                else:
                    rating, comment = None, None

                similar_draws.append({
                    "similaridade": similaridade_float,
                    "context": context,
                    "deck_name": await DeckSchema.get_deck_name_by_id(db, previous_draw.get('deck_id')),
                    "spread_type_name": await SpreadTypeSchema.get_spread_type_name_by_id(db, previous_draw.get('spread_type_id')),
                    "cards": previous_draw.get('cards'),
                    "reading_summary": resumo_leitura,
                    "rating": rating,
                    "comment": comment,
                    
                    #se existir is_reversed, adiciona
                    "is_reversed": previous_draw.get('is_reversed', []),
                })

        # Ordena: primeiro por rating (se existir, maior primeiro), depois por similaridade (maior primeiro)
        def sort_key(x):
            # Se rating não existe, considera -1 para ficar depois dos que têm rating
            return (x["rating"] if x["rating"] is not None else -1, x["similaridade"])

        similar_draws_sorted = sorted(similar_draws, key=sort_key, reverse=True)
        preview_context = similar_draws_sorted[:context_amount]

        # pega o nome do usuario
        user_name = await UserSchemaBase.get_user_name_by_id(db, user_id)
        
        mandala_id = await SpreadTypeSchema.get_id_by_name(db, "Mandala Astrológica")


        # Monta o prompt ajustado incluindo o contexto anterior, se houver
        # Monta string com contextos anteriores, se existirem
        previous_contexts_str = ""
        if preview_context:
            # print(f"Contextos anteriores encontrados: {preview_context}")
            previous_contexts_str = "\n".join(
                [
                    f"- Contexto anterior: '{ctx['context']}', Baralho: '{ctx['deck_name']}', Spread: '{ctx['spread_type_name']}', "
                    f"Cartas: {await CardSchema.get_cards_names_by_group_ids(db, ctx['cards'])}"
                    + (
                        f", Está invertida?: "
                        + (
                            str(ctx['is_reversed'])
                            if ctx.get('is_reversed') and len(ctx['is_reversed']) == len(ctx['cards'])
                            else str([False] * len(ctx['cards']))
                        )
                    )
                    + f", Resumo: {ctx['reading_summary']}"
                    + (
                        f", Avaliação do usuário: {ctx['rating']}, Comentário do usuário: '{ctx['comment']}'"
                        if ctx['rating'] is not None else ""
                    )
                    for ctx in preview_context
                ]
            )

        # Monta string com informações de cartas invertidas, se houver
        reversed_info = ""
        if draw_data.is_reversed is not None:
            reversed_info = "\n".join(
                [
                    f"- {card_name}: {'invertida' if is_rev else 'normal'}"
                    for card_name, is_rev in zip(cards_names, draw_data.is_reversed)
                ]
            )
            reversed_info = f"Situação de cada carta (invertida ou normal):\n{reversed_info}\n\n"

        # Parte comum do prompt
        explicacao_invertidas = (
            f"{reversed_info}"
            f"Para cada carta, utilize a lista 'is_reversed': {draw_data.is_reversed}.\n"
            f"Cada item da lista 'is_reversed' corresponde exatamente à carta na mesma posição da lista de cartas.\n"
            f"Se o valor correspondente for True, interprete a carta como invertida (com significado oposto ou alterado); se for False, interprete normalmente.\n"
            f"Exemplo: se is_reversed = [False, True, False], então a primeira e terceira carta são normais, e a segunda está invertida.\n"
            f"Cartas invertidas devem receber uma análise diferenciada, destacando como o significado se transforma em relação à posição normal.\n\n"
        )

        # Prompt base
        prompt_base = (
            f"As cartas fornecidas estão na ordem especificada.\n\n"
            f"{explicacao_invertidas}"
        )

        # Acrescenta contextos anteriores se houver
        if previous_contexts_str:
            prompt_base += (
                f"Considere também os seguintes contextos e leituras anteriores do consulente para enriquecer sua análise e trazer informações relevantes para a consulta atual:\n"
                f"{previous_contexts_str}\n\n"
            )
            
        # print(f"Prompt base: {prompt_base}")

        # Parte final do prompt
        prompt_final = (
            f"Realize uma leitura de tarot utilizando as cartas {cards_names}, considerando o contexto '{draw_data.context}', "
            f"o nome do consulente '{user_name}', o tipo de tiragem '{spreadname}' e o nome do baralho '{deckname}'.\n\n"
            f"É OBRIGATÓRIO aplicar o estilo de leitura '{reading_style_name}' de forma clara e perceptível durante toda a interpretação, "
            f"seguindo rigorosamente a seguinte descrição: '{reading_style_description}'.\n\n"
            f"A resposta deve ser dividida em três partes: introdução, interpretação individual de cada carta (nomeando cada uma), e conclusão.\n"
            f"Seja direto e objetivo para que o consulente saiba exatamente como agir após a leitura.\n\n"
            f"Se a pergunta for prática (exemplo: pedir sugestão de pizza), responda de forma clara e assertiva, sem rodeios.\n\n"
            f"O resultado DEVE ser retornado no seguinte formato de dicionário JSON VÁLIDO (com aspas duplas):\n"
            f"```json\n{{\"introducao\": \"...\", \"carta_1\": \"...\", \"carta_2\": \"...\", ..., \"conclusao\": \"...\"}}\n```\n\n"
            f"⚠️ É EXTREMAMENTE IMPORTANTE que o formato seja seguido com exatidão, usando aspas duplas em todas as chaves e valores, pois a API depende disso.\n\n"
            f"Se a tiragem tiver aspectos negativos, forneça uma análise honesta, construtiva e realista. "
            f"Todas as cartas fornecidas devem ser interpretadas, sem exceção."
        )

        # Prompt ajustado completo
        prompt_ajustado = prompt_base + prompt_final

        # Role fixo
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


        #pegar os tokens
        amount_tokens = await UserTypeSchema.get_token_amount_by_id(db, user_type_id)
        max_tokens = (amount_tokens) * (card_count + 2)

        reading = await openai_service.gerar_texto(prompt_ajustado=prompt_ajustado, role=role, max_tokens=max_tokens, temperature=0.9)

        status_id = await StatusSchema.get_id_by_name(db, "completed")

        # Se draw_data.is_reversed for None, envia lista vazia
        is_reversed = draw_data.is_reversed if draw_data.is_reversed is not None else []
        
        #verifica se a pessoa tem o estilo da carta
        if draw_data.card_style is not None:
            accessible_card_styles = await UserTypeSchema.get_accessible_card_styles_by_user_type(
                db, user_type_id
            )
            if draw_data.card_style not in accessible_card_styles:
                raise HTTPException(
                    status_code=400,
                    detail="Card style does not exist or is not accessible to the user."
                )
        #agora a gente atribui o valor dele para 1 caso venha None 
        if draw_data.card_style is None:
            draw_data.card_style = 1  # Default value if not provided
        
        
        
        draw = await DrawSchemaBase.update_draw_after_standard_reading(
            db, 
            draw_id=id_draw, 
            user_id=user_id, 
            spread_type_id=draw_data.spread_type_id,
            deck_id=draw_data.deck_id,
            cards=draw_data.cards,
            context=draw_data.context,
            status_id=status_id,
            reading=reading,
            topics=list_id_topics,
            is_reversed=is_reversed,
            card_style=draw_data.card_style
        )

        reading = JsonExtractor.extract_json_from_reading(reading)
        confirm_service = ConfirmMissionService()

        # se for do tipo mandala astrológica, tem que confirmar a missão do usuário
        if draw_data.spread_type_id == mandala_id:  # Mandala Astrológica
            
            mission_type_id = await MissionTypeSchemaBase.get_id_by_name(db, "Fazer uma leitura do tipo Mandala Astrológica")
            await confirm_service.confirm_mission(db,  mission_type_id, user_id)
        
        id_analitico = await ReadingStyleSchema.get_id_by_name(db, "Analítico")
        
        if draw_data.reading_style == id_analitico:
            # se for do tipo analítico, tem que confirmar a missão do usuário
            
            print("Fazer uma leitura no modo analitico")
            mission_type_id = await MissionTypeSchemaBase.get_id_by_name(db, "Fazer uma leitura no modo analítico")
            await confirm_service.confirm_mission(db,  mission_type_id, user_id)
            
        
        
        return {"leitura": reading}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro ao atualizar draw: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao buscar os eventos.")

