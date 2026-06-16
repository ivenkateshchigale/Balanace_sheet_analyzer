// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileStatus = document.getElementById('fileStatus');
const qaSection = document.getElementById('qaSection');
const chatHistory = document.getElementById('chatHistory');
const questionInput = document.getElementById('questionInput');
const askBtn = document.getElementById('askBtn');
const resetBtn = document.getElementById('resetBtn');
const endSessionBtn = document.getElementById('endSessionBtn');

let fileUploaded = false;

// File Upload Handling
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        handleFileUpload();
    }
});

fileInput.addEventListener('change', handleFileUpload);

async function handleFileUpload() {
    const file = fileInput.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['application/pdf', 'text/plain'];
    if (!validTypes.includes(file.type) && !file.name.endsWith('.pdf') && !file.name.endsWith('.txt')) {
        showStatus('Only PDF and TXT files are allowed', 'error');
        return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
        showStatus('File is too large. Maximum size is 50MB', 'error');
        return;
    }

    showStatus('Uploading and processing...', 'loading');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(`✓ Successfully loaded: ${data.filename}`, 'success');
            fileUploaded = true;
            qaSection.style.display = 'block';
            questionInput.focus();
            clearChat();
        } else {
            showStatus(`Error: ${data.error}`, 'error');
            fileUploaded = false;
            qaSection.style.display = 'none';
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
        fileUploaded = false;
        qaSection.style.display = 'none';
    }
}

function showStatus(message, type) {
    fileStatus.textContent = message;
    fileStatus.className = `file-status ${type}`;
}

// QA Handling
askBtn.addEventListener('click', askQuestion);
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askQuestion();
    }
});
resetBtn.addEventListener('click', resetConversation);
endSessionBtn.addEventListener('click', endSession);

async function askQuestion() {
    const question = questionInput.value.trim();
    
    if (!question) {
        questionInput.focus();
        return;
    }

    if (!fileUploaded) {
        addMessage('Please upload a balance sheet first', 'error');
        return;
    }

    // Add user message
    addMessage(question, 'user');
    questionInput.value = '';
    questionInput.disabled = true;
    askBtn.disabled = true;

    // Add loading indicator
    addMessage('Thinking...', 'loading');

    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });

        const data = await response.json();

        // Remove loading message
        removeLastMessage();

        if (response.ok) {
            addMessage(data.answer, 'assistant');
        } else {
            addMessage(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        removeLastMessage();
        addMessage(`Error: ${error.message}`, 'error');
    } finally {
        questionInput.disabled = false;
        askBtn.disabled = false;
        questionInput.focus();
    }
}

function addMessage(text, role) {
    const messageEl = document.createElement('div');
    messageEl.className = `chat-message ${role}`;
    messageEl.textContent = text;
    chatHistory.appendChild(messageEl);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function removeLastMessage() {
    const lastMessage = chatHistory.lastElementChild;
    if (lastMessage) {
        lastMessage.remove();
    }
}

function clearChat() {
    chatHistory.innerHTML = '';
}

async function resetConversation() {
    if (!fileUploaded) return;

    if (!confirm('Clear conversation history?')) {
        return;
    }

    try {
        const response = await fetch('/api/reset', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            clearChat();
            addMessage('Conversation history cleared. You can now ask new questions.', 'assistant');
        } else {
            addMessage(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        addMessage(`Error: ${error.message}`, 'error');
    }
}

// Initialize
window.addEventListener('load', () => {
    questionInput.focus();
});

async function endSession() {
    if (!confirm('Are you sure you want to end the session? The server will stop.')) {
        return;
    }

    try {
        addMessage('Ending session...', 'loading');
        
        const response = await fetch('/api/shutdown', {
            method: 'POST'
        });

        if (response.ok) {
            addMessage('✓ Server stopped successfully. You can close this window.', 'assistant');
            askBtn.disabled = true;
            questionInput.disabled = true;
            resetBtn.disabled = true;
            endSessionBtn.disabled = true;
            setTimeout(() => {
                window.close();
            }, 2000);
        }
    } catch (error) {
        // Server already stopped
        addMessage('Session ended. The server has stopped.', 'assistant');
        askBtn.disabled = true;
        questionInput.disabled = true;
        resetBtn.disabled = true;
        endSessionBtn.disabled = true;
    }
}
