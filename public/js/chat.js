// Real-time chat functionality
const chatModule = (() => {
  // Socket.io connection
  let socket;
  let currentChatId = null;
  let currentUserId = null;
  let typingTimeout = null;
  
  // Initialize chat
  const init = (userId) => {
    currentUserId = userId;
    
    // Connect to socket.io
    socket = io();
    
    // Authenticate socket connection
    const token = Auth.getToken();
    if (token) {
      socket.emit('authenticate', token);
    }
    
    // Listen for new messages
    socket.on('message:received', (message) => {
      appendMessage(message);
      updateChatLastActivity(message.timestamp);
      
      // If message is not from current user, mark as unread
      if (message.sender._id !== currentUserId) {
        updateUnreadCount(1);
      }
    });
    
    // Listen for typing indicators
    socket.on('typing:update', (data) => {
      updateTypingIndicator(data.userId, data.isTyping);
    });
    
    // Listen for new notifications
    socket.on('notification:new', () => {
      loadNotifications();
    });
    
    // Listen for message updates (read status)
    socket.on('messages:updated', (data) => {
      if (data.chatId === currentChatId) {
        updateMessageReadStatus();
      }
    });
  };
  
  // Join chat room
  const joinChat = (chatId) => {
    if (currentChatId) {
      socket.emit('leave:chat', currentChatId);
    }
    
    currentChatId = chatId;
    socket.emit('join:chat', chatId);
    
    // Mark messages as read
    socket.emit('messages:read', { chatId });
  };
  
  // Send message
  const sendMessage = (content) => {
    if (!currentChatId || !content.trim()) return;
    
    socket.emit('message:send', {
      chatId: currentChatId,
      content: content.trim()
    });
  };
  
  // Handle typing indicator
  const handleTyping = (isTyping) => {
    if (!currentChatId) return;
    
    if (isTyping) {
      socket.emit('typing:start', { chatId: currentChatId });
      
      // Clear previous timeout
      if (typingTimeout) {
        clearTimeout(typingTimeout);
      }
      
      // Set timeout to stop typing indicator after 3 seconds
      typingTimeout = setTimeout(() => {
        socket.emit('typing:stop', { chatId: currentChatId });
      }, 3000);
    } else {
      socket.emit('typing:stop', { chatId: currentChatId });
    }
  };
  
  // Append message to chat
  const appendMessage = (message) => {
    const chatMessages = document.querySelector('.chat-messages');
    if (!chatMessages) return;
    
    const isCurrentUser = message.sender._id === currentUserId;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${isCurrentUser ? 'message-outgoing' : 'message-incoming'}`;
    messageElement.dataset.id = message._id;
    
    const timestamp = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageElement.innerHTML = `
      <div class="message-content">
        ${!isCurrentUser ? `<div class="message-sender">${message.sender.name}</div>` : ''}
        <div class="message-text">${message.content}</div>
        <div class="message-meta">
          <span class="message-time">${timestamp}</span>
          ${isCurrentUser ? `<span class="message-status">${message.read ? '<i class="bi bi-check-all"></i>' : '<i class="bi bi-check"></i>'}</span>` : ''}
        </div>
      </div>
    `;
    
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  };
  
  // Update typing indicator
  const updateTypingIndicator = (userId, isTyping) => {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (!typingIndicator) return;
    
    if (isTyping && userId !== currentUserId) {
      typingIndicator.style.display = 'block';
    } else {
      typingIndicator.style.display = 'none';
    }
  };
  
  // Update chat last activity
  const updateChatLastActivity = (timestamp) => {
    const chatItem = document.querySelector(`.chat-item[data-id="${currentChatId}"]`);
    if (chatItem) {
      const lastActivity = chatItem.querySelector('.chat-last-activity');
      if (lastActivity) {
        lastActivity.textContent = formatLastActivity(timestamp);
      }
    }
  };
  
  // Update unread count
  const updateUnreadCount = (increment) => {
    const chatItem = document.querySelector(`.chat-item[data-id="${currentChatId}"]`);
    if (chatItem) {
      const unreadBadge = chatItem.querySelector('.unread-badge');
      if (unreadBadge) {
        let count = parseInt(unreadBadge.textContent) || 0;
        count += increment;
        
        if (count > 0) {
          unreadBadge.textContent = count;
          unreadBadge.style.display = 'inline-block';
        } else {
          unreadBadge.style.display = 'none';
        }
      }
    }
  };
  
  // Update message read status
  const updateMessageReadStatus = () => {
    const messages = document.querySelectorAll('.message-outgoing');
    messages.forEach(message => {
      const status = message.querySelector('.message-status');
      if (status) {
        status.innerHTML = '<i class="bi bi-check-all"></i>';
      }
    });
  };
  
  // Format last activity time
  const formatLastActivity = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    // Less than a minute
    if (diff < 60000) {
      return 'Just now';
    }
    
    // Less than an hour
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000);
      return `${minutes}m ago`;
    }
    
    // Less than a day
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000);
      return `${hours}h ago`;
    }
    
    // Less than a week
    if (diff < 604800000) {
      const days = Math.floor(diff / 86400000);
      return `${days}d ago`;
    }
    
    // Otherwise, return date
    return date.toLocaleDateString();
  };
  
  return {
    init,
    joinChat,
    sendMessage,
    handleTyping
  };
})();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Check if user is authenticated
  const token = Auth.getToken();
  if (token) {
    // Get user ID from token
    const payload = JSON.parse(atob(token.split('.')[1]));
    chatModule.init(payload.userId);
    
    // If on chat page, setup chat UI
    const chatId = new URLSearchParams(window.location.search).get('chat');
    if (chatId && document.querySelector('.chat-container')) {
      setupChatUI(chatId);
    }
  }
});

// Setup chat UI
async function setupChatUI(chatId) {
  try {
    // Join chat room
    chatModule.joinChat(chatId);
    
    // Load chat messages
    const response = await fetch(`/api/chats/${chatId}`, {
      headers: {
        'Authorization': `Bearer ${Auth.getToken()}`
      }
    });
    
    if (response.ok) {
      const chat = await response.json();
      
      // Set chat title
      document.querySelector('.chat-title').textContent = `Chat: ${chat.claim.post.title}`;
      
      // Clear messages
      const chatMessages = document.querySelector('.chat-messages');
      chatMessages.innerHTML = '';
      
      // Add messages
      chat.messages.forEach(message => {
        chatModule.appendMessage(message);
      });
      
      // Scroll to bottom
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  } catch (err) {
    console.error('Error setting up chat:', err);
  }
  
  // Setup message input
  const messageForm = document.getElementById('message-form');
  const messageInput = document.getElementById('message-input');
  
  messageForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const content = messageInput.value.trim();
    if (content) {
      chatModule.sendMessage(content);
      messageInput.value = '';
    }
  });
  
  // Setup typing indicator
  messageInput.addEventListener('input', () => {
    chatModule.handleTyping(messageInput.value.trim() !== '');
  });
}
