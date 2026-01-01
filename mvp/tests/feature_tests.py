import asyncio
import httpx
import time
import json
import uuid

# Use random IDs to avoid conflicts
USER_ID = "b40d1660-cdb3-4ed0-b0d3-2267b3d25072" # Use the specific user user requested? Or test user?
# The user asked to find session for specific user.
# But for testing FEATURES, I should use a test user to avoid polluting real user history?
# "test every aspect ... we are build".
# I'll use a TEST user for the full run to guarantee clean state.
USER_ID = "b40d1660-cdb3-4ed0-b0d3-2267b3d25072"
SESSION_ID = str(uuid.uuid4())

# Session Setup Required? 
# The API checks if session exists.
# @router.post("") verify session exists.
# So I must CREATE session first.

BASE_URL = "http://localhost:8000/api/v1"

async def test_session():
    print(f"\n🚀 STARTING FULL SYSTEM TEST")
    print(f"User ID: {USER_ID}")
    print(f"Session ID: {SESSION_ID}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # 0. Create Session
        print("\n[0/5] Creating Session...")
        res = await client.post(f"{BASE_URL}/chat/sessions", json={
            "title": "Automated Feature Test"
        }, params={"user_id": USER_ID})
        
        if res.status_code != 201:
            print(f"ERROR Creating Session: {res.status_code} - {res.text}")
            return
            
        session_data = res.json()
        real_session_id = session_data["id"]
        print(f"✅ Session Created: {real_session_id}")
        
        # 1. Test Memory Storage (Fact)
        print("\n[1/5] Testing Memory Storage...")
        res = await client.post(f"{BASE_URL}/chat", json={
            "message": "My name is Captain Price and I like dark mode.",
            "session_id": real_session_id
        }, params={"user_id": USER_ID})
        
        if res.status_code != 200:
            print(f"ERROR: {res.status_code} - {res.text}")
        else:
            print(f"Response: {res.json().get('content', 'No Content')}")
        
        # 2. Test Web Search
        print("\n[2/5] Testing Web Search...")
        res = await client.post(f"{BASE_URL}/chat", json={
            "message": "Who is currently the CEO of OpenAI?",
            "session_id": real_session_id
        }, params={"user_id": USER_ID})
        
        if res.status_code == 200:
            data = res.json()
            print(f"Response: {data['content'][:100]}...")
            sources = data.get("sources", [])
            print(f"Sources Found: {len(sources)}")
            if any(s['type'] == 'web' for s in sources):
                print("✅ Web Source Verified")
            else:
                print("❌ Web Source Missing (Check Router/Tavily)")
        else:
            print(f"ERROR: {res.status_code}")

        # 3. Test Finance Tool
        print("\n[3/5] Testing Finance Tool...")
        res = await client.post(f"{BASE_URL}/chat", json={
            "message": "What is the stock price of Apple?",
            "session_id": real_session_id
        }, params={"user_id": USER_ID})
        
        if res.status_code == 200:
            data = res.json()
            print(f"Response: {data['content'][:100]}...")
            sources = data.get("sources", [])
            if any(s['type'] == 'finance' for s in sources):
                print("✅ Finance Source Verified")
            else:
                print("❌ Finance Source Missing (Check Router/YFinance)")
        else:
             print(f"ERROR: {res.status_code}")

        # 4. Fill Context Window (Force Sliding Window)
        print("\n[4/5] Filling Context Window (6 dummy messages to clear STM)...")
        for i in range(6):
            await client.post(f"{BASE_URL}/chat", json={
                "message": f"Just sending dummy message {i} to push old context out.",
                "session_id": real_session_id
            }, params={"user_id": USER_ID})
            print(".", end="", flush=True)
        print(" Done.")

        # 5. Test Memory Recall (Router + DB Search)
        print("\n[5/5] Testing Deep Memory Recall (Did it forget me?)...")
        res = await client.post(f"{BASE_URL}/chat", json={
            "message": "What is my name?",
            "session_id": real_session_id
        }, params={"user_id": USER_ID})
        
        if res.status_code == 200:
            data = res.json()
            content = data['content']
            intent = data.get('intent', 'unknown')
            print(f"\nResponse: {content}")
            print(f"Intent Detected: {intent}")
            
            if "Price" in content or "Captain" in content:
                print("✅ MEMORY RECALL SUCCESSFUL! (Retrieved from Deep History)")
            else:
                print("❌ MEMORY RECALL FAILED (Context lost)")
        else:
             print(f"ERROR: {res.status_code}")

if __name__ == "__main__":
    asyncio.run(test_session())
