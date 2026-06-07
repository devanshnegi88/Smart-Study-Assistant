import google.genai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key="GOOGLE_API_KEY")
print("Key exists:", bool(os.getenv("GOOGLE_API_KEY")))
print("Key value:", os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")
response = model.generate_content("Say hello")

print(response.text)