from uuid import UUID
from fastapi import Depends
from app.modules.user_service.schema.session_schema import SessionSchema, SessionListSchema
from app.modules.user_service.repositories.session_repository import SessionRepository
from app.exceptions.exceptions import ResourceNotFoundException


class SessionService:
    def __init__(self, session_repository: SessionRepository) -> None:
        self.session_repository = session_repository
    
    async def get_user_sessions(self, user_id: UUID) -> SessionListSchema:
        """Get all sessions for a user"""
        sessions = await self.session_repository.get_by_user_id(user_id)
        return SessionListSchema(
            sessions=[SessionSchema.model_validate(s) for s in sessions],
            total=len(sessions)
        )
    
    async def revoke_session(self, user_id: UUID, session_id: UUID) -> bool:
        """Revoke a specific session"""
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ResourceNotFoundException("Session not found")
        if session.user_id != user_id:
            raise ResourceNotFoundException("Session not found")
        
        await self.session_repository.delete(id=session_id, commit=True)
        return True
    
    async def revoke_all_sessions(self, user_id: UUID, current_refresh_token: str | None = None) -> bool:
        """Revoke all sessions except current one"""
        sessions = await self.session_repository.get_by_user_id(user_id)
        for session in sessions:
            if current_refresh_token and session.refresh_token == current_refresh_token:
                continue  # Skip current session
            await self.session_repository.delete(id=session.id, commit=True)
        return True


def get_session_service(
    session_repository: SessionRepository = Depends(SessionRepository),
) -> SessionService:
    return SessionService(session_repository)
