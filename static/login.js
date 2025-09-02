document.addEventListener('DOMContentLoaded', () => {
    const emailInput = document.getElementById('email');
    const forgotPasswordBtn = document.getElementById('forgotPasswordBtn');
    const loginForm = document.getElementById('loginForm');
    const verifyCodeForm = document.getElementById('verifyCodeForm');
    const verificationCodeInput = document.getElementById('verificationCode');
    const jsFlashContainer = document.getElementById('js-flash-container'); 
    const newPasswordInput = document.getElementById('newPassword');
    const confirmNewPasswordInput = document.getElementById('confirmNewPassword');
    /**
     * Helper function to display a flash-style message using JavaScript.
     * @param {string} message The error message to display.
     * @param {string} category The category (e.g., 'error').
     */
    function showJsFlash(message, category = 'error') {
        jsFlashContainer.innerHTML = `<div class="flash-message ${category}">${message}</div>`;
    }

    let adminEmail = '';

    // 1. Check if the typed email belongs to an admin
    emailInput.addEventListener('blur', async () => {
        const email = emailInput.value;
        if (!email) {
            forgotPasswordBtn.style.display = 'none';
            return;
        }
        try {
            const response = await fetch('/api/users/check-admin-status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await response.json();
            forgotPasswordBtn.style.display = data.is_admin ? 'inline' : 'none';
        } catch (error) {
            console.error('Error checking admin status:', error);
            forgotPasswordBtn.style.display = 'none';
        }
    });

     // 2. Handle "Forgot Password" button click
    forgotPasswordBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        jsFlashContainer.innerHTML = ''; // Clear previous errors
        adminEmail = emailInput.value;
        forgotPasswordBtn.textContent = 'Sending...';
        forgotPasswordBtn.style.pointerEvents = 'none';

        try {
            const response = await fetch('/api/users/send-reset-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: adminEmail })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message);

            // Switch to the verification code form
            loginForm.style.display = 'none';
            forgotPasswordBtn.style.display = 'none';
            verifyCodeForm.style.display = 'block';

        } catch (error) {
            showJsFlash(error.message);
            forgotPasswordBtn.textContent = 'Forgot Password?';
            forgotPasswordBtn.style.pointerEvents = 'auto';
        }
    });

    // 3. Handle verification code form submission
    verifyCodeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        jsFlashContainer.innerHTML = '';
        const code = verificationCodeInput.value;
        try {
            const response = await fetch('/api/users/verify-reset-code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: adminEmail, code })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message);

            // <<< FIX: On success, store the token and show the new password form >>>
            resetToken = data.reset_token;
            verifyCodeForm.style.display = 'none';
            setNewPasswordForm.style.display = 'block';

        } catch (error) {
            showJsFlash(error.message);
        }
    });

    // <<< 4. Handle the final "Set New Password" form submission >>>
    setNewPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        jsFlashContainer.innerHTML = '';
        const newPassword = newPasswordInput.value;
        const confirmPassword = confirmNewPasswordInput.value;

        if (newPassword.length < 6) {
            showJsFlash('Password must be at least 6 characters long.');
            return;
        }
        if (newPassword !== confirmPassword) {
            showJsFlash('Passwords do not match.');
            return;
        }

        try {
            const response = await fetch('/api/users/set-new-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: adminEmail,
                    token: resetToken,
                    new_password: newPassword
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.message);

            showJsFlash(data.message + " Redirecting to login...", 'success');
        
            // Wait 3 seconds before redirecting to give the user time to read the message.
            setTimeout(() => {
                window.location.assign('/login');
            }, 3000);

        } catch (error) {
            showJsFlash(error.message);
        }
    });
});