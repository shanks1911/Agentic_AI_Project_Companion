# /src/server.py
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.agents.generate_plan import generate_tasks, generate_final_plan

fastapi_app = FastAPI()


@fastapi_app.get("/")
async def root():
    return {"message": "Agent backend is running"}


@fastapi_app.websocket("/ws/chat")
async def chat_socket(ws: WebSocket):
    await ws.accept()

    state = {
        "stage": "greet",
        "idea": None,
        "plan_type": None,
        "duration": None,
        "tasks": None
    }

    try:
        while True:
            try:
                msg = await ws.receive_text()
            except WebSocketDisconnect:
                print("❌ Client disconnected")
                break

            msg_lower = msg.lower().strip()

            # 1️⃣ Greeting
            if state["stage"] == "greet":
                await ws.send_text(json.dumps({
                    "sender": "ai",
                    "text": "👋 Hello! Please share your project idea."
                }))
                state["stage"] = "idea"
                continue

            # 2️⃣ Receive/refine idea
            elif state["stage"] == "idea":
                state["idea"] = msg
                await ws.send_text(json.dumps({
                    "sender": "ai",
                    "text": f"Got it! Your project idea is: '{msg}'. Would you like to refine or finalize it?"
                }))
                state["stage"] = "refine"
                continue

            elif state["stage"] == "refine":
                if "refine" in msg_lower:
                    await ws.send_text(json.dumps({
                        "sender": "ai",
                        "text": "Please enter your refined project idea."
                    }))
                    state["stage"] = "idea"
                else:  # finalize
                    await ws.send_text(json.dumps({
                        "sender": "ai",
                        "text": "Great! Do you want a Kanban plan, a Gantt plan, or both?"
                    }))
                    state["stage"] = "plan_choice"
                continue

            # 3️⃣ Choose plan type
            elif state["stage"] == "plan_choice":
                if any(word in msg_lower for word in ["kanban", "gantt", "both"]):
                    state["plan_type"] = "kanban" if "kanban" in msg_lower else "gantt" if "gantt" in msg_lower else "both"
                    await ws.send_text(json.dumps({
                        "sender": "ai",
                        "text": "⏱️ Please specify total project duration (e.g., '3 weeks', '45 days')."
                    }))
                    state["stage"] = "duration"
                else:
                    await ws.send_text(json.dumps({
                        "sender": "ai",
                        "text": "Please choose one: Kanban, Gantt, or Both."
                    }))
                continue

            # 4️⃣ Ask for duration & generate tasks preview
            elif state["stage"] == "duration":
                state["duration"] = msg
                loop = asyncio.get_running_loop()
                tasks_future = loop.run_in_executor(None, generate_tasks, state["idea"], state["duration"])
                tasks = await tasks_future
                state["tasks"] = tasks

                # Send tasks immediately for preview
                await ws.send_text(json.dumps({
                    "type": "tasks",
                    "sender": "ai",
                    "data": json.loads(tasks.model_dump_json()),
                    "text": "Here are your initial tasks. Type 'confirm' to accept or 'refine' to modify."
                }))
                state["stage"] = "confirm_tasks"
                continue

            # 5️⃣ Confirm tasks
            elif state["stage"] == "confirm_tasks":
                if "refine" in msg_lower:
                    await ws.send_text(json.dumps({
                        "sender": "ai",
                        "text": "Please provide your refined project idea or task changes."
                    }))
                    state["stage"] = "idea"
                elif "confirm" in msg_lower:
                    loop = asyncio.get_running_loop()
                    plan_future = loop.run_in_executor(
                        None,
                        generate_final_plan,
                        state["idea"],
                        state["plan_type"],
                        state["duration"],
                        state["tasks"]
                    )
                    result = await plan_future

                    # Send final plans
                    if state["plan_type"] == "both":
                        await ws.send_text(json.dumps({
                            "type": "kanban",
                            "sender": "ai",
                            "data": json.loads(result["kanban"].model_dump_json())
                        }))
                        await ws.send_text(json.dumps({
                            "type": "gantt",
                            "sender": "ai",
                            "data": json.loads(result["gantt"].model_dump_json())
                        }))
                    else:
                        await ws.send_text(json.dumps({
                            "type": state["plan_type"],
                            "sender": "ai",
                            "data": json.loads(result.model_dump_json())
                        }))

                    await ws.send_text(json.dumps({
                        "sender": "ai",
                        "text": "🎉 Your plan is ready!"
                    }))
                    state["stage"] = "done"
                else:
                    await ws.send_text(json.dumps({
                        "sender": "ai",
                        "text": "Please type 'confirm' to accept these tasks or 'refine' to modify them."
                    }))
                continue

            # 6️⃣ After plan completion
            elif state["stage"] == "done":
                if "new" in msg_lower:
                    state = {"stage": "greet", "idea": None, "plan_type": None, "duration": None, "tasks": None}
                    await ws.send_text(json.dumps({
                        "sender": "ai",
                        "text": "Let's start fresh! Please share your new project idea."
                    }))
                else:
                    await ws.send_text(json.dumps({
                        "sender": "ai",
                        "text": "If you’d like to start a new project, type 'new project'."
                    }))
                continue

    finally:
        if ws.client_state.name == "CONNECTED":
            await ws.close()
        print("🔒 WebSocket closed cleanly.")
