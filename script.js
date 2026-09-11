document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.querySelector('form');
    if (!contactForm) return;

    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Adjust input selectors to match your HTML input names/ids
        const name = contactForm.querySelector('[name="name"]')?.value || contactForm.querySelector('#name')?.value;
        const phone = contactForm.querySelector('[name="phone"]')?.value || contactForm.querySelector('#phone')?.value;
        const email = contactForm.querySelector('[name="email"]')?.value || contactForm.querySelector('#email')?.value;

        const submitBtn = contactForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn ? submitBtn.innerText : 'Send';

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerText = 'Sending...';
        }

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
                alert(result.message || 'Message sent successfully!');
                contactForm.reset();
            } else {
                alert(result.message || 'Failed to submit form.');
            }
        } catch (error) {
            console.error('Submission error:', error);
            alert('Something went wrong. Please try again later.');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerText = originalBtnText;
            }
        }
    });
});