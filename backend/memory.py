# backend/memory.py
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import hashlib

class ZeniMemory:
    def __init__(self):
        self.db_path = "database.json"
        self.load()
    
    def load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                self.memories = data.get('memories', [])
                self.users = data.get('users', {})
        else:
            self.memories = []
            self.users = {}
        self.save()
    
    def save(self):
        with open(self.db_path, 'w') as f:
            json.dump({
                'memories': self.memories[-1000:],  # Keep last 1000
                'users': self.users
            }, f, indent=2)
    
    def add_memory(self, user_id: str, content: str, category: str = "general", importance: int = 5):
        memory = {
            "id": hashlib.md5(f"{user_id}{datetime.now().isoformat()}{content}".encode()).hexdigest(),
            "user_id": user_id,
            "content": content,
            "category": category,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        self.memories.append(memory)
        self.save()
        return memory
    
    def get_memories(self, user_id: str, limit: int = 20) -> List[Dict]:
        user_memories = [m for m in self.memories if m['user_id'] == user_id]
        # Sort by importance and recency
        user_memories.sort(key=lambda x: (x['importance'], x['timestamp']), reverse=True)
        return user_memories[:limit]
    
    def search_memories(self, user_id: str, query: str) -> List[Dict]:
        user_memories = [m for m in self.memories if m['user_id'] == user_id]
        query_lower = query.lower()
        results = []
        for m in user_memories:
            if query_lower in m['content'].lower():
                results.append(m)
        return results[:10]
    
    def extract_memories_from_message(self, user_id: str, message: str):
        lower_msg = message.lower()
        added = []
        
        # Birthday detection
        if 'birthday' in lower_msg:
            import re
            dates = re.findall(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', message)
            if dates:
                added.append(self.add_memory(user_id, f"Birthday is {dates[0]}", "personal", 9))
        
        # Goal detection
        if any(word in lower_msg for word in ['want to', 'goal', 'plan to', 'i will']):
            added.append(self.add_memory(user_id, f"Goal: {message[:100]}", "goal", 8))
        
        # Dream detection
        if 'dream' in lower_msg and ('had' in lower_msg or 'last night' in lower_msg):
            added.append(self.add_memory(user_id, f"Dream: {message[:100]}", "dream", 7))
        
        # Work/career
        if any(word in lower_msg for word in ['work', 'job', 'career', 'boss', 'colleague']):
            added.append(self.add_memory(user_id, f"Work: {message[:100]}", "work", 6))
        
        # Relationship
        if any(word in lower_msg for word in ['mom', 'dad', 'friend', 'partner', 'girlfriend', 'boyfriend']):
            added.append(self.add_memory(user_id, f"Relationship: {message[:100]}", "relationship", 7))
        
        # Music
        if any(word in lower_msg for word in ['song', 'music', 'band', 'album', 'listen']):
            added.append(self.add_memory(user_id, f"Music: {message[:100]}", "music", 5))
        
        # Always store the conversation
        if len(message) > 10:
            added.append(self.add_memory(user_id, f"Discussed: {message[:80]}", "conversation", 3))
        
        return added
    
    def get_context_string(self, user_id: str) -> str:
        memories = self.get_memories(user_id, 15)
        if not memories:
            return ""
        
        context = "\n\n📝 What I remember about you:\n"
        for m in memories:
            context += f"• {m['content']} ({m['date']})\n"
        return context
    
    def delete_user_memories(self, user_id: str):
        self.memories = [m for m in self.memories if m['user_id'] != user_id]
        self.save()

# Global instance
memory_engine = ZeniMemory()
