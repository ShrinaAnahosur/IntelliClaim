import os
import google.generativeai as genai
from dotenv import load_dotenv 
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

clean_instruction = """
You are an AI assistant for an AI-powered car damage assessment and insurance claims system called IntelliClaim. 
Your role is to help users with:

- Car damage assessment: Guide users on how to upload images, describe damages, and get AI-based repair cost estimates.
- Insurance claim process: Explain the steps required to file a claim, required documents, and expected processing time.
- Policy information: Answer general questions about car insurance policies, coverage options, and common terms.
- Damage severity estimation: Provide insights on minor, moderate, and severe damages based on AI predictions.
- Customer support: Assist with frequently asked questions, troubleshooting, and directing users to human agents if needed.

Guidelines:
- Be concise, clear, and professional in your responses.
- Provide step-by-step guidance when explaining processes.
- If unsure, redirect users to official support rather than making assumptions.
- Ensure responses are friendly and informative, improving user experience.

Limitations:
- You do not make final claim decisions—only assist with AI predictions.
- If users need official verification, suggest contacting their insurance provider.
- You do not process payments or request sensitive personal data.
""".encode("utf-8").decode("utf-8")  # Ensuring proper encoding

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b",
    generation_config=generation_config,
    system_instruction=clean_instruction
)

history = []

print("Bot: Hello there! How may I assist you?")

while True:
    user_input = input("You: ")

    chat_session = model.start_chat(
    history=history
    )

    response = chat_session.send_message(user_input)

    model_response = response.text
    print(f'Bot: {model_response}')
    print()

    history.append({"role": "user", "parts": [user_input]})
    history.append({"role": "model", "parts": [model_response]})