document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss Flash Messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Form select role interaction
    const roleSelect = document.getElementById('roleSelect');
    const passwordContainer = document.getElementById('passwordFieldContainer');
    if (roleSelect && passwordContainer) {
        roleSelect.addEventListener('change', function() {
            if (this.value === 'Admin' || this.value === 'Founder') {
                passwordContainer.style.display = 'block';
            } else {
                passwordContainer.style.display = 'none';
            }
        });
        
        // Initial state
        if (roleSelect.value === 'Admin' || roleSelect.value === 'Founder') {
            passwordContainer.style.display = 'block';
        } else {
            passwordContainer.style.display = 'none';
        }
    }
});
