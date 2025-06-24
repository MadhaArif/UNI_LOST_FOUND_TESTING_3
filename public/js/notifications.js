// Notification system functionality
const notificationModule = (() => {
  let unreadCount = 0;
  
  // Initialize notifications
  const init = () => {
    loadNotifications();
    
    // Set up notification dropdown toggle
    const notificationDropdown = document.getElementById('notificationDropdown');
    if (notificationDropdown) {
      notificationDropdown.addEventListener('click', () => {
        markNotificationsAsRead();
      });
    }
  };
  
  // Load notifications
  const loadNotifications = async () => {
    try {
      const token = Auth.getToken();
      if (!token) return;
      
      const response = await fetch('/api/notifications', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const notifications = await response.json();
        renderNotifications(notifications);
        updateUnreadCount(notifications);
      }
    } catch (err) {
      console.error('Error loading notifications:', err);
    }
  };
  
  // Render notifications
  const renderNotifications = (notifications) => {
    const notificationList = document.querySelector('.notification-list');
    if (!notificationList) return;
    
    if (notifications.length === 0) {
      notificationList.innerHTML = '<div class="text-center p-2">No new notifications</div>';
      return;
    }
    
    notificationList.innerHTML = '';
    
    // Show only the latest 5 notifications
    const recentNotifications = notifications.slice(0, 5);
    
    recentNotifications.forEach(notification => {
      const notificationItem = document.createElement('div');
      notificationItem.className = `dropdown-item notification-item ${notification.read ? '' : 'unread'}`;
      notificationItem.dataset.id = notification._id;
      
      // Format date
      const date = new Date(notification.date);
      const formattedDate = formatNotificationDate(date);
      
      // Get icon based on notification type
      const icon = getNotificationIcon(notification.type);
      
      notificationItem.innerHTML = `
        <div class="notification-content">
          <div class="notification-icon">${icon}</div>
          <div class="notification-text">
            <div class="notification-message">${notification.message}</div>
            <div class="notification-time">${formattedDate}</div>
          </div>
        </div>
      `;
      
      // Add click event to navigate to link
      if (notification.link) {
        notificationItem.addEventListener('click', () => {
          window.location.href = notification.link;
        });
      }
      
      notificationList.appendChild(notificationItem);
    });
  };
  
  // Update unread count
  const updateUnreadCount = (notifications) => {
    const unreadNotifications = notifications.filter(notification => !notification.read);
    unreadCount = unreadNotifications.length;
    
    const badge = document.querySelector('.notification-badge');
    if (badge) {
      if (unreadCount > 0) {
        badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        badge.style.display = 'inline-block';
      } else {
        badge.style.display = 'none';
      }
    }
  };
  
  // Mark notifications as read
  const markNotificationsAsRead = async () => {
    try {
      const token = Auth.getToken();
      if (!token || unreadCount === 0) return;
      
      const response = await fetch('/api/notifications/read-all', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        // Update UI
        document.querySelectorAll('.notification-item.unread').forEach(item => {
          item.classList.remove('unread');
        });
        
        // Update badge
        const badge = document.querySelector('.notification-badge');
        if (badge) {
          badge.style.display = 'none';
        }
        
        unreadCount = 0;
      }
    } catch (err) {
      console.error('Error marking notifications as read:', err);
    }
  };
  
  // Format notification date
  const formatNotificationDate = (date) => {
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
  
  // Get notification icon based on type
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'CLAIM':
        return '<i class="bi bi-file-earmark-check"></i>';
      case 'MATCH':
        return '<i class="bi bi-search-heart"></i>';
      case 'CHAT':
        return '<i class="bi bi-chat-dots"></i>';
      case 'SYSTEM':
      default:
        return '<i class="bi bi-bell"></i>';
    }
  };
  
  return {
    init,
    loadNotifications
  };
})();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Check if user is authenticated
  const token = Auth.getToken();
  if (token) {
    // Initialize notification system
    notificationModule.init();
    
    // Show notification container
    const notificationContainer = document.getElementById('notification-container');
    if (notificationContainer) {
      notificationContainer.style.display = 'block';
    }
  }
});
