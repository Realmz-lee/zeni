// app.js
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const settingsToggle = document.getElementById('settingsToggle');
const settingsPanel = document.getElementById('settingsPanel');
const closeSettings = document.getElementById('closeSettings');
const clearMemoryBtn = document.getElementById('clearMemoryBtn');
const personalitySelect = document.getElementById('personalitySelect');
const userIdInput = document.getElementById('userIdInput');
const backendUrlInput = document.getElementById('backendUrl');
const statusBadge = document.getElementById('statusBadge');
const memoryCountLabel = document.getElementById('memoryCountLabel');

// Load saved settings
let userId = localStorage.getItem('zeni_user_id') || 'user_' + Math.random().toString(36).substr(2, 8);
let backendUrl = localStorage.getItem('zeni_backend_url') || 'http://localhost:8000';
let currentPersonality = localStorage.getItem('zeni_personality') || 'friend';

userIdInput.value = userId;
backendUrlInput.value = backendUrl;
personalitySelect.value = currentPersonality;

// Save settings when changed
userIdInput.addEventListener('change', () => {
    userId = userIdInput.value;
    localStorage.setItem('zeni_user_id', userId);
    loadMemoriesCount();
});

backendUrlInput.addEventListener('change', () => {
    backendUrl = backendUrlInput.value;
    localStorage.setItem('zeni_backend_url', backendUrl);
    checkBackendHealth();
});

personalitySelect.addEventListener('change', () => {
    currentPersonality = personalitySelect.value;
    localStorage.setItem('zeni_personality', currentPersonality);
});

// UI Functions
function addMessage(text, isUser = true) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isUser ? 'user' : 'zeni'}`;
    msgDiv.innerHTML = `
        <div class="bubble">${text.replace(/\n/g, '<br>')}</div>
        <div class="timestamp">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
    `;
    chatMessages.appendChild(msgDiv);
    msgDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function addSystemMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message zeni';
    msgDiv.innerHTML = `
        <div class="bubble" style="background: rgba(139, 92, 246, 0.15);">
            🔧 ${text}
        </div>
        <div class="timestamp">Just now</div>
    `;
    chatMessages.appendChild(msgDiv);
    msgDiv.scrollIntoView({ behavior: 'smooth' });
}

// Backend API calls
async function checkBackendHealth() {
    try {
        const response = await fetch(`${backendUrl}/health`);
        if (response.ok) {
            statusBadge.innerHTML = '🟢 Connected';
            statusBadge.style.borderColor = 'rgba(34, 197, 94, 0.3)';
            statusBadge.style.color = '#22c55e';
            return true;
        }
    } catch (e) {
        statusBadge.innerHTML = '🔴 Offline';
        statusBadge.style.borderColor = 'rgba(239, 68, 68, 0.3)';
        statusBadge.style.color = '#EF4444';
    }
    return false;
}

async function loadMemoriesCount() {
    try {
        const response = await fetch(`${backendUrl}/memories/${userId}?limit=1`);
        const data = await response.json();
        memoryCountLabel.textContent = `📝 Memories: ${data.count}`;
    } catch (e) {
        memoryCountLabel.textContent = '📝 Memories: Offline';
    }
}

async function sendToZeni(message) {
    try {
        const response = await fetch(`${backendUrl}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                message: message,
                personality: currentPersonality
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        return data.reply;
    } catch (error) {
        console.error('Error:', error);
        return `😅 Can't reach Zeni's brain. Make sure the backend is running at ${backendUrl}`;
    }
}

async function clearMemories() {
    if (!confirm('⚠️ Delete ALL memories? This cannot be undone.')) return;
    
    try {
        const response = await fetch(`${backendUrl}/memories/${userId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            addSystemMessage('🗑️ All memories cleared. Zeni starts fresh with you.');
            loadMemoriesCount();
        } else {
            addSystemMessage('❌ Failed to clear memories');
        }
    } catch (e) {
        addSystemMessage('❌ Cannot connect to backend');
    }
}

// Chat handler
async function handleSend() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    messageInput.value = '';
    addMessage(message, true);
    
    typingIndicator.style.display = 'flex';
    
    const reply = await sendToZeni(message);
    
    typingIndicator.style.display = 'none';
    addMessage(reply, false);
    
    loadMemoriesCount();
    messageInput.focus();
}

// Event listeners
sendBtn.addEventListener('click', handleSend);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
});

settingsToggle.addEventListener('click', () => {
    settingsPanel.classList.toggle('show');
});

closeSettings.addEventListener('click', () => {
    settingsPanel.classList.remove('show');
});

clearMemoryBtn.addEventListener('click', clearMemories);

// Initialize
checkBackendHealth();
setInterval(checkBackendHealth, 30000);
loadMemoriesCount();
