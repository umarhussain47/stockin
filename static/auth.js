// auth.js - Handle login and signup

// Check if user is already logged in
function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (token) {
        // Redirect to research page if already logged in
        window.location.href = '/research.html';
    }
}

// Show error message
function showError(message) {
    const errorMsg = document.getElementById('errorMsg');
    errorMsg.textContent = message;
    errorMsg.classList.add('show');
    
    setTimeout(() => {
        errorMsg.classList.remove('show');
    }, 5000);
}

// Show success message
function showSuccess(message) {
    const successMsg = document.getElementById('successMsg');
    if (successMsg) {
        successMsg.textContent = message;
        successMsg.classList.add('show');
    }
}

// Login Form Handler
if (document.getElementById('loginForm')) {
    checkAuth(); // Redirect if already logged in
    
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const loginBtn = document.getElementById('loginBtn');
        
        // Disable button and show loading
        loginBtn.disabled = true;
        loginBtn.textContent = 'Logging in...';
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Store token and user info
                localStorage.setItem('access_token', data.session.access_token);
                localStorage.setItem('user_email', data.session.user.email);
                localStorage.setItem('user_id', data.session.user.id);
                
                // Redirect to research page
                window.location.href = '/research.html';
            } else {
                showError(data.error || 'Login failed. Please try again.');
                loginBtn.disabled = false;
                loginBtn.textContent = 'Login';
            }
        } catch (error) {
            showError('Network error. Please try again.');
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login';
        }
    });
}

// Signup Form Handler
if (document.getElementById('signupForm')) {
    checkAuth(); // Redirect if already logged in
    
    document.getElementById('signupForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const signupBtn = document.getElementById('signupBtn');
        
        // Validate passwords match
        if (password !== confirmPassword) {
            showError('Passwords do not match');
            return;
        }
        
        // Validate password length
        if (password.length < 6) {
            showError('Password must be at least 6 characters');
            return;
        }
        
        // Disable button and show loading
        signupBtn.disabled = true;
        signupBtn.textContent = 'Creating account...';
        
        try {
            const response = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Check if email verification is required
                if (data.requires_verification) {
                    // Show message and redirect to login
                    showSuccess('Account created! Please check your email to verify, then login.');
                    
                    setTimeout(() => {
                        window.location.href = '/login.html';
                    }, 3000);
                } else {
                    // Auto-login enabled, store session and redirect
                    showSuccess('Account created! Redirecting...');
                    
                    localStorage.setItem('access_token', data.session.access_token);
                    localStorage.setItem('user_email', data.session.user.email);
                    localStorage.setItem('user_id', data.session.user.id);
                    
                    setTimeout(() => {
                        window.location.href = '/research.html';
                    }, 2000);
                }
            } else {
                showError(data.error || 'Signup failed. Please try again.');
                signupBtn.disabled = false;
                signupBtn.textContent = 'Sign Up';
            }
        } catch (error) {
            showError('Network error. Please try again.');
            signupBtn.disabled = false;
            signupBtn.textContent = 'Sign Up';
        }
    });
}