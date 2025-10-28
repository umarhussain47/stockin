document.getElementById('askBtn').addEventListener('click', async ()=>{
    const company = document.getElementById('company').value.trim();
    const tab = document.getElementById('tab').value;
    const question = document.getElementById('question').value.trim();
    const out = document.getElementById('answerSection');
    out.innerText = 'Thinking...';
    const res = await fetch('/api/research', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({company, tab, question})
    });
    if(res.ok){
        const j = await res.json();
        out.innerText = j.answer;
    } else {
        out.innerText = 'Error: ' + (await res.text());
    }
});
