// filepath: c:\Users\sebas\OneDrive\Desktop\USM PROYECTO\sidebar\script_sidebar.js
document.querySelectorAll('.menu-item-dropdown .menu-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const parent = this.closest('.menu-item-dropdown');
        parent.classList.toggle('open');
    });
});

document.querySelector('.menu-btn').addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('collapsed');
});
