// Image gallery functionality for item details
function setupImageGallery() {
  const galleryContainers = document.querySelectorAll('.image-gallery');
  
  galleryContainers.forEach(gallery => {
    const mainImage = gallery.querySelector('.gallery-main img');
    const thumbnails = gallery.querySelectorAll('.gallery-thumbnail');
    
    thumbnails.forEach(thumbnail => {
      thumbnail.addEventListener('click', function() {
        // Update main image
        mainImage.src = this.querySelector('img').src;
        
        // Update active state
        thumbnails.forEach(t => t.classList.remove('active'));
        this.classList.add('active');
      });
    });
  });
}

// Function to create image gallery for item details
function createImageGallery(images) {
  if (!images || images.length === 0) {
    return `<div class="no-image">No image available</div>`;
  }
  
  const mainImage = images[0];
  let thumbnailsHtml = '';
  
  images.forEach((image, index) => {
    thumbnailsHtml += `
      <div class="gallery-thumbnail ${index === 0 ? 'active' : ''}">
        <img src="${image}" alt="Item image ${index + 1}">
      </div>
    `;
  });
  
  return `
    <div class="image-gallery">
      <div class="gallery-main">
        <img src="${mainImage}" alt="Item main image">
      </div>
      ${images.length > 1 ? `<div class="gallery-thumbnails">${thumbnailsHtml}</div>` : ''}
    </div>
  `;
}

// Function to render item details with images
function renderItemDetails(item) {
  const detailsContainer = document.getElementById('item-details');
  if (!detailsContainer) return;
  
  const imageGallery = createImageGallery(item.images);
  
  detailsContainer.innerHTML = `
    <div class="row">
      <div class="col-md-6">
        ${imageGallery}
      </div>
      <div class="col-md-6">
        <h2>${item.title}</h2>
        <p class="badge ${item.type === 'LOST' ? 'bg-danger' : 'bg-success'}">${item.type}</p>
        <p><strong>Category:</strong> ${item.category.replace('_', ' ')}</p>
        <p><strong>${item.type === 'LOST' ? 'Lost at' : 'Found at'}:</strong> ${item.location}</p>
        <p><strong>Date:</strong> ${new Date(item.date).toLocaleDateString()}</p>
        <p><strong>Posted by:</strong> ${item.user ? item.user.firstName + ' ' + item.user.lastName : 'Anonymous'}</p>
        <div class="description">
          <h4>Description</h4>
          <p>${item.description || 'No description provided'}</p>
        </div>
        ${item.type === 'FOUND' ? `
          <button id="claim-item-btn" class="btn btn-primary" data-id="${item._id}">I Lost This</button>
        ` : ''}
      </div>
    </div>
  `;
  
  // Setup gallery functionality
  setupImageGallery();
  
  // Add claim button event listener
  const claimBtn = document.getElementById('claim-item-btn');
  if (claimBtn) {
    claimBtn.addEventListener('click', () => {
      if (!Auth.getToken()) {
        alert('Please login to claim items');
        return;
      }
      showClaimForm(item._id);
    });
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // If on item details page, load item details
  const itemId = new URLSearchParams(window.location.search).get('id');
  if (itemId && document.getElementById('item-details')) {
    loadItemDetails(itemId);
  }
});

// Function to load item details
async function loadItemDetails(itemId) {
  try {
    const response = await fetch(`/api/posts/${itemId}`);
    if (response.ok) {
      const item = await response.json();
      renderItemDetails(item);
    } else {
      document.getElementById('item-details').innerHTML = `
        <div class="alert alert-danger">Failed to load item details. The item may have been removed.</div>
      `;
    }
  } catch (err) {
    console.error('Error loading item details:', err);
    document.getElementById('item-details').innerHTML = `
      <div class="alert alert-danger">An error occurred while loading item details.</div>
    `;
  }
}
