document.addEventListener('DOMContentLoaded', function(){
    const toggle = document.getElementById('themeToggle');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const saved = localStorage.getItem('theme');
    if(saved === 'dark' || (!saved && prefersDark)) document.body.classList.add('dark');

    toggle?.addEventListener('click', ()=>{
        document.body.classList.toggle('dark');
        localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
    });

    const avatarInputs = document.querySelectorAll('.avatar-input');

    document.querySelectorAll('.avatar-button').forEach(button => {
        button.addEventListener('click', () => {
            const postId = button.dataset.postId;
            const input = document.querySelector(`.avatar-input[data-post-id="${postId}"]`);
            input?.click();
        });
    });

    avatarInputs.forEach(input => {
        input.addEventListener('change', event => {
            const file = event.target.files?.[0];
            const postId = input.dataset.postId;
            if (!file || !postId) return;
            const reader = new FileReader();
            reader.onload = () => {
                const url = reader.result;
                document.querySelectorAll(`.avatar[data-post-id="${postId}"]`).forEach(img => {
                    img.src = url;
                });
                localStorage.setItem(`avatar-${postId}`, url);
                input.value = '';
            };
            reader.readAsDataURL(file);
        });
    });

    const loadSavedAvatars = () => {
        document.querySelectorAll('.avatar[data-post-id]').forEach(img => {
            const postId = img.dataset.postId;
            const saved = localStorage.getItem(`avatar-${postId}`);
            if (saved) img.src = saved;
        });
    };

    loadSavedAvatars();

    // Simple reveal on scroll
    const cards = document.querySelectorAll('.card');
    const io = new IntersectionObserver((entries)=>{
        entries.forEach(e=>{if(e.isIntersecting){e.target.style.transform='translateY(0)';e.target.style.opacity=1;io.unobserve(e.target)}}),{threshold:0.08}
    });
    cards.forEach(c=>{c.style.transform='translateY(8px)';c.style.opacity=0;io.observe(c)});

    // Localize UTC date/time to user's local browser timezone
    document.querySelectorAll('time.post-date').forEach(el => {
        let isoStr = el.getAttribute('datetime');
        if (isoStr) {
            // Append Z if there is no timezone specified in ISO format (since it is UTC in database)
            if (!isoStr.endsWith('Z') && !/[-+]\d{2}:\d{2}$/.test(isoStr)) {
                isoStr += 'Z';
            }
            const date = new Date(isoStr);
            if (!isNaN(date.getTime())) {
                const options = {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                };
                // If original text contains a colon (time), render local time as well
                if (el.textContent.includes(':')) {
                    options.hour = '2-digit';
                    options.minute = '2-digit';
                    options.hour12 = true;
                }
                el.textContent = date.toLocaleString(undefined, options);
            }
        }
    });
});