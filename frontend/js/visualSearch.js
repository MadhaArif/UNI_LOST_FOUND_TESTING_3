// Visual Search Functionality

class VisualSearchHandler {
    constructor() {
        this.init();
    }

    init() {
        // Initialize event listeners
        this.setupImageUpload();
        this.setupVisualSearchForm();
    }

    setupImageUpload() {
        const imageUpload = document.getElementById('imageUpload');
        const imagePreview = document.getElementById('imagePreview');

        if (imageUpload) {
            imageUpload.addEventListener('change', (event) => {
                const file = event.target.files[0];
                if (file) {
                    // Validate file type
                    if (!file.type.startsWith('image/')) {
                        alert('Please select a valid image file.');
                        return;
                    }

                    // Validate file size (max 5MB)
                    if (file.size > 5 * 1024 * 1024) {
                        alert('Image size should be less than 5MB.');
                        return;
                    }

                    // Preview the image
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        imagePreview.src = e.target.result;
                        imagePreview.style.display = 'block';
                        
                        // Enable visual search
                        this.enableVisualSearch(e.target.result);
                    };
                    reader.readAsDataURL(file);
                }
            });
        }
    }

    setupVisualSearchForm() {
        // Create search button if it doesn't exist
        const uploadSection = document.querySelector('.visual-search-section .col-md-6');
        if (uploadSection && !document.getElementById('visualSearchBtn')) {
            const searchButton = document.createElement('button');
            searchButton.id = 'visualSearchBtn';
            searchButton.className = 'btn btn-primary w-100 mt-3';
            searchButton.innerHTML = '<i class="fas fa-search me-2"></i>Search Similar Items';
            searchButton.style.display = 'none';
            searchButton.onclick = () => this.performVisualSearch();
            
            uploadSection.appendChild(searchButton);
        }
    }

    enableVisualSearch(imageDataUrl) {
        const searchBtn = document.getElementById('visualSearchBtn');
        if (searchBtn) {
            searchBtn.style.display = 'block';
            this.currentImageData = imageDataUrl;
        }
    }

    async performVisualSearch() {
        if (!this.currentImageData) {
            alert('Please upload an image first.');
            return;
        }

        const searchBtn = document.getElementById('visualSearchBtn');
        const resultsContainer = document.getElementById('similarItemsResults');
        
        try {
            // Show loading state
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
            searchBtn.disabled = true;

            // Clear previous results
            if (resultsContainer) {
                resultsContainer.innerHTML = '<div class="text-center"><i class="fas fa-search fa-2x text-primary mb-3"></i><p>Analyzing image and searching for similar items...</p></div>';
            }

            // Prepare search data
            const searchData = {
                imageBase64: this.currentImageData,
                searchType: 'both' // Search both lost and found items
            };

            // Make API call
            const response = await fetch('/api/search/visual', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchData)
            });

            const result = await response.json();

            if (result.success) {
                this.displayVisualSearchResults(result.items);
            } else {
                this.displayErrorMessage(result.message || 'Search failed. Please try again.');
            }

        } catch (error) {
            console.error('Visual search error:', error);
            this.displayErrorMessage('An error occurred while searching. Please try again.');
        } finally {
            // Reset button state
            searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>Search Similar Items';
            searchBtn.disabled = false;
        }
    }

    displayVisualSearchResults(items) {
        const resultsContainer = document.getElementById('similarItemsResults');
        
        if (!resultsContainer) return;

        if (items.length === 0) {
            resultsContainer.innerHTML = `
                <div class="alert alert-info text-center">
                    <i class="fas fa-info-circle me-2"></i>
                    No similar items found. Try uploading a different image or check back later.
                </div>
            `;
            return;
        }

        let resultsHTML = `
            <div class="mt-4">
                <h4 class="mb-3">
                    <i class="fas fa-images me-2"></i>
                    Similar Items Found (${items.length})
                </h4>
                <div class="row">
        `;

        items.forEach(item => {
            const similarityBadge = item.similarity_score ? 
                `<span class="badge bg-success">${item.similarity_score}% match</span>` : '';
            
            const itemTypeIcon = item.type === 'lost' ? 
                '<i class="fas fa-search text-danger"></i>' : 
                '<i class="fas fa-hands-helping text-success"></i>';

            resultsHTML += `
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="position-relative">
                            <img src="${item.image || 'https://via.placeholder.com/300x200?text=No+Image'}" 
                                 class="card-img-top" alt="${item.title}" 
                                 style="height: 200px; object-fit: cover;">
                            <div class="position-absolute top-0 end-0 m-2">
                                ${similarityBadge}
                            </div>
                            <div class="position-absolute top-0 start-0 m-2">
                                ${itemTypeIcon}
                            </div>
                        </div>
                        <div class="card-body">
                            <h6 class="card-title">${item.title}</h6>
                            <p class="card-text small text-muted mb-2">
                                <i class="fas fa-map-marker-alt me-1"></i>${item.location}
                                ${item.specificLocation ? ` - ${item.specificLocation}` : ''}
                            </p>
                            <p class="card-text small text-muted mb-2">
                                <i class="fas fa-calendar me-1"></i>${item.date}
                            </p>
                            <p class="card-text small">${item.description.substring(0, 80)}${item.description.length > 80 ? '...' : ''}</p>
                        </div>
                        <div class="card-footer bg-transparent">
                            <button class="btn btn-sm btn-primary w-100" 
                                    onclick="viewItemDetails(${JSON.stringify(item).replace(/"/g, '&quot;')})">
                                <i class="fas fa-eye me-1"></i>View Details
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        resultsHTML += `
                </div>
                <div class="text-center mt-3">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Results are ranked by visual similarity. Higher percentages indicate better matches.
                    </small>
                </div>
            </div>
        `;

        resultsContainer.innerHTML = resultsHTML;
    }

    displayErrorMessage(message) {
        const resultsContainer = document.getElementById('similarItemsResults');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="alert alert-warning text-center">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>
            `;
        }
    }
}

// Initialize visual search when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize visual search handler
    new VisualSearchHandler();
});
