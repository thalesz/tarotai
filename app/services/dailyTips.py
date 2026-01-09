from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.postgresdatabase import Session
from app.schemas.status import StatusSchemaBase
from app.schemas.user_type import UserTypeSchemaBase, UserTypeSchema
from app.schemas.user import UserSchemaBase
from app.schemas.daily_tips import DailyTipsSchemaBase
from app.services.openai import OpenAIService
from app.services.extract import JsonExtractor
from app.prompts.daily_tips import build_daily_tips_prompt, build_daily_tips_role
import asyncio


class DailyTipsService:
    def __init__(self):
        # retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.backoff = 2  # exponential backoff multiplier

    async def create_daily_tips_for_user(
        self,
        db: AsyncSession,
        user_id: int
    ):
        """
        Create daily tips for a specific user.
        """
        try:
            print(f"Creating daily tips for user {user_id}...")
            
            # Build the prompt
            prompt = build_daily_tips_prompt()
            role = build_daily_tips_role()

            # Get user type and max tokens
            user_type_id = await UserSchemaBase.get_user_type_by_id(db, user_id)
            max_tokens = int(await UserTypeSchema.get_token_amount_by_id(db, user_type_id))

            # Cap the requested tokens to avoid exceeding model limits and high costs
            # Use a conservative multiplier for tips (they're shorter than zodiac readings)
            requested_max_tokens = min(max_tokens * 5, 2000)

            # Generate tips using OpenAI
            openai_service = OpenAIService()
            response = await openai_service.gerar_texto(
                prompt_ajustado=prompt,
                role=role,
                max_tokens=requested_max_tokens,
                temperature=0.8,
            )

            print(f"Response from OpenAI for user {user_id}: {response[:100]}...")
            
            # Extract JSON from response
            extracted_text = JsonExtractor.extract_json_from_reading(response)
            print(f"Extracted text: {extracted_text}")

            # Save to database
            status_id = await StatusSchemaBase.get_id_by_name(db=db, name="active")
            daily_tips = await DailyTipsSchemaBase.create_daily_tips(
                db=db,
                user_id=user_id,
                reading=response,
                status=status_id
            )
            
            print(f"Daily tips created for user {user_id}: {daily_tips.id}")
            
            return daily_tips

        except Exception as e:
            print(f"Error creating daily tips for user {user_id}: {e}")
            raise

    async def create_daily_tips_for_all_users(self):
        """
        Create daily tips for all active users.
        """
        async with Session() as session:
            db: AsyncSession = session

            print("Creating daily tips for all users...")

            # Get active status and user types
            id_active = await StatusSchemaBase.get_id_by_name(db=session, name="active")
            id_standard = await UserTypeSchemaBase.get_id_by_name(session=session, name="STANDARD")
            id_premium = await UserTypeSchemaBase.get_id_by_name(session=session, name="PREMIUM")
            id_admin = await UserTypeSchemaBase.get_id_by_name(session=session, name="ADM")

            # Get all active users
            active_users = await UserSchemaBase.get_all_id_by_status(
                db=db, 
                status_id=id_active, 
                user_type=[id_standard, id_premium, id_admin],
                require_birth_info=False  # Daily tips don't require birth info
            )

            if not active_users:
                print("No active users found.")
                return {"processed": 0, "total": 0, "errors": []}

            print(f"Active users: {len(active_users)}")
            errors = []
            processed = 0

            for user in active_users:
                # Retry loop for creating daily tips per user
                last_exc = None
                for attempt in range(self.max_retries):
                    try:
                        await self.create_daily_tips_for_user(db=db, user_id=user)
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

                # Retry deleting old entries (best-effort, keep only last 7 days)
                if last_exc is None:  # Only try to delete if creation was successful
                    for attempt in range(max(1, self.max_retries - 1)):
                        try:
                            await DailyTipsSchemaBase.delete_old_entries(session=db, user_id=user, count=7)
                            break
                        except Exception as e:
                            wait = self.retry_delay * (self.backoff ** attempt)
                            print(f"Attempt {attempt+1} to delete old entries failed for user {user}: {e}. Retrying in {wait}s...")
                            if attempt < max(1, self.max_retries - 1) - 1:
                                await asyncio.sleep(wait)
                            else:
                                print(f"Delete attempts failed for user {user}: {e}")
                                errors.append({"user": user, "error_delete": str(e)})

            print(f"Processed {processed} of {len(active_users)} users. Errors: {len(errors)}")
            return {"processed": processed, "total": len(active_users), "errors": errors}
