from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.topic import TopicModel
from app.basic.topic import topics
from sqlalchemy.future import select

class TopicSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = (
            True  # Allows arbitrary types like SQLAlchemy's DateTime
        )
        validate_assignment = True
    
    
    @staticmethod
    async def get_topic_names_by_id(
        session: AsyncSession, topic_id: int | list[int]
    ) -> str | list[str] | None:
        """
        Returns the topic name by its ID or a list of topic names by their IDs.
        """
        if isinstance(topic_id, list):
            if not topic_id:
                return []
            result = await session.execute(
                select(TopicModel.name).where(TopicModel.id.in_(topic_id))
            )
            return [row[0] for row in result.fetchall()]
        else:
            result = await session.execute(
                select(TopicModel.name).where(TopicModel.id == topic_id)
            )
            row = result.first()
            return row[0] if row else None
    
    @staticmethod
    async def get_all_topics_ids_by_list_names(
        session: AsyncSession, names: list[str]
    ) -> list[int]:
        """
        Returns a list of topic IDs based on the provided list of names.
        """
        result = await session.execute(
            select(TopicModel.id).where(TopicModel.name.in_(names))
        )
        return [row[0] for row in result.fetchall()]
    
    @staticmethod
    async def get_all_topics_names(session: AsyncSession) -> list[str]:
        """
        Returns a list of all topic names from the database.
        """
        result = await session.execute(select(TopicModel.name))
        return [row[0] for row in result.fetchall()]
    
    @staticmethod
    async def sync_topics(session: AsyncSession):
        """
        Syncs the topics with the database. Checks if a topic exists, and if not, adds it.
        """

        for topic in topics:
            existing_topic = await session.execute(
                select(TopicModel).where(TopicModel.id == topic['id'])
            )
            if not existing_topic.scalars().first():
                topic_model = TopicModel(**topic)
                session.add(topic_model)
        await session.commit()

class TopicSchema(TopicSchemaBase):
    """
    Schema for Topic.
    """
    id: int
    name: str
    description: str | None = None
