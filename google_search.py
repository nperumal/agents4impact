from google import genai
from google.genai import types
from config import Config

client = genai.Client(api_key=Config.GOOGLE_API_KEY)

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="List the events near San Ramon, CA this weekend.",
    config=config,
)

print(response.text)