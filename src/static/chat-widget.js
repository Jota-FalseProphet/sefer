/**
 * Sefer Chat Widget — floating PiP chat synced with main chat session.
 * Reads active conversation from localStorage, loads history, sends to same session.
 */
(function() {
    const TOKEN = localStorage.getItem('sefer_token');
    if (!TOKEN) return;

    const headers = { 'Authorization': `Bearer ${TOKEN}` };
    let currentSessionId = localStorage.getItem('sefer_session_id') || null;
    let currentConvId = localStorage.getItem('sefer_conv_id') || null;
    let isOpen = false;
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };

    // Create widget HTML
    const widget = document.createElement('div');
    widget.id = 'chat-widget';
    widget.innerHTML = `
        <div id="chat-widget-toggle" title="Chat con Sefer">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
        </div>
        <div id="chat-widget-panel">
            <div id="chat-widget-header">
                <span id="chat-widget-title">Sefer</span>
                <div id="chat-widget-controls">
                    <button id="chat-widget-minimize" title="Minimizar">&#8212;</button>
                    <button id="chat-widget-expand" title="Abrir chat completo">&#8599;</button>
                </div>
            </div>
            <div id="chat-widget-messages"></div>
            <div id="chat-widget-typing" style="display:none;">
                <span class="typing-text">Pensando</span><span>.</span><span>.</span><span>.</span>
            </div>
            <div id="chat-widget-input">
                <textarea id="chat-widget-textarea" placeholder="Escribe aqui..." rows="1"></textarea>
                <button id="chat-widget-send">&#9654;</button>
            </div>
        </div>
    `;
    document.body.appendChild(widget);

    const toggle = document.getElementById('chat-widget-toggle');
    const panel = document.getElementById('chat-widget-panel');
    const header = document.getElementById('chat-widget-header');
    const messages = document.getElementById('chat-widget-messages');
    const textarea = document.getElementById('chat-widget-textarea');
    const sendBtn = document.getElementById('chat-widget-send');
    const typing = document.getElementById('chat-widget-typing');
    const typingText = typing.querySelector('.typing-text');
    const minimizeBtn = document.getElementById('chat-widget-minimize');
    const expandBtn = document.getElementById('chat-widget-expand');
    const titleEl = document.getElementById('chat-widget-title');

    // Toggle — always reload history when opening
    toggle.addEventListener('click', () => {
        isOpen = true;
        panel.style.display = 'flex';
        toggle.style.display = 'none';
        loadHistory();
        textarea.focus();
    });

    minimizeBtn.addEventListener('click', () => {
        isOpen = false;
        panel.style.display = 'none';
        toggle.style.display = 'flex';
    });

    expandBtn.addEventListener('click', () => window.location.href = '/');

    // Dragging
    header.addEventListener('mousedown', (e) => {
        if (e.target.tagName === 'BUTTON') return;
        isDragging = true;
        const rect = panel.getBoundingClientRect();
        dragOffset.x = e.clientX - rect.left;
        dragOffset.y = e.clientY - rect.top;
        panel.style.transition = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        panel.style.left = (e.clientX - dragOffset.x) + 'px';
        panel.style.top = (e.clientY - dragOffset.y) + 'px';
        panel.style.right = 'auto';
        panel.style.bottom = 'auto';
    });

    document.addEventListener('mouseup', () => { isDragging = false; panel.style.transition = ''; });

    // Input
    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    textarea.addEventListener('input', () => {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 100) + 'px';
    });
    sendBtn.addEventListener('click', sendMessage);

    // Sync session from localStorage (main chat updates these)
    function syncFromLocalStorage() {
        currentSessionId = localStorage.getItem('sefer_session_id') || null;
        currentConvId = localStorage.getItem('sefer_conv_id') || null;
    }

    // Load history from DB
    async function loadHistory() {
        messages.innerHTML = '';
        syncFromLocalStorage();

        // If no active conversation, load the most recent one
        if (!currentConvId) {
            try {
                const res = await fetch('/api/conversations', { headers });
                if (res.ok) {
                    const convs = await res.json();
                    if (convs.length > 0) {
                        currentConvId = convs[0].id;
                        currentSessionId = convs[0].session_id;
                        localStorage.setItem('sefer_session_id', currentSessionId || '');
                        localStorage.setItem('sefer_conv_id', currentConvId || '');
                        titleEl.textContent = convs[0].title || 'Sefer';
                    }
                }
            } catch {}
        }

        if (!currentConvId) {
            messages.innerHTML = '<div class="message assistant">Hola! Soy Sefer. Preguntame lo que necesites.</div>';
            return;
        }

        try {
            const res = await fetch(`/api/conversations/${currentConvId}/messages`, { headers });
            if (res.ok) {
                const msgs = await res.json();
                for (const msg of msgs) {
                    addMessage(msg.content, msg.role);
                }
            }
        } catch {}

        if (messages.children.length === 0) {
            messages.innerHTML = '<div class="message assistant">Hola! Soy Sefer. Preguntame lo que necesites.</div>';
        }
    }

    function addMessage(text, role) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.textContent = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
    }

    function setTyping(visible, text) {
        typing.style.display = visible ? 'block' : 'none';
        if (text) typingText.textContent = text;
        messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage() {
        const text = textarea.value.trim();
        if (!text) return;

        textarea.value = '';
        textarea.style.height = 'auto';
        sendBtn.disabled = true;

        addMessage(text, 'user');
        setTyping(true, 'Pensando');

        const assistantDiv = addMessage('', 'assistant');
        let textParts = [];
        let toolsUsed = [];

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { ...headers, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    session_id: currentSessionId,
                    conversation_id: currentConvId ? parseInt(currentConvId) : null,
                }),
            });

            if (res.status === 401) { localStorage.clear(); window.location.href = '/login'; return; }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    const data = line.slice(6).trim();
                    if (data === '[DONE]') continue;
                    try {
                        const event = JSON.parse(data);
                        handleEvent(event, assistantDiv, textParts, toolsUsed);
                    } catch {}
                }
            }
        } catch (err) {
            addMessage(`Error: ${err.message}`, 'error');
        }

        setTyping(false);
        sendBtn.disabled = false;
        textarea.focus();

        // Process actions
        const fullText = textParts.join('');
        processActions(fullText, assistantDiv);
    }

    function handleEvent(event, div, textParts, toolsUsed) {
        if (event.type === 'system' && event.subtype === 'init') {
            currentSessionId = event.session_id;
            if (event.conversation_id) currentConvId = event.conversation_id;
            // Sync back to localStorage so main chat stays in sync
            localStorage.setItem('sefer_session_id', currentSessionId || '');
            localStorage.setItem('sefer_conv_id', currentConvId || '');
        }
        if (event.type === 'assistant') {
            for (const block of (event.message?.content || [])) {
                if (block.type === 'text') {
                    textParts.push(block.text);
                    renderAssistant(div, textParts, toolsUsed);
                    setTyping(true, 'Escribiendo');
                } else if (block.type === 'tool_use') {
                    const label = getToolLabel(block.name, block.input);
                    toolsUsed.push(label);
                    renderAssistant(div, textParts, toolsUsed);
                    setTyping(true, label);
                }
            }
        } else if (event.type === 'result') {
            if (event.session_id) currentSessionId = event.session_id;
            if (event.result && textParts.length === 0) {
                textParts.push(event.result);
                renderAssistant(div, textParts, toolsUsed);
            }
            setTyping(false);
        } else if (event.type === 'error') {
            div.className = 'message error';
            div.textContent = event.error || 'Error desconocido';
            setTyping(false);
        }
        messages.scrollTop = messages.scrollHeight;
    }

    function renderAssistant(div, textParts, toolsUsed) {
        let html = '';
        if (toolsUsed.length > 0) {
            html += '<div class="tools-used">';
            for (const t of toolsUsed) html += `<span class="tool-badge">${esc(t)}</span>`;
            html += '</div>';
        }
        html += esc(textParts.join(''));
        div.innerHTML = html;
    }

    function processActions(text, div) {
        const regex = /```sefer-action\n([\s\S]*?)```/g;
        let match;
        while ((match = regex.exec(text)) !== null) {
            const lines = match[1].trim().split('\n');
            const action = {};
            for (const line of lines) {
                const [key, ...val] = line.split(':');
                if (key && val.length) action[key.trim()] = val.join(':').trim();
            }
            executeAction(action, div);
        }

        // Spec blocks
        const specMatch = text.match(/```sefer-spec\n([\s\S]*?)```/);
        if (specMatch) {
            const block = specMatch[1];
            const hi = block.indexOf('---');
            if (hi > 0) {
                const hLines = block.substring(0, hi).trim().split('\n');
                const content = block.substring(hi + 3).trim();
                let title = '', priority = 'medium';
                for (const l of hLines) {
                    if (l.startsWith('title:')) title = l.substring(6).trim();
                    if (l.startsWith('priority:')) priority = l.substring(9).trim();
                }
                if (title) {
                    const btn = document.createElement('button');
                    btn.textContent = 'Guardar como spec';
                    btn.className = 'action-btn';
                    btn.onclick = async () => {
                        const r = await fetch('/api/specs', {
                            method: 'POST',
                            headers: { ...headers, 'Content-Type': 'application/json' },
                            body: JSON.stringify({ title, content, priority, chat_session_id: currentSessionId }),
                        });
                        if (r.ok) { btn.textContent = 'Spec guardada'; btn.disabled = true; btn.classList.add('success'); }
                    };
                    div.appendChild(btn);
                }
            }
        }
    }

    async function executeAction(action, div) {
        const st = document.createElement('div');
        st.className = 'action-status';
        div.appendChild(st);
        try {
            if (action.action === 'move_spec') {
                const r = await fetch(`/api/specs/${action.spec_id}/move`, {
                    method: 'PUT', headers: { ...headers, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: action.status }),
                });
                st.textContent = r.ok ? `Spec movida a ${action.status}` : 'Error';
                st.classList.add(r.ok ? 'success' : 'error');
            } else if (action.action === 'assign_spec') {
                const r = await fetch(`/api/specs/${action.spec_id}/assign`, {
                    method: 'PUT', headers: { ...headers, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ developer_id: parseInt(action.developer_id) }),
                });
                st.textContent = r.ok ? 'Spec asignada' : 'Error';
                st.classList.add(r.ok ? 'success' : 'error');
            }
        } catch { st.textContent = 'Error'; st.classList.add('error'); }
    }

    function getToolLabel(name, input) {
        const labels = { 'Read': 'Leyendo archivo', 'Grep': 'Buscando', 'Glob': 'Buscando archivos' };
        let label = labels[name] || name;
        if (name === 'Read' && input?.file_path) label += `: ${input.file_path.split(/[/\\]/).pop()}`;
        return label;
    }

    function esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }

    // Listen for localStorage changes from main chat (cross-tab sync)
    window.addEventListener('storage', (e) => {
        if (e.key === 'sefer_session_id' || e.key === 'sefer_conv_id') {
            syncFromLocalStorage();
            if (isOpen) loadHistory();
        }
    });
})();
