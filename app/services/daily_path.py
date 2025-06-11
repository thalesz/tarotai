from app.schemas.status import StatusSchemaBase  # Adjust the import path as needed
from app.schemas.user_type import UserTypeSchemaBase  # Adjust the import path as needed
from app.schemas.user import UserSchemaBase  # Adjust the import path as needed
from app.schemas.subscription import SubscriptionSchemaBase  # Adjust the import path as needed
from datetime import datetime
from app.core.postgresdatabase import Session
from sqlalchemy.ext.asyncio import AsyncSession
from collections import Counter
from app.schemas.draw import DrawCreate  # Adjust the import path as needed
from app.schemas.transaction import TransactionSchemaBase  # Adjust the import path as needed
from app.schemas.planet import PlanetSchemaBase  # Adjust the import path as needed
from app.schemas.user_type import UserTypeSchema  # Add this import
from app.services.descricao_astrologica import DescricaoAstrologicaService  # Add this import
from app.schemas.personal_sign import PersonalSignSchema  # Add this import
from app.schemas.zodiac import ZodiacSchemaBase  # Add this import
from app.schemas.daily_zodiac import DailyZodiacSchemaBase  # Add this import
from app.schemas.daily_path import DailyPathSchemaBase  # Add this import
from app.services.planet import PlanetSignCalculator  # Add this import
from app.services.openai import OpenAIService
from app.services.extract import JsonExtractor
import random


class DailyPathService:

    async def create_daily_path_for_user(
        self,
        db: AsyncSession,
        user_id: int
    ):
        """
        Create a daily path for a specific user.
        """
        try:
            print(f"Creating daily path for user {user_id}...")
            
            user_name = await UserSchemaBase.get_user_name_by_id(db, user_id)
            
            birth_info = await UserSchemaBase.get_birth_info_by_id(db, user_id)
            # Inicializa o dicionário das posições dos planetas (se ainda não estiver inicializado)

            # print(f"Signs for user {user_id}: {signs}")  # Debugging line to check the signs
            # Gera um seed aleatório para garantir variedade máxima
            seed = f"{user_id}-{datetime.now().strftime('%Y-%m-%d')}-{random.randint(0, 1_000_000)}"
            # Para garantir ainda mais originalidade, vamos adicionar elementos únicos ao prompt:
            # - Um número aleatório exclusivo para o usuário e o dia
            # - Uma palavra-chave gerada a partir do nome do usuário e do seed
            # - Um desafio do dia, criado a partir de uma lista embaralhada

            unique_number = random.randint(1000, 9999)
            keyword = ''.join(random.sample(user_name.lower().replace(" ", ""), min(5, len(user_name))))
            desafios = [
                "Pratique o silêncio por 5 minutos.",
                "Escreva uma carta para si mesmo.",
                "Observe um detalhe novo ao seu redor.",
                "Ofereça um elogio genuíno a alguém.",
                "Desenhe um símbolo que represente seu dia.",
                "Medite sobre uma cor específica.",
                "Caminhe descalço por alguns minutos.",
                "Anote um sonho ou desejo secreto.",
                "Experimente um aroma diferente hoje.",
                "Escolha uma música e dance livremente."
            ]
            random.shuffle(desafios)
            desafio_do_dia = desafios[0]

            prompt = (
                f"Crie uma leitura diária única, altamente personalizada e surpreendente para o usuário de ID {user_name}.\n"
                f"Data atual: {datetime.now().strftime('%Y-%m-%d')}.\n"
                f"Seed de aleatoriedade: {seed}\n"
                f"Número exclusivo do dia: {unique_number}\n"
                f"Palavra-chave secreta: {keyword}\n"
                f"Desafio do dia: {desafio_do_dia}\n"
                f"Informações do usuário:\n"
                f"- Data de nascimento: {birth_info['birth_date']}\n"
                f"- Horário de nascimento: {birth_info['birth_time']}\n"
                f"- Local de nascimento: {birth_info['birth_place']}\n\n"

                "Com base nessas informações, aplique um conjunto integrado de práticas místicas para criar uma leitura profunda, simbólica e absolutamente original, incluindo:\n"
                "- Numerologia pessoal e do dia (análise dos números e suas vibrações)\n"
                "- Arquétipos do tarot, escolhendo cartas que ressoem com a energia do usuário\n"
                "- Simbolismo das runas e seus significados\n"
                "- Energia dos chakras, indicando quais centros energéticos estão mais ativos ou necessitam atenção\n"
                "- Ciclos naturais, como fases da lua e elementos da natureza (terra, água, fogo, ar)\n"
                "- Práticas de mindfulness e intuição para ação fluida\n"
                "- Incorpore a palavra-chave e o desafio do dia de forma criativa na leitura\n\n"

                "A leitura deve ser o mais aleatória, criativa e imprevisível possível, evitando repetições e garantindo que cada usuário receba uma mensagem diferente, mesmo em dias consecutivos ou entre usuários distintos. Use o seed, o número exclusivo, a palavra-chave e o desafio do dia para inspirar variações inesperadas. Exemplo: use-os para fazer suas escolhas do que retornar , exemplo seed 4, voce retornaa o que seria a sua quarta escolha por resposta, use todas as variaveis\n\n"
  
                "A leitura deve conter os seguintes tópicos, cada um com um parágrafo claro, profundo, poético e inspirador:\n"
                "- 'mensagem_do_dia': uma frase motivacional ou reflexão simbólica\n"
                "- 'energia': descrição da energia ou vibração que o usuário carrega hoje, baseada nas práticas acima\n"
                "- 'cor_do_dia': uma cor simbólica que protege e equilibra emocionalmente\n"
                "- 'numeros_da_sorte': números que atuam como sinais e lembretes, com suas interpretações\n"
                "- 'simbolo': um símbolo místico ou arquétipo (runa, carta de tarot, chakra) que representa a conexão interna, seja o mais original e aleatório possível\n"
                "- 'som_invisivel': uma metáfora sonora ou sensação que traduz a energia do dia\n"
                "- 'intuicao': um conselho para confiar na intuição e agir com consciência plena\n"
                "- 'azar_do_dia': palavras, atitudes ou objetos a evitar para não atrair energias negativas\n"
                "- 'anotacao_do_universo': uma mensagem final que encoraje a continuar o caminho com fé e coragem\n\n"

                "IMPORTANTE: Retorne a leitura SOMENTE no seguinte formato JSON, dentro de um bloco markdown:\n"
                "```json\n"
                "{\n"
                '  "mensagem_do_dia": "...",\n'
                '  "energia": "...",\n'
                '  "cor_do_dia": "...",\n'
                '  "numeros_da_sorte": ["...", "..."],\n'
                '  "simbolo": "...",\n'
                '  "som_invisivel": "...",\n'
                '  "intuicao": "...",\n'
                '  "azar_do_dia": "...",\n'
                '  "anotacao_do_universo": "..."\n'
                "}\n"
                "```\n"
                "Não inclua nenhuma explicação antes ou depois do bloco JSON. Apenas o bloco JSON, para facilitar a extração automática."
            )


            
            role = (
                "Você é um guia espiritual experiente, que oferece leituras diárias profundas e personalizadas, "
                "com foco em autoconhecimento, crescimento interior e orientação prática para o dia a dia. "
                "Sua linguagem é poética, acolhedora e simbólica, capaz de traduzir sensações sutis em palavras claras e inspiradoras. "
                "Você evita qualquer menção a signos, astrologia ou previsões genéricas, criando uma mensagem única para cada pessoa, "
                "focando em vibrações, símbolos e intuições que ajudam o usuário a encontrar clareza e confiança."
            )


            
            user_type_id = await UserSchemaBase.get_user_type_by_id(db, user_id)
            max_tokens = int(await UserTypeSchema.get_token_amount_by_id(db, user_type_id))
            
            openai_service = OpenAIService()
            response = await openai_service.gerar_texto(
                prompt_ajustado=prompt,
                role=role,
                max_tokens=max_tokens*10,
                temperature=0.9
            )
            # print(f"Response from OpenAI: {response}")  # Debugging line to check the response
            
            extracted_text = JsonExtractor.extract_json_from_reading(response)
            print(f"Extracted text: {extracted_text}")  # Debugging line to check the extracted text

            # agora salva ne... 
            DailyPath= await DailyPathSchemaBase.create_daily_path(
                db=db,
                user_id=user_id,
                reading=response,
                status=await StatusSchemaBase.get_id_by_name(db=db, name="active")
            )
            
            print(f"Daily path created for user {user_id}: {DailyPath}")

            # salvar a leitura do signo (implementação omitida)

        except Exception as e:
            print(f"Error creating daily zodiac for user {user_id}: {e}")

    # Esta função será chamada uma vez por dia

    async def create_daily_path_for_all_users(self):
        """
        Create a daily path for all active users.
        """
        async with Session() as session:
            db: AsyncSession = session

            print("Creating daily zodiacs for all users...")

            id_active = await StatusSchemaBase.get_id_by_name(db=session, name="active")
            id_standard = await UserTypeSchemaBase.get_id_by_name(session=session, name="STANDARD")
            id_premium = await UserTypeSchemaBase.get_id_by_name(session=session, name="PREMIUM")
            id_admin = await UserTypeSchemaBase.get_id_by_name(session=session, name="ADM")

            active_users = await UserSchemaBase.get_all_id_by_status(
                db=db, status_id=id_active, user_type=[id_standard, id_premium, id_admin]
            )

            if not active_users:
                print("No active users found.")
                return

            print(f"Active users: {active_users}")
            for user in active_users:
                # verificar se ele tem informações de nascimento
                await self.create_daily_path_for_user(
                    db=db, user_id=user
                )
                await DailyPathSchemaBase.delete_old_entries(session=db, user_id=user, count=1)

            
            # agora por ultimo vamos fazer uma funcão que so mantem os 7 ultimos dias de leitura salvos
