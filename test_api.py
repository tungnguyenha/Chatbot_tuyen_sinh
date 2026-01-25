import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

print(f"✅ API Key found: {api_key[:10]}...{api_key[-5:]}")
print(f"   Length: {len(api_key)} characters")

genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel("gemini-flash-latest")

    print("\n🧪 Testing Gemini API...")
    response = model.generate_content("Say hello by Vietnamese.")
    print("✅ API works!")
    print(response.text)

except Exception as e:
    print("❌ API test failed:", e)


# import google.generativeai as genai
# import os
# from dotenv import load_dotenv
# import google.generativeai as genai

# load_dotenv()
# api_key = os.getenv("GOOGLE_API_KEY")
# genai.configure(api_key=api_key)

# print("Available models:")
# for m in genai.list_models():
#     if 'generateContent' in m.supported_generation_methods:
#         print(f"  - {m.name}")