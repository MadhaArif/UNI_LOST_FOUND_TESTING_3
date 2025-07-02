// Main App JavaScript File

// Function to handle generic API requests
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {}
    };

    if (data) {
        if (data instanceof FormData) {
            // FormData handles its own Content-Type
            options.body = data;
        } else {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        }
    }

    // Add Authorization header if token exists
    const token = localStorage.getItem('token');
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, options);
        const responseData = await response.json();
        if (!response.ok) {
            // Log error or show user-friendly message
            console.error('API Error:', responseData.message || response.statusText);
            alert(`Error: ${responseData.message || response.statusText}`);
            return null;
        }
        return responseData;
    } catch (error) {
        console.error('Network or other error:', error);
        alert('An error occurred. Please check your connection and try again.');
        return null;
    }
}

// Function to handle user logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user'); // Remove any other user-related data
    // Redirect to login page or home page
    window.location.href = '/index.html'; // Or your login page
}

// Search functionality (basic example, assuming you have a search form)
function initializeSearch() {
    const searchForm = document.getElementById('searchForm'); // Assuming a form with id 'searchForm'
    const searchInput = document.getElementById('searchInput'); // Assuming an input with id 'searchInput'
    const searchResultsContainer = document.getElementById('searchResults'); // Container for results

    if (searchForm && searchInput && searchResultsContainer) {
        searchForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const query = searchInput.value.trim();
            if (!query) {
                searchResultsContainer.innerHTML = '<p>Please enter a search term.</p>';
                return;
            }

            // Determine if searching for lost or found items (example: based on current page or a dropdown)
            // This is a placeholder - you'll need to adjust based on your actual UI
            const searchType = window.location.pathname.includes('lost.html') ? 'lost' : 'found';

            searchResultsContainer.innerHTML = '<p>Searching...</p>';
            const items = await apiRequest(`/api/posts/${searchType}?search=${encodeURIComponent(query)}`);

            if (items && items.length > 0) {
                let html = '<ul>';
                items.forEach(item => {
                    html += `<li>
                        <h5>${item.title}</h5>
                        <p>${item.description}</p>
                        <small>Location: ${item.location}</small>
                    </li>`;
                });
                html += '</ul>';
                searchResultsContainer.innerHTML = html;
            } else if (items) {
                searchResultsContainer.innerHTML = '<p>No items found matching your search.</p>';
            } else {
                searchResultsContainer.innerHTML = '<p>Search failed. Please try again later.</p>';
            }
        });
    }
}

// Report Lost/Found Item Form functionality
function initializeReportForm() {
    const reportForm = document.getElementById('reportItemForm'); // Assuming a form with id 'reportItemForm'

    if (reportForm) {
        reportForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const formData = new FormData(reportForm);

            // Example: Client-side validation (can be more extensive)
            const title = formData.get('title');
            if (!title || title.trim() === '') {
                alert('Please enter a title for the item.');
                return;
            }

            // The backend /api/posts endpoint handles image uploads via multer
            // and expects other fields like 'type', 'category', 'location', 'description'
            // Ensure your form has these input fields with correct 'name' attributes.

            const result = await apiRequest('/api/posts', 'POST', formData);

            if (result) {
                alert('Item reported successfully!');
                reportForm.reset();
                // Optionally, redirect or update UI
                // e.g., window.location.href = '/dashboard.html';
            } else {
                alert('Failed to report item. Please try again.');
            }
        });
    }
}


// DOMContentLoaded listener to initialize functionalities
document.addEventListener('DOMContentLoaded', () => {
    // Initialize search if relevant elements are on the page
    initializeSearch();

    // Initialize report form if relevant elements are on the page
    initializeReportForm();

    // Setup logout button if it exists
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', logout);
    }

    // Check authentication status and update UI (e.g., show/hide elements)
    // This is a basic example. You might want to fetch user profile, etc.
    const token = localStorage.getItem('token');
    if (token) {
        // User is logged in - update UI accordingly
        // e.g., show user-specific navigation, hide login/signup buttons
        console.log("User is logged in.");
        // You could add elements to show username, link to dashboard etc.
        // Example: document.getElementById('userSpecificContent').style.display = 'block';
    } else {
        // User is not logged in
        console.log("User is not logged in.");
        // Example: document.getElementById('loginSignupButtons').style.display = 'block';
    }

    // If Posts module exists (from post.js), initialize it
    if (typeof Posts !== 'undefined' && Posts.getRecentLostItems) {
        Posts.getRecentLostItems(); // For pages that display recent lost items
    }

    // If VisualSearchHandler exists (from visualSearch.js), initialize it
    // This is already handled by visualSearch.js itself with its own DOMContentLoaded listener.
    // No need to re-initialize here unless you change that structure.
});
