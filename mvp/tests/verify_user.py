import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.db.database import get_session_context
from app.models.chat_session_model import ChatSession
from app.models.chat_model import ChatMessage
from app.models.chat_source_model import ChatSource # Ensure this is imported!
from sqlalchemy import select

async def main():
    user_id = 'b40d1660-cdb3-4ed0-b0d3-2267b3d25072'
    print(f"--- Verifying User History: {user_id} ---")
    
    try:
        async with get_session_context() as db:
            # Get Sessions
            res = await db.execute(select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()))
            sessions = res.scalars().all()
            print(f'Found {len(sessions)} sessions.')
            
            if sessions:
                sid = sessions[0].id
                print(f'Latest Session ID: {sid}')
                print(f'Session Name: {sessions[0].title}')
                
                # Get Messages
                res_msgs = await db.execute(select(ChatMessage).where(ChatMessage.session_id == sid).order_by(ChatMessage.created_at))
                msgs = res_msgs.scalars().all()
                print(f'Message Count: {len(msgs)}')
                print("\nLast 10 Messages:")
                for m in msgs[-10:]:
                    content_preview = m.content[:100].replace('\n', ' ') + ('...' if len(m.content) > 100 else '')
                    print(f'[{m.role.upper()}] {content_preview}')
                    
                # Scan all user messages
                print("\nScanning ALL SESSIONS for 'name' mentions:")
                stmt = (
                    select(ChatMessage)
                    .join(ChatSession, ChatMessage.session_id == ChatSession.id)
                    .where(ChatSession.user_id == user_id)
                    .order_by(ChatMessage.created_at)
                )
                res = await db.execute(stmt)
                all_msgs = res.scalars().all()
                for m in all_msgs:
                    if "name" in m.content.lower():
                         print(f"[{m.session.title}] [{m.role}] {m.content}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
