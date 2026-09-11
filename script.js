document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.getElementById('contact-form');
    const statusText = document.getElementById('form-status');
    const submitBtn = document.getElementById('submit-btn');

    if (!contactForm) return;

    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const name = document.getElementById('name').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const email = document.getElementById('email').value.trim();

        submitBtn.disabled = true;
        submitBtn.innerText = 'Sending...';
        if (statusText) statusText.innerText = '';

        try {
            const response = await fetch('https://portfolio-backend-sr55.onrender.com/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, phone, email })
            });

            const result = await response.json();

            if (response.ok) {
                if (statusText) {
                    statusText.style.color = '#4ade80';
                    statusText.innerText = result.message || 'Message sent successfully!';
                }
                contactForm.reset();
            } else {
                if (statusText) {
                    statusText.style.color = '#f87171';
                    statusText.innerText = result.message || 'Failed to submit form.';
                }
            }
        } catch (error) {
            console.error('Submission error:', error);
            if (statusText) {
                statusText.style.color = '#f87171';
                statusText.innerText = 'Could not connect to the backend server.';
            }
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = 'Send Message';
        }
    });
});