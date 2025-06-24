// Posts Module
const Posts = (() => {
  const baseUrl = 'http://localhost:5000/api/posts';
  
  // Get recent lost items
  const getRecentLostItems = async () => {
    try {
      const response = await fetch(`${baseUrl}/lost?limit=4`);
      if (response.ok) {
        const items = await response.json();
        renderItems(items, 'recent-lost-items');
      }
    } catch (err) {
      console.error('Failed to fetch items:', err);
    }
  };

  // Render items to DOM
  const renderItems = (items, containerId) => {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = items.map(item => `
      <div class="item-card">
        <img src="${item.images[0] || '/images/placeholder.jpg'}" alt="${item.title}">
        <h4>${item.title}</h4>
        <p>${item.description.substring(0, 50)}...</p>
        <small>Lost on: ${new Date(item.date).toLocaleDateString()}</small>
      </div>
    `).join('');
  };

  // Initialize
  if (document.getElementById('recent-lost-items')) {
    getRecentLostItems();
  }

  return {
    getRecentLostItems,
    renderItems
  };
})();