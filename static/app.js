// document.getElementById('askBtn').addEventListener('click', async ()=>{
//     const company = document.getElementById('company').value.trim();
//     const tab = document.getElementById('tab').value;
//     const question = document.getElementById('question').value.trim();
//     const out = document.getElementById('answerSection');
//     out.innerText = 'Thinking...';
//     const res = await fetch('/api/research', {
//         method: 'POST',
//         headers: {'Content-Type':'application/json'},
//         body: JSON.stringify({company, tab, question})
//     });
//     if(res.ok){
//         const j = await res.json();
//         out.innerText = j.answer;
//     } else {
//         out.innerText = 'Error: ' + (await res.text());
//     }
// });

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
            const res = await fetch('/api/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company, tab, question })
            });
            const data = await res.json();
            chatBox.removeChild(typing);
            addMessage(data.answer || "No response received.", 'bot');
        } catch (err) {
            chatBox.removeChild(typing);
            addMessage("Error fetching response.", 'bot');
        }
    });
});

