import asyncio
import logging
import uuid
from mvp.app.services.chat_service import ChatService
from mvp.app.services.memory_service import get_memory_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("🧪 PROOF OF CONCEPT: Background Summarization")
    print("------------------------------------------")
    
    # 1. Setup Services
    service = ChatService()
    await service.connect()
    
    memory = await get_memory_service()
    
    # Mock IDs
    user_id = "summary_test_user"
    session_id = str(uuid.uuid4())
    print(f"Created Session: {session_id}")
    
    try:
        # 2. Populate History (simulate 12 messages)
        print("Populating 12 messages...")
        for i in range(12):
            await memory.add_stm(session_id, "user", f"This is message number {i}. I am talking about quantum computing.")
            await memory.add_stm(session_id, "assistant", f"Acknowledged message {i}.")
            
        # 3. Trigger Background Persistence (which triggers summarization)
        print("Triggering background save (THRESHOLD=10)...")
        await service.save_session_background(
            user_id=user_id,
            session_id=session_id,
            user_message="Trigger msg",
            ai_response="Trigger response"
        )
        
        # 4. Check for Summary
        print("Checking summary storage...")
        # Give it a second as it calls the LLM
        await asyncio.sleep(3) 
        
        summary = await memory.get_summary(session_id)
        
        if summary:
            print(f"✅ SUCCESS: Summary generated!")
            print(f"📝 Summary Content: {summary}")
        else:
            print("❌ FAILURE: No summary found.")
            
    finally:
        await service.close()
        
if __name__ == "__main__":
    asyncio.run(main())
