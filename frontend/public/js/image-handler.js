// Image upload and preview functionality
const imageUploadHandler = () => {
  const imageInputs = document.querySelectorAll('.image-upload');
  
  imageInputs.forEach(input => {
    const previewContainer = input.closest('.form-group').querySelector('.image-preview');
    
    input.addEventListener('change', function() {
      previewContainer.innerHTML = '';
      
      if (this.files) {
        const maxFiles = 3;
        const files = Array.from(this.files).slice(0, maxFiles);
        
        files.forEach(file => {
          if (!file.type.match('image.*')) {
            return;
          }
          
          const reader = new FileReader();
          
          reader.onload = function(e) {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';
            
            const img = document.createElement('img');
            img.src = e.target.result;
            img.className = 'img-thumbnail';
            
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn btn-sm btn-danger remove-image';
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', function(e) {
              e.preventDefault();
              previewItem.remove();
              
              // Create a new FileList without this file
              const dt = new DataTransfer();
              const remainingFiles = Array.from(input.files).filter(f => f !== file);
              remainingFiles.forEach(f => dt.items.add(f));
              input.files = dt.files;
            });
            
            previewItem.appendChild(img);
            previewItem.appendChild(removeBtn);
            previewContainer.appendChild(previewItem);
          };
          
          reader.readAsDataURL(file);
        });
      }
    });
  });
};

// Image similarity search functionality
const setupImageSimilaritySearch = () => {
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
      searchResultsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p>Searching for similar items...</p></div>';
      
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

// Initialize image functionality
document.addEventListener('DOMContentLoaded', function() {
  imageUploadHandler();
  setupImageSimilaritySearch();
});
