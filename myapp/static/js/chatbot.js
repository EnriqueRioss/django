// static/js/chatbot.js

document.addEventListener('DOMContentLoaded', function () {
    // --- Selección de Elementos del DOM ---
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotFab = document.getElementById('chatbot-fab');
    const chatbotCloseBtn = document.getElementById('chatbot-close-btn');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const chatbotForm = document.getElementById('chatbot-form');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSendBtn = document.getElementById('chatbot-send-btn');

    // --- Clave para el Almacenamiento de Sesión ---
    const CHAT_HISTORY_KEY = 'genassist_chat_history_v2'; // v2 para evitar conflictos con la versión anterior

    // --- Array para mantener el estado del historial en memoria ---
    let chatHistory = [];

    // --- Funciones de Utilidad ---

    // Dibuja un mensaje en la UI
    function renderMessage(messageObject) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${messageObject.sender}-message`);
        messageElement.innerHTML = messageObject.text; // Renderiza HTML como <strong>, <ul>, etc.
        chatbotMessages.appendChild(messageElement);
    }

    // Dibuja todo el historial de chat en la UI
    function renderChatHistory() {
        chatbotMessages.innerHTML = ''; // Limpia la ventana de chat antes de redibujar
        chatHistory.forEach(message => {
            renderMessage(message);
        });
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight; // Siempre desplaza al final
    }
    
    // Añade un nuevo mensaje al estado y a la UI, y lo guarda
    function addMessage(text, sender) {
        const messageObject = { text, sender };
        chatHistory.push(messageObject); // Añade al array en memoria
        renderMessage(messageObject);     // Dibuja solo el nuevo mensaje
        saveChatHistory();                // Guarda el array actualizado en sessionStorage
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    // Muestra/oculta el indicador de "escribiendo..."
    function showTypingIndicator(show) {
        let indicator = document.getElementById('typing-indicator');
        if (show) {
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.id = 'typing-indicator';
                indicator.classList.add('message', 'bot-message');
                indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
                chatbotMessages.appendChild(indicator);
            }
        } else {
            if (indicator) {
                indicator.remove();
            }
        }
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    // --- Lógica de Persistencia ---

    // Guarda el array del historial en sessionStorage como un string JSON
    function saveChatHistory() {
        try {
            sessionStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(chatHistory));
            console.log('Chat history saved:', chatHistory); // DEBUG
        } catch (e) {
            console.error('Failed to save chat history to sessionStorage:', e);
        }
    }

    // Carga el historial desde sessionStorage
    function loadChatHistory() {
        try {
            const savedHistoryJSON = sessionStorage.getItem(CHAT_HISTORY_KEY);
            console.log('Attempting to load history from sessionStorage...'); // DEBUG

            if (savedHistoryJSON) {
                chatHistory = JSON.parse(savedHistoryJSON);
                console.log('History loaded successfully:', chatHistory); // DEBUG
                renderChatHistory(); // Dibuja todo el historial cargado
            } else {
                console.log('No history found. Initializing with welcome message.'); // DEBUG
                // Si no hay historial, inicializa con un mensaje de bienvenida
                chatHistory = []; // Asegúrate de que el array esté vacío
                addMessage("¡Hola! Soy GenAssist. ¿En qué puedo ayudarte hoy?", 'bot');
            }
        } catch (e) {
            console.error('Failed to load or parse chat history from sessionStorage:', e);
            chatHistory = []; // En caso de error, reinicia el historial
            addMessage("Hubo un error cargando el historial. Empecemos de nuevo.", 'bot');
        }
    }

    // --- Manejadores de Eventos ---

    chatbotFab.addEventListener('click', () => {
        chatbotContainer.classList.add('open');
        chatbotFab.classList.add('hidden');
    });

    chatbotCloseBtn.addEventListener('click', () => {
        chatbotContainer.classList.remove('open');
        chatbotFab.classList.remove('hidden');
    });

    chatbotForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const query = chatbotInput.value.trim();
        if (!query) return;

        addMessage(query, 'user');
        chatbotInput.value = '';
        chatbotInput.disabled = true;
        chatbotSendBtn.disabled = true;
        showTypingIndicator(true);

        try {
            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';').find(row => row.trim().startsWith(name + '='));
                    if (cookie) {
                        cookieValue = decodeURIComponent(cookie.trim().substring(name.length + 1));
                    }
                }
                return cookieValue;
            }
            const csrftoken = getCookie('csrftoken');

            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ query: query })
            });

            const data = await response.json();
            showTypingIndicator(false);

            if (!response.ok) {
                addMessage(`Error: ${data.error || 'No se pudo conectar con el asistente.'}`, 'bot');
            } else {
                addMessage(data.response, 'bot');
            }

        } catch (error) {
            showTypingIndicator(false);
            console.error('Error en la petición del chatbot:', error);
            addMessage('Lo siento, hubo un problema de conexión. Por favor, intenta de nuevo.', 'bot');
        } finally {
            chatbotInput.disabled = false;
            chatbotSendBtn.disabled = false;
            chatbotInput.focus();
        }
    });

    // --- Inicialización ---
    console.log('Chatbot script initialized.'); // DEBUG
    loadChatHistory();
    chatbotInput.disabled = false;
    chatbotSendBtn.disabled = false;
});