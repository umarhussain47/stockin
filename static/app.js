document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chatBox');
    const askBtn = document.getElementById('askBtn');
    const companyInput = document.getElementById('company');
    const questionInput = document.getElementById('question');
    const tabSelect = document.getElementById('tab');

    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = `msg ${type}`;
        div.textContent = text;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

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
            // Use authFetch instead of regular fetch
            const res = await authFetch('/api/research', {
                method: 'POST',
                body: JSON.stringify({ company, tab, question })
            });
            
            // authFetch returns null and redirects on 401
            if (!res) {
                chatBox.removeChild(typing);
                return;
            }
            
            const data = await res.json();
            chatBox.removeChild(typing);
            addMessage(data.answer || "No response received.", 'bot');
        } catch (err) {
            chatBox.removeChild(typing);
            addMessage("Error fetching response.", 'bot');
            console.error('Research error:', err);
        }
    });
});