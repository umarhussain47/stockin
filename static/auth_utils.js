// auth-utils.js - Reusable auth utilities for all pages

// Check if user is authenticated, redirect to login if not

function requireAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
        return null;
    }
    return token;
}

// Get auth headers for API requests
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Logout function
function logout() {
    const token = localStorage.getItem('access_token');
    
    // Call logout API
    fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    }).finally(() => {
        // Clear local storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_email');
        localStorage.removeItem('user_id');
        
        // Redirect to login
        window.location.href = '/login.html';
    });
}

// Add logout button to nav (call this on page load)
function addLogoutButton() {
    const nav = document.querySelector('.nav');
    if (nav) {
        const userEmail = localStorage.getItem('user_email');
        const logoutBtn = document.createElement('a');
        logoutBtn.href = '#';
        logoutBtn.textContent = userEmail ? `Logout (${userEmail})` : 'Logout';
        logoutBtn.style.marginLeft = 'auto';
        logoutBtn.onclick = (e) => {
            e.preventDefault();
            logout();
        };
        nav.appendChild(logoutBtn);
    }
}

// Initialize auth on protected pages
function initAuth() {
    requireAuth();
    addLogoutButton();
}

// Handle 401 responses globally
async function authFetch(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            ...getAuthHeaders()
        }
    });
    
    if (response.status === 401) {
        // Token expired or invalid, redirect to login
        localStorage.clear();
        window.location.href = '/login.html';
        return null;
    }
    
    return response;
}