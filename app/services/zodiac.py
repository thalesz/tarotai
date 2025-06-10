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
from app.services.planet import PlanetSignCalculator  # Add this import
from app.services.openai import OpenAIService
from app.services.extract import JsonExtractor


class DailyZodiacService:
    def __init__(self):
        # Inicializa o dicionário com as posições atuais dos planetas uma única vez
        self.current_positions_dict = None

    async def _initialize_planet_positions(self, db: AsyncSession):
        if self.current_positions_dict is None:
            planets = await PlanetSchemaBase.get_all_planet_ids_and_names(session=db)
            now_date = datetime.now().strftime("%Y-%m-%d")
            now_time = datetime.now().strftime("%H:%M")
            positions = {}
            for planet in planets:
                planet_name = planet["name"]
                current_position = await PlanetSignCalculator().planet_sign(
                    birth_date=now_date,
                    birth_time=now_time,
                    birth_place="Earth",
                    planet_name=planet_name,
                )
                positions[planet_name] = (
                    current_position[1]
                    if current_position
                    and isinstance(current_position, (list, tuple))
                    and len(current_position) > 1
                    else current_position
                    if current_position
                    else None
                )
            self.current_positions_dict = positions

    async def create_daily_zodiac_for_user(
        self,
        db: AsyncSession,
        user_id: int
    ):
        """
        Create a daily zodiac for a specific user.
        """
        try:
            # Inicializa o dicionário das posições dos planetas (se ainda não estiver inicializado)
            await self._initialize_planet_positions(db)

            planets = await PlanetSchemaBase.get_all_planet_ids_and_names(session=db)
            planet_ids = [planet["id"] for planet in planets]

            signs = []
            # print(f"Planets for user {user_id}: {planets}")  # Debugging line to check the planets
            for id in planet_ids:
                # print(f"Processing planet ID: {id}")  # Debugging line to check the current planet ID
                zodiac_sign = await PersonalSignSchema.get_sign_by_planet_id(
                    session=db, user_id=user_id, planet_id=id
                )
                # print(f"Zodiac sign for planet ID {id}: {zodiac_sign}")  # Debugging line to check the zodiac sign
                zodiac_name = None
                zodiac_degree = None
                if zodiac_sign and isinstance(zodiac_sign, list) and len(zodiac_sign) > 0:
                    zodiac_sign_data = zodiac_sign[0]
                    zodiac_name = await ZodiacSchemaBase.get_zodiac_name_by_id(db, zodiac_sign_data["zodiac_sign"])
                    zodiac_degree = zodiac_sign_data.get("degree")
                # print(f"Zodiac name for planet ID {id}: {zodiac_name}")  # Debugging line to check the zodiac name
                planet_name = next((planet["name"] for planet in planets if planet["id"] == id), None)
                # print(f"Planet name for ID {id}: {planet_name}")  # Debugging line to check the planet name

                signs.append({
                    "planet_name": planet_name,
                    "zodiac_sign": zodiac_name,
                    "degree": zodiac_degree,
                    # "current_position": self.current_positions_dict.get(planet_name)
                })

            # print(f"Signs for user {user_id}: {signs}")  # Debugging line to check the signs
            prompt = (
                    f"Crie uma leitura astrológica diária **única e altamente personalizada** para o usuário de ID {user_id}, "
                    f"com base em sua configuração natal planetária e nas **posições astrológicas atuais** dos planetas. "
                    f"Dados astrológicos do usuário: {signs}. "
                    "alem disso em current position temos as posições atuais dos planetas: "
                    f"{self.current_positions_dict}. "

                    "Utilize princípios de astrologia moderna e tradicional para analisar como os trânsitos atuais influenciam "
                    "os signos natais do usuário. Faça uma leitura precisa, criativa e com profundidade simbólica, incluindo conselhos práticos e espirituais. "
                    "A mensagem deve soar como vinda de um astrólogo experiente que compreende a complexidade e a individualidade de cada mapa astral. "

                    "A resposta deve estar **em formato JSON**, com as seguintes chaves obrigatórias:\n"
                    "- 'diario': visão geral do dia\n"
                    "- 'amor': insights e conselhos sobre relacionamentos e emoções\n"
                    "- 'trabalho': tendências e desafios na área profissional\n"
                    "- 'saude': observações sobre bem-estar físico e mental\n"
                    "- 'financas': panorama financeiro\n"
                    "- 'espiritualidade': reflexões internas e conexões com o eu superior\n"
                    "- 'conselho': mensagem final ou mantra do dia\n\n"

                    "Cada campo deve conter um parágrafo claro, informativo e personalizado. Evite repetições. "
                    "Inspire-se em fontes confiáveis de astrologia, como Liz Greene, Stephen Arroyo e Dane Rudhyar. "
                    "Seja criativo e profundo, entregando uma mensagem que pareça feita **exclusivamente** para esse usuário."
                )
            
            role = (
                "Você é um astrólogo profissional renomado, com mais de 20 anos de experiência em astrologia moderna, psicológica e esotérica. "
                "Seu conhecimento abrange tanto a leitura de mapas natais quanto a interpretação de trânsitos e progressões. "
                "Você tem a habilidade de traduzir complexos padrões astrológicos em orientações práticas e inspiradoras, "
                "com uma linguagem clara, acolhedora e profunda. Seu objetivo é oferecer ao usuário uma orientação única, "
                "baseada em seu perfil astrológico individual, com foco em autoconhecimento, crescimento pessoal e tomadas de decisão conscientes. "
                "Você escreve com empatia, precisão simbólica e autoridade, como um verdadeiro guia espiritual moderno."
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

            # agora salva ne ... 
            DailyZodiac= await DailyZodiacSchemaBase.create_daily_zodiac(
                db=db,
                user_id=user_id,
                reading=response,
                status=await StatusSchemaBase.get_id_by_name(db=db, name="active")
            )
            
            
            
            print(f"Daily zodiac created for user {user_id}: {DailyZodiac}")
            
            
            # salvar a leitura do signo (implementação omitida)

        except Exception as e:
            print(f"Error creating daily zodiac for user {user_id}: {e}")

    # Esta função será chamada uma vez por dia

    async def create_daily_zodiac_for_all_users(self):
        """
        Create a daily zodiac for all active users.
        """
        async with Session() as session:
            db: AsyncSession = session

            print("Creating daily zodiacs for all users...")

            id_active = await StatusSchemaBase.get_id_by_name(db=session, name="active")
            id_standard = await UserTypeSchemaBase.get_id_by_name(session=session, name="STANDARD")
            id_premium = await UserTypeSchemaBase.get_id_by_name(session=session, name="PREMIUM")
            id_admin = await UserTypeSchemaBase.get_id_by_name(session=session, name="ADM")

            active_users = await UserSchemaBase.get_all_id_by_status(
                db=db, status_id=id_active, user_type=[id_standard, id_premium, id_admin], require_birth_info=True
            )

            if not active_users:
                print("No active users found.")
                return

            print(f"Active users: {active_users}")
            for user in active_users:
                # verificar se ele tem informações de nascimento
                await self.create_daily_zodiac_for_user(
                    db=db, user_id=user
                )
                await DailyZodiacSchemaBase.delete_old_entries(session=db, user_id=user, count=7)

            
            # agora por ultimo vamos fazer uma funcão que so mantem os 7 ultimos dias de leitura salvos
