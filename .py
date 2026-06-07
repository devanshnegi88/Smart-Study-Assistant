import google.generativeai as genai

API_KEY = "Ab8RN6LzLVjBYtVeVYv_cX8TILiAylqjbEk1hzcSGvrElFnCng"

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-3.0-flash")

response = model.generate_content("Hello")

print(response.text)