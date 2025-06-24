// Image similarity AI feature integration
const imageSimilarityModule = (() => {
  // Initialize image similarity feature
  const init = () => {
    setupSimilaritySearch();
    setupSimilarityRecommendations();
  };
  
  // Setup similarity search form
  const setupSimilaritySearch = () => {
    const similaritySearchForm = document.getElementById('similarity-search-form');
    if (!similaritySearchForm) return;
    
    similaritySearchForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const token = Auth.getToken();
      if (!token) {
        alert('Please login to use image search');
        return;
      }
      
      const formData = new FormData();
      const imageInput = document.getElementById('similarity-image');
      
      if (!imageInput.files || imageInput.files.length === 0) {
        alert('Please select an image to search');
        return;
      }
      
      formData.append('image', imageInput.files[0]);
      
      try {
        const searchResultsContainer = document.getElementById('similarity-results');
        searchResultsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p>Analyzing image and searching for similar items...</p></div>';
        
        const response = await fetch('/api/posts/find-similar?type=FOUND', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });
        
        if (response.ok) {
          const similarItems = await response.json();
          
          if (similarItems.length === 0) {
            searchResultsContainer.innerHTML = '<div class="alert alert-info">No similar items found. Try a different image or check back later.</div>';
            return;
          }
          
          searchResultsContainer.innerHTML = '<h4>Similar Items Found</h4><div class="similar-items-grid"></div>';
          const itemsGrid = searchResultsContainer.querySelector('.similar-items-grid');
          
          similarItems.forEach(item => {
            const itemCard = document.createElement('div');
            itemCard.className = 'item-card';
            
            const similarityPercent = Math.round(item.similarity * 100);
            
            itemCard.innerHTML = `
              <div class="similarity-badge">${similarityPercent}% match</div>
              <img src="${item.images && item.images[0] ? item.images[0] : '/images/placeholder.jpg'}" alt="${item.title}">
              <h4>${item.title}</h4>
              <p><strong>Category:</strong> ${item.category.replace('_', ' ')}</p>
              <p><strong>Found at:</strong> ${item.location}</p>
              <p><strong>Date:</strong> ${new Date(item.date).toLocaleDateString()}</p>
              <button class="btn claim-btn" data-id="${item._id}">I Lost This</button>
            `;
            
            itemsGrid.appendChild(itemCard);
          });
          
          // Add event listeners to claim buttons
          document.querySelectorAll('.claim-btn').forEach(btn => {
            btn.addEventListener('click', () => {
              if (!Auth.getToken()) {
                alert('Please login to claim items');
                return;
              }
              claimItem(btn.dataset.id);
            });
          });
        } else {
          throw new Error('Search failed');
        }
      } catch (err) {
        console.error('Error searching for similar items:', err);
        document.getElementById('similarity-results').innerHTML = '<div class="alert alert-danger">Failed to search for similar items. Please try again.</div>';
      }
    });
  };
  
  // Setup automatic similarity recommendations for lost items
  const setupSimilarityRecommendations = () => {
    const recommendationsContainer = document.getElementById('similarity-recommendations');
    if (!recommendationsContainer) return;
    
    const postId = new URLSearchParams(window.location.search).get('post');
    if (!postId) return;
    
    loadSimilarityRecommendations(postId, recommendationsContainer);
  };
  
  // Load similarity recommendations for a lost item
  const loadSimilarityRecommendations = async (postId, container) => {
    try {
      const token = Auth.getToken();
      if (!token) return;
      
      container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p>Finding potential matches...</p></div>';
      
      const response = await fetch(`/api/posts/${postId}/similar`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const similarItems = await response.json();
        
        if (similarItems.length === 0) {
          container.innerHTML = '<div class="alert alert-info">No potential matches found yet. We\'ll notify you when similar items are posted.</div>';
          return;
        }
        
        container.innerHTML = '<h4>Potential Matches</h4><div class="similar-items-grid"></div>';
        const itemsGrid = container.querySelector('.similar-items-grid');
        
        similarItems.forEach(item => {
          const itemCard = document.createElement('div');
          itemCard.className = 'item-card';
          
          const similarityPercent = Math.round(item.similarity * 100);
          
          itemCard.innerHTML = `
            <div class="similarity-badge">${similarityPercent}% match</div>
            <img src="${item.images && item.images[0] ? item.images[0] : '/images/placeholder.jpg'}" alt="${item.title}">
            <h4>${item.title}</h4>
            <p><strong>Category:</strong> ${item.category.replace('_', ' ')}</p>
            <p><strong>Found at:</strong> ${item.location}</p>
            <p><strong>Date:</strong> ${new Date(item.date).toLocaleDateString()}</p>
            <a href="/item-details.html?id=${item._id}" class="btn btn-primary">View Details</a>
          `;
          
          itemsGrid.appendChild(itemCard);
        });
      } else {
        throw new Error('Failed to load recommendations');
      }
    } catch (err) {
      console.error('Error loading similarity recommendations:', err);
      container.innerHTML = '<div class="alert alert-danger">Failed to load potential matches. Please try again later.</div>';
    }
  };
  
  return {
    init
  };
})();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Check if user is authenticated
  const token = Auth.getToken();
  if (token) {
    // Initialize image similarity module
    imageSimilarityModule.init();
  }
});
