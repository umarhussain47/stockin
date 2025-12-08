// --- Global Helper: Authenticated Fetch ---
const apiFetch = (url, options = {}) => {
    const token = localStorage.getItem('access_token');
    
    // 1. Ensure headers exist or create them
    options.headers = options.headers || {};
    
    // 2. Attach the JWT Bearer token to all protected requests
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // 3. Ensure Content-Type is set for JSON bodies
    if (!options.headers['Content-Type']) {
        options.headers['Content-Type'] = 'application/json';
    }
    
    return fetch(url, options).then(response => {
        // 4. If 401 Unauthorized, clear token and redirect to login
        if (response.status === 401) {
            console.error("Unauthorized: Token is invalid or expired.");
            localStorage.removeItem('access_token');
            
            // Redirect only if we are not already on an auth page
            const currentPath = window.location.pathname;
            if (currentPath !== '/login.html' && currentPath !== '/signup.html') {
                 window.location.href = '/login.html';
            }
        }
        return response;
    });
};


document.addEventListener('DOMContentLoaded', () => {
    // --- 1. DOM Elements (Used on multiple pages) ---
    const chatBox = document.getElementById('chatBox');
    const askBtn = document.getElementById('askBtn');
    const companyInput = document.getElementById('company');
    const questionInput = document.getElementById('question');
    const tabSelect = document.getElementById('tab');
    
    // Auth elements
    const loginBtn = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const messageElement = document.getElementById('message');


    // --- 2. Authorization Guard: Protect main app pages ---
    const protectedPaths = ['/research.html', '/recents.html', '/favourites.html'];
    const currentPath = window.location.pathname;

    if (protectedPaths.includes(currentPath)) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            console.log("No token found, redirecting to login.");
            window.location.href = '/login.html';
            return; // Stop execution on protected pages if unauthorized
        }
    }


    // --- 3. Chat Helper Function ---
    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = `msg ${type}`;
        div.textContent = text;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }


    // --- 4. Existing Research Page Logic (UPDATED to use apiFetch) ---
    if (askBtn) {
        askBtn.addEventListener('click', async () => {
            const company = companyInput.value.trim();
            const question = questionInput.value.trim();
            const tab = tabSelect.value;

            if (!company || !question) return alert("Please enter both company and question.");

            addMessage(`(${company} - ${tab}) ${question}`, 'user');
            questionInput.value = '';

            const typing = document.createElement('div');
            typing.className = 'msg bot';
            typing.innerHTML = '<span class="typing">Thinking...</span>';
            chatBox.appendChild(typing);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                // *** UPDATED: Using apiFetch to automatically attach the JWT ***
                const res = await apiFetch('/api/research', {
                    method: 'POST',
                    body: JSON.stringify({ company, tab, question })
                });

                if (res.status === 401) {
                    // apiFetch handles the redirect, but stop here
                    chatBox.removeChild(typing);
                    return;
                }
                
                const data = await res.json();
                chatBox.removeChild(typing);
                addMessage(data.answer || "No response received.", 'bot');
            } catch (err) {
                chatBox.removeChild(typing);
                addMessage("Error fetching response.", 'bot');
            }
        });
    }

    // --- 5. Login Page Logic ---
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            const email = emailInput.value;
            const password = passwordInput.value;
            
            if (!email || !password) {
                messageElement.textContent = 'Please enter both email and password.';
                return;
            }

            messageElement.textContent = 'Logging in...';

            fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            })
            .then(res => res.json().then(data => ({ status: res.status, body: data })))
            .then(({ status, body }) => {
                if (status === 200) {
                    // Success: Store the JWT and redirect
                    localStorage.setItem('access_token', body.access_token);
                    messageElement.style.color = 'green';
                    messageElement.textContent = 'Login successful! Redirecting...';
                    window.location.href = '/research.html';
                } else {
                    // Failure: Display error
                    messageElement.style.color = 'red';
                    messageElement.textContent = body.error || 'Login failed. Check your credentials.';
                }
            })
            .catch(err => {
                messageElement.style.color = 'red';
                messageElement.textContent = 'Network error during login.';
            });
        });
    }

    // --- 6. Signup Page Logic ---
    if (signupBtn) {
        signupBtn.addEventListener('click', () => {
            const email = emailInput.value;
            const password = passwordInput.value;

            if (!email || !password) {
                messageElement.textContent = 'Please enter both email and password.';
                return;
            }

            messageElement.textContent = 'Signing up...';

            fetch('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            })
            .then(res => res.json().then(data => ({ status: res.status, body: data })))
            .then(({ status, body }) => {
                if (status === 200) {
                    // Success: Supabase requires email verification by default
                    messageElement.style.color = 'green';
                    messageElement.textContent = body.message || 'Signup successful! Please check your email to confirm your account.';
                    // No redirect here, user must verify email first
                } else {
                    // Failure: Display error
                    messageElement.style.color = 'red';
                    messageElement.textContent = body.error || 'Signup failed.';
                }
            })
            .catch(err => {
                messageElement.style.color = 'red';
                messageElement.textContent = 'Network error during signup.';
            });
        });
    }
});