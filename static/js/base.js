document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.querySelector('.nav-toggler');
    const navList = document.getElementById('mobileMenu');
    navToggle.addEventListener('click', function() {
        navList.classList.toggle('open');
    });
});