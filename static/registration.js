


document.addEventListener('DOMContentLoaded', function() {
    const togglePassword = document.querySelector('.toggle-password');
    togglePassword.addEventListener('click', function () {
        const passwordInput = document.getElementById('password');
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            this.innerHTML = '&#128584;'; 
        } else {
            passwordInput.type = 'password';
            this.innerHTML = '&#128065;'; 
        }
    });
});


document.addEventListener('DOMContentLoaded', function() {
    const flashes = document.querySelectorAll('.flashes li');
    let authCodeError = false;
    flashes.forEach(flash => {
        if (flash.textContent.includes('Invalid auth code')) {
            authCodeError = true;
        }
    });
    var button = document.getElementById('register');
    button.addEventListener('click', function() {
        const modal = document.getElementById('authModal'); 
        const span = document.getElementsByClassName('close')[0];
        modal.style.display = 'block';
        span.onclick = function() {
            modal.style.display = 'none';
        }
        window.onclick = function(event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        });

});
