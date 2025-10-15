# /src/server.py
import json
from fastapi import FastAPI, WebSocket
from src.main_agent import app
from langchain_core.messages import HumanMessage

fastapi_app = FastAPI()

@fastapi_app.get("/")
async def root():
    return {"message": "Agent backend is running"}

@fastapi_app.websocket("/ws/chat")
async def chat_socket(ws: WebSocket):
    await ws.accept()
    conversation_history = []

    while True:
        try:
            user_msg = await ws.receive_text()
            if user_msg.lower() == "exit":
                await ws.send_text(json.dumps({"sender": "system", "text": "Goodbye!"}))
                break

            conversation_history.append(HumanMessage(content=user_msg))
            result_state = app.invoke({"messages": conversation_history})
            final_message = result_state['messages'][-1]
            conversation_history.append(final_message)

            # Ensure content is a string
            content = getattr(final_message, "content", str(final_message))
            sender = "ai"
            await ws.send_text(json.dumps({"sender": sender, "text": content}))
            print("Sent to frontend:", content)  # Debug
        except Exception as e:
            await ws.send_text(json.dumps({"sender": "system", "text": f"Error: {e}"}))
            break
