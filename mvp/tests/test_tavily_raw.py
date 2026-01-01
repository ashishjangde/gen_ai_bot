from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TAVILY_API_KEY")
if not api_key:
    print("❌ TAVILY_API_KEY not found in env")
    exit(1)

client = TavilyClient(api_key=api_key)

print("🔎 Searching Tavily...")
response = client.search(
    query="latest news about TCS",
    max_results=2,
    search_depth="basic",
    include_images=True, # Maybe icons are here?
    include_answer=False
)

print("\n--- RAW RESPONSE ITEM 0 ---")
if response.get("results"):
    print(response["results"][0])
    print("\nKeys available:", response["results"][0].keys())
else:
    print("No results found.")
