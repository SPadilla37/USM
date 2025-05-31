// filepath: c:\Users\sebas\OneDrive\Desktop\USM PROYECTO\sidebar\script_sidebar.js
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const menuBtn = document.querySelector('.menu-btn');
    const dropdownItems = document.querySelectorAll('.menu-item-dropdown');
    const menuLinks = document.querySelectorAll('.menu-link, .sub-menu-link');
    const mainIframe = document.getElementById('main-iframe');

    // Toggle sidebar
    menuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        
        // Close all dropdowns when collapsing
        if (sidebar.classList.contains('collapsed')) {
            dropdownItems.forEach(item => {
                item.classList.remove('open');
            });
        }
    });

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
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Close other dropdowns
            dropdownItems.forEach(otherItem => {
                if (otherItem !== item) {
                    otherItem.classList.remove('open');
                }
            });
            
            // Toggle current dropdown
            item.classList.toggle('open');
        });
    });

    // Handle page navigation
    menuLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            if (!link.closest('.menu-item-dropdown') || link.classList.contains('sub-menu-link')) {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                if (page) {
                    mainIframe.src = page;
                    
                    // Remove active class from all links
                    menuLinks.forEach(l => l.classList.remove('active'));
                    // Add active class to clicked link
                    link.classList.add('active');
                }
            }
        });
    });
});
