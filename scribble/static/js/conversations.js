// conversations.js - Handles all conversation-related functionality
let currentConversationId = null;
let messagePollingInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize conversation functionality when the conversations page loads
    if (document.getElementById('conversations-page')) {
        initConversationList();
        initMessageHandling();
        initSearchAndFilters();
        
        // Handle page visibility change to refresh data if needed
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && currentConversationId) {
                loadConversation(currentConversationId);
            }
        });
    }
});

// Start polling for new messages
function startMessagePolling(conversationId) {
    // Clear any existing interval
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
    }
    
    // Poll for new messages every 3 seconds
    messagePollingInterval = setInterval(() => {
        if (currentConversationId) {
            fetch(`/api/chat/conversation/${currentConversationId}/messages/`)
                .then(response => response.json())
                .then(data => {
                    if (data.messages && data.messages.length > 0) {
                        renderMessages(data.messages);
                    }
                })
                .catch(error => console.error('Error fetching messages:', error));
        }
    }, 3000);
}

// Add a message to the chat UI
function addMessageToChat(messageData) {
    const messagesContainer = document.getElementById('messages-container');
    if (!messagesContainer) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${messageData.sender}`;
    messageElement.id = `msg-${messageData.id}`;
    
    const isUser = messageData.sender === 'user';
    const messageClass = isUser ? 'user' : 'ai';
    
    messageElement.innerHTML = `
        <div class="flex ${isUser ? 'justify-end' : 'justify-start'} mb-4">
            <div class="flex max-w-xs lg:max-w-md">
                <div class="${isUser ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-800'} px-4 py-2 rounded-lg shadow">
                    <div class="message-content">${formatMessageContent(messageData.content)}</div>
                    <div class="text-xs mt-1 text-right ${isUser ? 'text-indigo-200' : 'text-gray-500'}">
                        ${formatTime(messageData.created_at)}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Initialize the conversation list
function initConversationList() {
    // Load conversations
    loadConversations();
    
    // Set up auto-refresh
    setInterval(loadConversations, 30000); // Refresh every 30 seconds
}

// Load conversations from the API
function loadConversations() {
    const container = document.getElementById('conversation-list');
    if (!container) return;
    
    // Show loading state
    container.innerHTML = `
        <div class="p-4 text-center text-gray-500">
            <i class="fas fa-spinner fa-spin text-2xl mb-2"></i>
            <p>Loading conversations...</p>
        </div>`;
    
    // Get filter values
    const searchQuery = document.getElementById('search-conversations')?.value || '';
    const statusFilter = document.getElementById('status-filter')?.value || 'all';
    const dateFrom = document.getElementById('date-from')?.value || '';
    const dateTo = document.getElementById('date-to')?.value || '';
    
    // Build query string
    const params = new URLSearchParams({
        search: searchQuery,
        status: statusFilter,
        date_from: dateFrom,
        date_to: dateTo,
        limit: 50
    });
    
    // Fetch conversations
    fetch(`/api/conversations/?${params.toString()}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to load conversations');
            return response.json();
        })
        .then(data => {
            renderConversationList(data.results || []);
            
            // If there's an active conversation, load its messages
            const activeConversationId = getActiveConversationId();
            if (activeConversationId) {
                loadConversation(activeConversationId);
            }
        })
        .catch(error => {
            console.error('Error loading conversations:', error);
            container.innerHTML = `
                <div class="p-4 text-center text-red-500">
                    <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                    <p>Failed to load conversations. Please try again.</p>
                    <button onclick="loadConversations()" class="mt-2 px-3 py-1 bg-gray-100 rounded hover:bg-gray-200">
                        <i class="fas fa-sync-alt mr-1"></i> Retry
                    </button>
                </div>`;
        });
}

// Render the list of conversations
function renderConversationList(conversations) {
    const container = document.getElementById('conversation-list');
    if (!container) return;
    
    if (conversations.length === 0) {
        container.innerHTML = `
            <div class="p-4 text-center text-gray-500">
                <i class="far fa-comment-dots text-2xl mb-2"></i>
                <p>No conversations found</p>
            </div>`;
        return;
    }
    
    const activeConversationId = getActiveConversationId();
    
    container.innerHTML = conversations.map(conv => `
        <div class="conversation-item border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${activeConversationId === conv.id ? 'bg-blue-50' : ''}" 
             data-conversation-id="${conv.id}">
            <div class="p-4">
                <div class="flex justify-between items-start">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center">
                            <h4 class="text-sm font-medium text-gray-900 truncate">
                                ${conv.user?.name || 'Anonymous User'}
                            </h4>
                            ${conv.unread_count > 0 ? 
                                `<span class="ml-2 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                                    ${conv.unread_count}
                                </span>` : ''
                            }
                        </div>
                        <p class="text-sm text-gray-500 truncate mt-1">
                            ${conv.last_message?.content ? 
                                `${conv.last_message.sender === 'user' ? 'User: ' : 'AI: '}${conv.last_message.content}` : 
                                'No messages yet'}
                        </p>
                    </div>
                    <div class="ml-4 flex-shrink-0">
                        <span class="text-xs text-gray-500">
                            ${formatTimeAgo(conv.updated_at)}
                        </span>
                    </div>
                </div>
                <div class="mt-2 flex items-center text-xs text-gray-500">
                    <span class="inline-flex items-center">
                        <i class="fas ${conv.ai_enabled ? 'fa-toggle-on text-green-500' : 'fa-toggle-off text-gray-400'} mr-1"></i>
                        AI ${conv.ai_enabled ? 'On' : 'Off'}
                    </span>
                    <span class="mx-2">•</span>
                    <span>${formatDate(conv.updated_at)}</span>
                </div>
            </div>
        </div>`
    ).join('');
    
    // Add click handlers to conversation items
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', function() {
            const conversationId = this.getAttribute('data-conversation-id');
            loadConversation(conversationId);
            
            // Update active state
            document.querySelectorAll('.conversation-item').forEach(i => 
                i.classList.remove('bg-blue-50')
            );
            this.classList.add('bg-blue-50');
            
            // Update URL
            history.pushState({}, '', `?conversation=${conversationId}`);
        });
    });
}

// Load a specific conversation
function loadConversation(conversationId) {
    // Start polling for messages
    startMessagePolling(conversationId);
    if (!conversationId) return;
    
    const messagesContainer = document.getElementById('messages-container');
    const chatTitle = document.getElementById('chat-title');
    const chatSubtitle = document.getElementById('chat-subtitle');
    const aiToggleContainer = document.getElementById('ai-toggle-container');
    
    // Show loading state
    messagesContainer.innerHTML = `
        <div class="flex items-center justify-center h-full">
            <div class="text-center">
                <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
                <p class="text-gray-500">Loading conversation...</p>
            </div>
        </div>`;
    
    // Fetch conversation details
    fetch(`/api/conversations/${conversationId}/`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to load conversation');
            return response.json();
        })
        .then(conversation => {
            // Update UI with conversation info
            chatTitle.textContent = conversation.user?.name || 'Anonymous User';
            chatSubtitle.textContent = conversation.started_at ? 
                `Started ${formatFullDate(conversation.started_at)}` : 'New conversation';
            
            // Show AI toggle
            aiToggleContainer.style.display = 'flex';
            updateAIToggle(conversation.ai_enabled);
            
            // Load messages
            return fetch(`/api/conversations/${conversationId}/messages/`);
        })
        .then(response => {
            if (!response.ok) throw new Error('Failed to load messages');
            return response.json();
        })
        .then(data => {
            renderMessages(data.results || []);
            
            // Mark messages as read
            markMessagesAsRead(conversationId);
            
            // Scroll to bottom
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Update unread count in the conversation list
            updateUnreadCount(conversationId, 0);
        })
        .catch(error => {
            console.error('Error loading conversation:', error);
            messagesContainer.innerHTML = `
                <div class="p-4 text-center text-red-500">
                    <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                    <p>Failed to load conversation. Please try again.</p>
                    <button onclick="loadConversation('${conversationId}')" class="mt-2 px-3 py-1 bg-gray-100 rounded hover:bg-gray-200">
                        <i class="fas fa-sync-alt mr-1"></i> Retry
                    </button>
                </div>`;
        });
}

// Render messages in the chat area
function renderMessages(messages) {
    const container = document.getElementById('messages-container');
    if (!container) return;
    
    container.innerHTML = messages.map(msg => `
        <div class="message ${msg.sender}">
            <div class="flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} mb-4">
                <div class="flex max-w-xs lg:max-w-md">
                    ${msg.sender !== 'user' ? `
                        <div class="flex-shrink-0 h-8 w-8 rounded-full bg-indigo-200 flex items-center justify-center text-indigo-600 mr-2">
                            <i class="fas fa-robot"></i>
                        </div>
                    ` : ''}
                    <div class="${msg.sender === 'user' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-800'} px-4 py-2 rounded-lg shadow">
                        <div class="message-content">${formatMessageContent(msg.content)}</div>
                        <div class="text-xs mt-1 text-right ${msg.sender === 'user' ? 'text-indigo-200' : 'text-gray-500'}">
                            ${formatTime(msg.created_at)}
                            ${msg.is_read ? '<i class="fas fa-check ml-1"></i>' : ''}
                        </div>
                    </div>
                    ${msg.sender === 'user' ? `
                        <div class="flex-shrink-0 h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 ml-2">
                            <i class="fas fa-user"></i>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>`
    ).join('');
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Handle incoming message data
function handleIncomingMessage(message) {
    // Check if this message is already displayed
    if (document.getElementById(`msg-${message.id}`)) {
        return; // Skip if message already exists
    }
    
    // Add the message to the chat
    addMessageToChat(message);
    
    // Mark as read if it's a user message
    if (message.sender === 'user' && !message.is_read) {
        markMessagesAsRead(currentConversationId);
    }
    
    // Update the conversation list to show the latest message
    if (document.getElementById('conversation-list')) {
        loadConversations();
    }
}

// Initialize message sending and receiving
function initMessageHandling() {
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    
    if (messageForm && messageInput) {
        // Handle form submission
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = messageInput.value.trim();
            if (!message) return;
            
            const conversationId = getActiveConversationId();
            if (!conversationId) {
                // Create a new conversation if none is active
                createNewConversation(message);
                return;
            }
            
            // Send message via AJAX
            fetch(`/api/chat/conversation/${conversationId}/send/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ message })
            })
            .then(response => response.json())
            .then(data => {
                // Add message to UI immediately
                const messageHtml = `
                    <div class="message user">
                        <div class="flex justify-end mb-4">
                            <div class="flex max-w-xs lg:max-w-md">
                                <div class="bg-indigo-600 text-white px-4 py-2 rounded-lg shadow">
                                    <div class="message-content">${formatMessageContent(message)}</div>
                                    <div class="text-xs mt-1 text-right text-indigo-200">
                                        Just now
                                        <i class="fas fa-check ml-1"></i>
                                    </div>
                                </div>
                                <div class="flex-shrink-0 h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 ml-2">
                                    <i class="fas fa-user"></i>
                                </div>
                            </div>
                        </div>
                    </div>`;
                const messagesContainer = document.getElementById('messages-container');
                messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            })
            .catch(error => {
                console.error('Error sending message:', error);
                const errorElement = document.createElement('div');
                errorElement.className = 'text-red-500 text-sm mt-1 text-center';
                errorElement.textContent = 'Failed to send message. Please try again.';
                document.getElementById('message-input').appendChild(errorElement);
            });
            
            // Clear input
            messageInput.value = '';
        });
        
        // Handle AI toggle
        const aiToggle = document.getElementById('toggle-ai');
        if (aiToggle) {
            aiToggle.addEventListener('click', function() {
                const conversationId = getActiveConversationId();
                if (!conversationId) return;
                
                const currentStatus = document.getElementById('ai-status').textContent === 'On';
                toggleAIResponse(conversationId, !currentStatus);
            });
        }
    }
}

// Toggle AI response for a conversation
function toggleAIResponse(conversationId, enable) {
    const toggleCircle = document.getElementById('toggle-circle');
    const aiStatus = document.getElementById('ai-status');
    
    // Update UI immediately for better responsiveness
    toggleCircle.style.transform = enable ? 'translateX(1.5rem)' : 'translateX(0.25rem)';
    aiStatus.textContent = enable ? 'On' : 'Off';
    
    // Send request to server
    fetch(`/api/conversations/${conversationId}/toggle-ai/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ enable })
    })
    .then(response => response.json())
    .then(data => {
        // Update UI based on server response
        if (data.ai_enabled !== undefined) {
            aiStatus.textContent = data.ai_enabled ? 'On' : 'Off';
            toggleCircle.style.transform = data.ai_enabled ? 'translateX(1.5rem)' : 'translateX(0.25rem)';
            
            // Show notification
            showNotification(
                'AI Responses Updated',
                `AI responses have been turned ${data.ai_enabled ? 'on' : 'off'} for this conversation`,
                'success'
            );
        }
    })
    .catch(error => {
        console.error('Error toggling AI:', error);
        showNotification('Error', 'Failed to update AI settings', 'error');
    });
}

// Initialize search and filter functionality
function initSearchAndFilters() {
    // Search input
    const searchInput = document.getElementById('search-conversations');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                loadConversations();
            }, 500);
        });
    }
    
    // Status filter
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', loadConversations);
    }
    
    // Date range filter
    const dateFrom = document.getElementById('date-from');
    const dateTo = document.getElementById('date-to');
    
    if (dateFrom) {
        dateFrom.addEventListener('change', function() {
            if (dateTo.value && dateTo.value < this.value) {
                dateTo.value = this.value;
            }
            loadConversations();
        });
    }
    
    if (dateTo) {
        dateTo.addEventListener('change', function() {
            if (dateFrom.value && dateFrom.value > this.value) {
                dateFrom.value = this.value;
            }
            loadConversations();
        });
    }
    
    // Clear filters button
    const clearFiltersBtn = document.getElementById('clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            if (searchInput) searchInput.value = '';
            if (statusFilter) statusFilter.value = 'all';
            if (dateFrom) dateFrom.value = '';
            if (dateTo) dateTo.value = '';
            loadConversations();
        });
    }
}

// Get the currently active conversation ID from the URL
function getActiveConversationId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('conversation');
}

// Mark messages as read
function markMessagesAsRead(conversationId) {
    fetch(`/api/conversations/${conversationId}/mark-read/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .catch(error => console.error('Error marking messages as read:', error));
}

// Update unread count for a conversation in the list
function updateUnreadCount(conversationId, count) {
    const conversationItem = document.querySelector(`.conversation-item[data-conversation-id="${conversationId}"]`);
    if (!conversationItem) return;
    
    const unreadBadge = conversationItem.querySelector('.unread-badge');
    
    if (count > 0) {
        if (!unreadBadge) {
            const badge = document.createElement('span');
            badge.className = 'unread-badge ml-2 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full';
            badge.textContent = count;
            conversationItem.querySelector('h4').appendChild(badge);
        } else {
            unreadBadge.textContent = count;
        }
    } else if (unreadBadge) {
        unreadBadge.remove();
    }
}

// Format message content (URLs, line breaks, etc.)
function formatMessageContent(content) {
    if (!content) return '';
    
    // Convert URLs to links
    let formatted = content.replace(
        /(https?:\/\/[^\s]+)/g, 
        url => `<a href="${url}" target="_blank" class="text-indigo-600 hover:underline">${url}</a>`
    );
    
    // Convert line breaks to <br>
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
}

// Format date as relative time (e.g., "2 hours ago")
function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return interval === 1 ? `1 ${unit} ago` : `${interval} ${unit}s ago`;
        }
    }
    
    return 'Just now';
}

// Format time (e.g., "2:30 PM")
function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

// Format full date (e.g., "Jan 1, 2023")
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
}

// Format full date and time (e.g., "Jan 1, 2023, 2:30 PM")
function formatFullDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString([], { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
    });
}

// Get CSRF token from cookies
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

// Create a new conversation
function createNewConversation(firstMessage) {
    // Show loading state
    const messagesContainer = document.getElementById('messages-container');
    messagesContainer.innerHTML = `
        <div class="flex items-center justify-center h-full">
            <div class="text-center">
                <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
                <p class="text-gray-500">Starting new conversation...</p>
            </div>
        </div>`;
    
    // Create new conversation
    fetch('/api/conversations/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            initial_message: firstMessage
        })
    })
    .then(response => response.json())
    .then(conversation => {
        // Update URL with new conversation ID
        history.pushState({}, '', `?conversation=${conversation.id}`);
        
        // Load the new conversation
        loadConversation(conversation.id);
        
        // Reload conversation list to show the new one
        loadConversations();
    })
    .catch(error => {
        console.error('Error creating conversation:', error);
        messagesContainer.innerHTML = `
            <div class="p-4 text-center text-red-500">
                <i class="fas fa-exclamation-circle text-2xl mb-2"></i>
                <p>Failed to start a new conversation. Please try again.</p>
                <button onclick="createNewConversation('${firstMessage}')" class="mt-2 px-3 py-1 bg-gray-100 rounded hover:bg-gray-200">
                    <i class="fas fa-sync-alt mr-1"></i> Retry
                </button>
            </div>`;
    });
}

// Export functions to global scope
window.loadConversations = loadConversations;
window.loadConversation = loadConversation;
window.sendMessage = sendMessage;
