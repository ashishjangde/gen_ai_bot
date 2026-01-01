import asyncio
import httpx
import json
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
USER_ID = "b40d1660-cdb3-4ed0-b0d3-2267b3d25072" # Matches proof.sh
# We need a valid session. Let's create one first.

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Create a Session
        print("Creating session...")
        try:
            # We assume auth is not enforced or we use a mock user_id
            # In the API, user_id is a query param or body? 
            # In router.py: user_id: UUID, db... 
            # It seems user_id is injected via Depends? Or just passed?
            # Looking at chat.py: `request: ChatRequest, user_id: UUID`
            # Wait, `user_id` argument usually comes from a Dependency (auth).
            # If `user_id` is just a raw argument without Depends, FastAPI looks for query param.
            # Let's check `api/v1/chat.py` imports again.
            # It imports `user_id` ? No.
            # `async def send_message(..., user_id: UUID, ...)`
            # If `user_id` is not using Depends, it's a query parameter.
            # PROBABILITY: The original code likely used a dependency for current_user but the snippet showed `user_id: UUID`.
            # Let's assume it's a query param for now based on the file content unless there is an auth dependency hidden.
            # Check `auth` router usage.
            pass
        except Exception as e:
            print(f"Setup error: {e}")
            return

        # Let's assume we can just pass user_id as query param for this MVP POC environment
        # Create session
        response = await client.post(
            f"{BASE_URL}/api/v1/chat/sessions?user_id={USER_ID}",
            json={"title": "Streaming Test"}
        )
        if response.status_code != 201:
            print(f"Failed to create session: {response.text}")
            # Try listing sessions to get one
            response = await client.get(f"{BASE_URL}/api/v1/chat/sessions?user_id={USER_ID}")
            if response.status_code == 200:
                data = response.json()
                if data["sessions"]:
                    session_id = data["sessions"][0]["id"]
                    print(f"Using existing session: {session_id}")
                else:
                    print("No sessions and cannot create.")
                    return
            else:
                print("Failed to list sessions.")
                return
        else:
            session_id = response.json()["id"]
            print(f"Created session: {session_id}")

        # 2. Test Streaming Chat
        print(f"\nSending message to session {session_id}...")
        payload = {
            "session_id": session_id,
            "message": "Explain quantum computing in 2 sentences."
        }
        
        async with client.stream("POST", f"{BASE_URL}/api/v1/chat?user_id={USER_ID}", json=payload) as response:
            print(f"Status: {response.status_code}")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        print("\nStream finished.")
                    else:
                        try:
                            data = json.loads(data_str)
                            if "content" in data:
                                print(data["content"], end="", flush=True)
                            elif "usage" in data:
                                print(f"\n[Usage Report]: {data['usage']}")
                            if "error" in data:
                                print(f"\nError: {data['error']}")
                        except:
                            print(f"\nRaw line: {line}")

if __name__ == "__main__":
    asyncio.run(main())
