from pydantic import BaseModel
from sqlalchemy import select  # Import the select function
from sqlalchemy.ext.asyncio import AsyncSession  # Import AsyncSession
from sqlalchemy.exc import IntegrityError  # Import IntegrityError
from datetime import datetime  # Import datetime for timestamp fields
from app.models.review import ReviewModel


class ReviewSchemaBase(BaseModel):

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,  # Allows arbitrary types like SQLAlchemy's DateTime
        "validate_assignment": True
    }
    
    @staticmethod
    async def get_rating_and_comment_by_draw_id(
        session: AsyncSession,
        draw_id: int
    ) -> tuple[int, str] | None:
        """
        Retrieve only the rating and comment by draw ID.
        """
        query = select(ReviewModel.rating, ReviewModel.comment).where(
            ReviewModel.draw == draw_id
        )

        result = await session.execute(query)
        row = result.first()

        if row:
            return row[0], row[1]
        return None

    # se não tiver mais tem que retornar vazio
    @staticmethod
    async def get_reviews_by_user(
        session: AsyncSession,
        user_id: int,
        count: int = 1
    ) -> list['ReviewSchema']:
        """
        Retrieve reviews by a user in batches of 5.
        'count' is the batch number (1 returns the first 5, 2 returns the next 5, etc).
        """
        limit = 5
        offset = (count - 1) * limit

        try:
            query = select(ReviewModel).where(
                ReviewModel.user == user_id
            ).order_by(ReviewModel.created_at.desc()).limit(limit).offset(offset)

            result = await session.execute(query)
            reviews = result.scalars().all()

            if reviews:
                return [ReviewSchema.model_validate(review) for review in reviews]

            return []
        except Exception as e:
            print(f"Error fetching reviews by user: {e}")
            return []

    @staticmethod
    async def get_review_by_user_and_draw(
        session: AsyncSession,
        user_id: int,
        draw_id: int
    ) -> 'ReviewSchema | None':
        """
        Retrieve a review by user and draw ID.
        
        """
        query = select(ReviewModel).where(
            ReviewModel.user == user_id,
            ReviewModel.draw == draw_id
        )
        
        result = await session.execute(query)
        review = result.scalars().first()
        
        if review:
            return ReviewSchema.model_validate(review)
        
        return None
    
    
    @staticmethod
    async def create_review(
        session: AsyncSession,
        user_id: int,
        draw_id: int,
        rating: int,
        comment: str
    ) -> 'ReviewSchema':
        """
        Create a new review for a specific draw.
        
        """
        new_review = ReviewModel(
            user=user_id,
            draw=draw_id,
            rating=rating,
            comment=comment,
            created_at=datetime.now()
        )
        
        session.add(new_review)
        await session.commit()
        await session.refresh(new_review)
        
        return ReviewSchema.model_validate(new_review)
    
        
class ReviewSchema(ReviewSchemaBase):
    id: int
    user: int
    draw: int
    rating: int
    comment: str
    created_at: datetime