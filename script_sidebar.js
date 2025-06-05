// filepath: c:\Users\sebas\OneDrive\Desktop\USM PROYECTO\sidebar\script_sidebar.js
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const menuBtn = document.querySelector('.menu-btn');
    const dropdownItems = document.querySelectorAll('.menu-item-dropdown');
    const menuLinks = document.querySelectorAll('.menu-link, .sub-menu-link');
    const mainIframe = document.getElementById('main-iframe');

    // Toggle sidebar
    if (menuBtn) {
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent event from bubbling
            sidebar.classList.toggle('collapsed');
            
            // Close all dropdowns when collapsing
            if (sidebar.classList.contains('collapsed')) {
                dropdownItems.forEach(item => {
                    item.classList.remove('open');
                });
            }
        });
    }

    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
                sidebar.classList.add('collapsed');
            }
        }
    });
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('collapsed');
        }
    });

    // Handle dropdown menus
    dropdownItems.forEach(item => {
        const link = item.querySelector('.menu-link');
        if (link) {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                // Don't toggle dropdown if sidebar is collapsed
                if (sidebar.classList.contains('collapsed')) {
                    return;
                }
                
                // Close other dropdowns
                dropdownItems.forEach(otherItem => {
                    if (otherItem !== item) {
                        otherItem.classList.remove('open');
                    }
                });
                
                // Toggle current dropdown
                item.classList.toggle('open');
            });
        }
    });

    // Handle page navigation
    menuLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            if (!link.closest('.menu-item-dropdown') || link.classList.contains('sub-menu-link')) {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                if (page) {
                    // Remove active class from all links
                    menuLinks.forEach(l => l.classList.remove('active'));
                    // Add active class to clicked link
                    link.classList.add('active');
                    
                    // Navigate to the page
                    window.location.href = page;
                }
            }
        });
    });

    // Handle logout
    const logoutBtn = document.querySelector('.user-icon');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
});

// Función para manejar el cierre de sesión
function handleLogout() {
    // Eliminar datos de sesión
    localStorage.removeItem('authToken');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    
    // Redirigir a la página de inicio
    window.location.href = 'index.html';
}
