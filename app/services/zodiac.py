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
from app.prompts.daily_zodiac import build_daily_zodiac_prompt, build_daily_zodiac_role
import asyncio


class DailyZodiacService:
    def __init__(self):
        # Inicializa o dicionário com as posições atuais dos planetas uma única vez
        self.current_positions_dict = None
        # retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.backoff = 2  # exponential backoff multiplier
        
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
            print(f"Creating daily zodiac for user {user_id}...")
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
            prompt = build_daily_zodiac_prompt(user_id=user_id, signs=signs, current_positions=self.current_positions_dict)
            
            role = build_daily_zodiac_role()


            
            user_type_id = await UserSchemaBase.get_user_type_by_id(db, user_id)
            max_tokens = int(await UserTypeSchema.get_token_amount_by_id(db, user_type_id))

            # cap the requested tokens to avoid exceeding model limits and high costs
            # use a conservative multiplier and an absolute cap
            requested_max_tokens = min(max_tokens * 15, 7000)

            openai_service = OpenAIService()
            response = await openai_service.gerar_texto(
                prompt_ajustado=prompt,
                role=role,
                max_tokens=requested_max_tokens,
                temperature=0.9,
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
            raise

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
            errors = []
            processed = 0
            for user in active_users:
                # retry loop for creating daily zodiac per user
                last_exc = None
                for attempt in range(self.max_retries):
                    try:
                        await self.create_daily_zodiac_for_user(db=db, user_id=user)
                        processed += 1
                        last_exc = None
                        break
                    except Exception as e:
                        last_exc = e
                        wait = self.retry_delay * (self.backoff ** attempt)
                        print(f"Attempt {attempt+1} failed for user {user}: {e}. Retrying in {wait}s...")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(wait)
                        else:
                            print(f"All attempts failed for user {user}: {e}")
                            errors.append({"user": user, "error": str(e)})

                # retry deleting old entries (best-effort)
                last_del_exc = None
                for attempt in range(max(1, self.max_retries - 1)):
                    try:
                        await DailyZodiacSchemaBase.delete_old_entries(session=db, user_id=user, count=7)
                        last_del_exc = None
                        break
                    except Exception as e:
                        last_del_exc = e
                        wait = self.retry_delay * (self.backoff ** attempt)
                        print(f"Attempt {attempt+1} to delete old entries failed for user {user}: {e}. Retrying in {wait}s...")
                        if attempt < max(1, self.max_retries - 1) - 1:
                            await asyncio.sleep(wait)
                        else:
                            print(f"Delete attempts failed for user {user}: {e}")
                            errors.append({"user": user, "error_delete": str(e)})

            print(f"Processed {processed} of {len(active_users)} users. Errors: {errors}")
            return {"processed": processed, "total": len(active_users), "errors": errors}

            # agora por ultimo vamos fazer uma funcão que so mantem os 7 ultimos dias de leitura salvos
