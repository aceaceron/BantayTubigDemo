document.addEventListener('DOMContentLoaded', () => {
    // --- Common Elements & Helper ---
    const jsFlashContainer = document.getElementById('js-flash-container');
    function showJsFlash(message, category = 'error') {
        jsFlashContainer.innerHTML = `<div class="flash-message ${category}">${message}</div>`;
    }

    // --- Check if we are in REGISTRATION mode ---
    const registrationForm = document.getElementById('registrationForm');
    if (registrationForm) {
        // --- Registration Logic ---
        const fullNameInput = document.getElementById('regFullName');
        const emailInput = document.getElementById('regEmail');
        const passwordInput = document.getElementById('regPassword');
        const confirmPasswordInput = document.getElementById('regConfirmPassword');
        const phoneInput = document.getElementById('regPhoneNumber');

        registrationForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            jsFlashContainer.innerHTML = ''; // Clear previous errors

            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;

            // --- Validation ---
            if (password.length < 6) {
                showJsFlash('Password must be at least 6 characters long.');
                return;
            }
            if (password !== confirmPassword) {
                showJsFlash('Passwords do not match.');
                return;
            }

             try {
                const roles = await (await fetch('/api/roles/setup')).json();
                const adminRole = roles.find(r => r.name === 'Administrator');
                if (!adminRole) {
                    throw new Error('Administrator role not found in the system.');
                }

                const userData = {
                    full_name: fullNameInput.value,
                    email: emailInput.value,
                    password: password,
                    phone_number: phoneInput.value,
                    role_id: adminRole.id
                };

                // Send data to the secure, one-time admin creation endpoint
                const response = await fetch('/api/users/setup/create_first_admin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });

                const data = await response.json();
                if (!response.ok) throw new Error(data.message);

                // --- Redirect to dashboard on success ---
                showJsFlash('Account created! Redirecting to the dashboard...', 'success');
                setTimeout(() => {
                    window.location.href = '/'; // Redirect to the main dashboard
                }, 1500);

            } catch (error) {
                showJsFlash(error.message || 'An unexpected error occurred.');
            }
        });
        // --- Phone Number Input Formatting ---
        phoneInput.addEventListener('focus', () => {
            if (phoneInput.value === '') {
                phoneInput.value = '+639';
            }
        });

        phoneInput.addEventListener('input', () => {
            let value = phoneInput.value;
            if (!value.startsWith('+639')) {
                value = '+639';
            }
            // Allow only numbers after the prefix and limit the total length to 13 characters
            const numericPart = value.substring(4).replace(/[^0-9]/g, '');
            phoneInput.value = '+639' + numericPart.substring(0, 9);
        });

        phoneInput.addEventListener('keydown', (e) => {
            // Prevent the user from deleting the prefix
            const selectionStart = e.target.selectionStart;
            if (selectionStart < 4 && (e.key === 'Backspace' || e.key === 'Delete')) {
                e.preventDefault();
            }
        });

    } else {
        // --- Login & Password Reset Logic ---
        const emailInput = document.getElementById('email');
        const forgotPasswordBtn = document.getElementById('forgotPasswordBtn');
        const loginForm = document.getElementById('loginForm');
        const verifyCodeForm = document.getElementById('verifyCodeForm');
        const setNewPasswordForm = document.getElementById('setNewPasswordForm');
        const verificationCodeInput = document.getElementById('verificationCode');
        const newPasswordInput = document.getElementById('newPassword');
        const confirmNewPasswordInput = document.getElementById('confirmNewPassword');
        let adminEmail = '';
        let resetToken = '';

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

        forgotPasswordBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            jsFlashContainer.innerHTML = '';
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

                loginForm.style.display = 'none';
                forgotPasswordBtn.style.display = 'none';
                verifyCodeForm.style.display = 'block';
            } catch (error) {
                showJsFlash(error.message);
                forgotPasswordBtn.textContent = 'Forgot Password?';
                forgotPasswordBtn.style.pointerEvents = 'auto';
            }
        });

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

                resetToken = data.reset_token;
                verifyCodeForm.style.display = 'none';
                setNewPasswordForm.style.display = 'block';
            } catch (error) {
                showJsFlash(error.message);
            }
        });

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

                showJsFlash(data.message + " Redirecting...", 'success');
                setTimeout(() => {
                    window.location.assign('/login');
                }, 3000);
            } catch (error) {
                showJsFlash(error.message);
            }
        });
    }
});