# backend/server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from openai import OpenAI
import os
from dotenv import load_dotenv
from memory import memory_engine

load_dotenv()

app = FastAPI(title="Zeni AI Backend", description="Your AI Best Friend")

# CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Personality prompts
PERSONALITIES = {
    "friend": "You are Zeni, a casual and supportive AI best friend. You're warm, empathetic, and use emojis sometimes. Keep responses conversational and under 150 words.",
    "mentor": "You are Zeni, a professional mentor AI. You're growth-focused, wise, and give actionable advice. Be direct but encouraging.",
    "coach": "You are Zeni, a motivational coach AI. You push users toward their goals and celebrate wins. Use energetic language.",
    "bestie": "You are Zeni, a best friend AI. You're fun, personal, and talk like a close friend would. Be slightly sarcastic but loving."
}

# Request/Response Models
class ChatRequest(BaseModel):
    user_id: str
    message: str
    personality: str = "friend"

class ChatResponse(BaseModel):
    reply: str
    memories_created: int

class MemoryResponse(BaseModel):
    memories: List[Dict[str, Any]]
    count: int

# Endpoints
@app.get("/")
def root():
    return {"message": "Zeni AI Backend is running!", "status": "active"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint - Zeni responds with memory context"""
    try:
        # 1. Extract and store memories from user message
        new_memories = memory_engine.extract_memories_from_message(
            request.user_id, 
            request.message
        )
        
        # 2. Get memory context
        memory_context = memory_engine.get_context_string(request.user_id)
        
        # 3. Build system prompt
        personality_prompt = PERSONALITIES.get(request.personality, PERSONALITIES["friend"])
        system_prompt = f"""{personality_prompt}

{memory_context}

Important: Reference specific things the user has told you. Show that you remember them.
Keep responses warm and natural. Use memories naturally in conversation."""

        # 4. Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=0.8,
            max_tokens=300
        )
        
        reply = response.choices[0].message.content
        
        # 5. Store that conversation happened
        memory_engine.add_memory(
            request.user_id,
            f"User asked: '{request.message[:80]}' - Zeni responded supportively",
            "conversation",
            3
        )
        
        return ChatResponse(
            reply=reply,
            memories_created=len(new_memories)
        )
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memories/{user_id}", response_model=MemoryResponse)
async def get_memories(user_id: str, limit: int = 50):
    """Get all memories for a user"""
    memories = memory_engine.get_memories(user_id, limit)
    return MemoryResponse(memories=memories, count=len(memories))

@app.delete("/memories/{user_id}")
async def delete_memories(user_id: str):
    """Delete all memories for a user"""
    memory_engine.delete_user_memories(user_id)
    return {"message": f"Deleted all memories for user {user_id}"}

@app.post("/memory/search")
async def search_memories(user_id: str, query: str):
    """Search memories by keyword"""
    results = memory_engine.search_memories(user_id, query)
    return {"results": results, "count": len(results)}

@app.get("/health")
async def health():
    return {"status": "healthy", "memories_count": len(memory_engine.memories)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
