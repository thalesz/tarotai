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
import asyncio

from app.services.openai import OpenAIService  # Import OpenAIService
from app.schemas.topic import TopicSchema  # Import TopicSchema
from app.schemas.status import StatusSchema  # Import StatusSchema
from app.schemas.reading_style import ReadingStyleSchema # Import ReadingStyleSchema
from app.schemas.review import ReviewSchema  # Import ReviewSchema
from app.schemas.mission_type import MissionTypeSchemaBase  # Import MissionTypeSchemaBase
from app.services.confirmMissionService import ConfirmMissionService

from app.services.extract import JsonExtractor  # Import JsonExtractor
from app.prompts.analise_contexto import (
    prompt_analise_contexto_template,
    role_analise_contexto,
)
from app.prompts.comparador import (
    prompt_comparador_template,
    role_comparador,
)
from app.prompts.resumo_leitura import (
    prompt_resumo_leitura_template,
    role_resumo_leitura,
)
from app.prompts.readings import (
    prompt_base_template,
    prompt_final_template,
    role as readings_role,
)

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
        cards_names = await CardSchema.get_cards_names_by_group_ids(db, draw_data.cards, keep_order=True)
        
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
        
        

        prompt_analise_contexto = prompt_analise_contexto_template.format(
            context=draw_data.context,
            topic_name=topic_name,
        )

        openai_service = OpenAIService()  # Initialize the OpenAIService

        # Limit concurrent OpenAI requests to avoid spikes (adjust as needed)
        _openai_semaphore = asyncio.Semaphore(5)

        async def _call_openai(prompt_ajustado, role, max_tokens, temperature):
            async with _openai_semaphore:
                return await openai_service.gerar_texto(
                    prompt_ajustado=prompt_ajustado,
                    role=role,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
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

        # Parallelize comparator calls and subsequent resumo_leitura for matches
        if draws_with_topics:
            # 1) Fetch all contexts concurrently
            context_coros = [DrawSchemaBase.get_context_by_id(db, draw_id) for draw_id in draws_with_topics]
            contexts = await asyncio.gather(*context_coros)

            # 2) Build comparator prompts and run comparator in parallel (throttled)
            comparator_prompts = [
                prompt_comparador_template.format(context1=draw_data.context, context2=ctx)
                for ctx in contexts
            ]
            comparator_tasks = [
                _call_openai(prompt, role_comparador, 10, 0.9) for prompt in comparator_prompts
            ]
            comparator_results = await asyncio.gather(*comparator_tasks)

            # 3) For those above threshold, fetch draw details and reviews in parallel
            positive_indices = []
            similaridade_values = []
            for idx, res in enumerate(comparator_results):
                try:
                    val = float(res)
                except Exception:
                    val = 0.0
                similaridade_values.append(val)
                if val > 0.5:
                    positive_indices.append(idx)

            if positive_indices:
                # coroutines for draw details and reviews and deck/spread names
                draw_detail_coros = [DrawSchemaBase.get_draw_details_by_id(db, draws_with_topics[i]) for i in positive_indices]
                review_coros = [ReviewSchema.get_rating_and_comment_by_draw_id(db, draws_with_topics[i]) for i in positive_indices]
                draw_details = await asyncio.gather(*draw_detail_coros)
                reviews = await asyncio.gather(*review_coros)

                # Prepare resumo_leitura prompts and call OpenAI in parallel (throttled)
                resumo_prompts = []
                for d in draw_details:
                    prev_reading = d.get('reading')
                    if isinstance(prev_reading, str):
                        try:
                            prev_reading = JsonExtractor.extract_json_from_reading(prev_reading)
                        except Exception:
                            pass
                    prev_deck_name = await DeckSchema.get_deck_name_by_id(db, d.get('deck_id'))
                    prev_spread_name = await SpreadTypeSchema.get_spread_type_name_by_id(db, d.get('spread_type_id'))
                    resumo_prompts.append(
                        prompt_resumo_leitura_template.format(
                            context=d.get('context'),
                            deck_name=prev_deck_name,
                            spread_name=prev_spread_name,
                            cards=d.get('cards'),
                            reading=prev_reading,
                        )
                    )

                resumo_tasks = [_call_openai(p, role_resumo_leitura, 50, 0.9) for p in resumo_prompts]
                resumo_results = await asyncio.gather(*resumo_tasks)

                # Assemble similar_draws using collected data
                for idx_local, idx_global in enumerate(positive_indices):
                    d = draw_details[idx_local]
                    review = reviews[idx_local]
                    rating, comment = (review if review else (None, None))
                    similar_draws.append({
                        "similaridade": similaridade_values[idx_global],
                        "context": contexts[idx_global],
                        "deck_name": await DeckSchema.get_deck_name_by_id(db, d.get('deck_id')),
                        "spread_type_name": await SpreadTypeSchema.get_spread_type_name_by_id(db, d.get('spread_type_id')),
                        "cards": d.get('cards'),
                        "reading_summary": resumo_results[idx_local],
                        "rating": rating,
                        "comment": comment,
                        "is_reversed": d.get('is_reversed', []),
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
            # print(f"Reversed info: {reversed_info}")
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

        # Prompt base (do template)
        prompt_base = prompt_base_template.format(explicacao_invertidas=explicacao_invertidas)

        # Acrescenta contextos anteriores se houver
        if previous_contexts_str:
            prompt_base += (
                f"Considere também os seguintes contextos e leituras anteriores do consulente para enriquecer sua análise e trazer informações relevantes para a consulta atual:\n"
                f"{previous_contexts_str}\n\n"
            )

        # Parte final do prompt (do template)
        prompt_final = prompt_final_template.format(
            cards_names=cards_names,
            context=draw_data.context,
            user_name=user_name,
            spreadname=spreadname,
            deckname=deckname,
            reading_style_name=reading_style_name,
            reading_style_description=reading_style_description,
        )

        # Prompt ajustado completo
        prompt_ajustado = prompt_base + prompt_final

        # Role fixo (do template)
        role = readings_role


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
        
        
        


        reading = JsonExtractor.extract_json_from_reading(reading)
        confirm_service = ConfirmMissionService()

        # se for do tipo mandala astrológica, tem que confirmar a missão do usuário
        if draw_data.spread_type_id == mandala_id:  # Mandala Astrológica
            
            mission_type_id = await MissionTypeSchemaBase.get_id_by_name(db, "Fazer uma leitura do tipo Mandala Astrológica")
            await confirm_service.confirm_mission(db,  mission_type_id, user_id)
        
        id_analitico = await ReadingStyleSchema.get_id_by_name(db, "Analítico")
        
        if draw_data.reading_style == id_analitico:
            # se for do tipo analítico, tem que confirmar a missão do usuário
            
            # print("Fazer uma leitura no modo analitico")
            mission_type_id = await MissionTypeSchemaBase.get_id_by_name(db, "Fazer uma leitura no modo analítico")
            await confirm_service.confirm_mission(db,  mission_type_id, user_id)
            
        
        ordered_reading = {}
        ordered_reading["introducao"] = reading.get("introducao", "")

        cards_names = await CardSchema.get_cards_names_by_group_ids(db, draw_data.cards, keep_order=True)
        # print(f"Cards names reordered: {cards_names}")
        
        # Reordena as cartas e renomeia as chaves para carta_1, carta_2, ...
        carta_idx = 1
        for card_name in cards_names:
            # Encontrar a chave original (ex: carta_10) cujo valor corresponde ao nome da carta atual
            for key, value in reading.items():
                if key.startswith("carta_") and card_name in value:
                    ordered_reading[f"carta_{carta_idx}"] = value
                    carta_idx += 1
                    break
                            
        ordered_reading["conclusao"] = reading.get("conclusao", "")
        
        # Only extract JSON if ordered_reading is a string
        if isinstance(ordered_reading, str):
            ordered_reading = JsonExtractor.extract_json_from_reading(ordered_reading)
        
        # Converte o dicionário ordered_reading para uma string JSON antes de enviar ao banco
        import json
        ordered_reading_json = json.dumps(ordered_reading)

        draw = await DrawSchemaBase.update_draw_after_standard_reading(
            db, 
            draw_id=id_draw, 
            user_id=user_id, 
            spread_type_id=draw_data.spread_type_id,
            deck_id=draw_data.deck_id,
            cards=draw_data.cards,
            context=draw_data.context,
            status_id=status_id,
            reading=ordered_reading_json,  # Usa a string JSON aqui
            topics=list_id_topics,
            is_reversed=is_reversed,
            card_style=draw_data.card_style
        )
        
        
        return {"leitura": ordered_reading, "id": id_draw}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro ao atualizar draw: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao buscar os eventos.")
