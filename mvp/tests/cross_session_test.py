import asyncio
import httpx
import uuid
import sys

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
USER_ID = "b40d1660-cdb3-4ed0-b0d3-2267b3d25072" # Use existing valid user

async def test_cross_session_memory():
    print(f"\n🧪 STARTING CROSS-SESSION MEMORY TEST")
    print(f"User ID: {USER_ID}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # --- SESSION A ---
        print("\n[1/3] Creating Session A...")
        res = await client.post(f"{BASE_URL}/chat/sessions", json={"title": "Session A"}, params={"user_id": USER_ID})
        if res.status_code != 201:
            print(f"❌ Failed to create Session A: {res.text}")
            return
        session_a_id = res.json()["id"]
        print(f"✅ Session A Created: {session_a_id}")
        
        print("[1.5] Telling AI my name in Session A...")
        res = await client.post(f"{BASE_URL}/chat", json={
            "message": "My name is Commander Shepard.",
            "session_id": session_a_id
        }, params={"user_id": USER_ID})
        print(f"Response A: {res.json().get('content')}")
        
        # --- SESSION B ---
        print("\n[2/3] Creating Session B (New Context)...")
        res = await client.post(f"{BASE_URL}/chat/sessions", json={"title": "Session B"}, params={"user_id": USER_ID})
        session_b_id = res.json()["id"]
        print(f"✅ Session B Created: {session_b_id}")
        
        print("[2.5] Asking for name in Session B...")
        res = await client.post(f"{BASE_URL}/chat", json={
            "message": "What is my name?",
            "session_id": session_b_id
        }, params={"user_id": USER_ID})
        
        data = res.json()
        content = data.get('content', '')
        intent = data.get('intent', 'unknown')
        
        print(f"\n📝 Response in Session B: {content}")
        print(f"🎯 Intent Detected: {intent}")
        print("-" * 50)
        
        # --- VERIFICATION ---
        if "Shepard" in content:
            print("✅ SUCCESS: AI remembered name across sessions!")
        else:
            print("❌ FAILURE: AI forgot name in new session.")

if __name__ == "__main__":
    asyncio.run(test_cross_session_memory())
