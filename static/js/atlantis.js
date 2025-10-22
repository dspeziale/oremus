/**
 * Atlantis 2.0 Dashboard - JavaScript Functions
 * Dashboard Liturgia
 */

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar
    initSidebar();

    // Initialize tooltips
    initTooltips();

    // Initialize animations
    initAnimations();

    // Initialize search
    initSearch();

    // Initialize notifications
    initNotifications();
});

/**
 * Sidebar Functions
 */
function initSidebar() {
    // Toggle sidebar on mobile
    const sidebarToggler = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('.sidebar');

    if (sidebarToggler) {
        sidebarToggler.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }

    // Minimize sidebar on desktop
    const minimizeBtn = document.querySelector('.btn-minimize');
    const mainPanel = document.querySelector('.main-panel');

    if (minimizeBtn) {
        minimizeBtn.addEventListener('click', function() {
            sidebar.classList.toggle('minimized');
            mainPanel.classList.toggle('expanded');

            // Save state to localStorage
            const isMinimized = sidebar.classList.contains('minimized');
            localStorage.setItem('sidebarMinimized', isMinimized);
        });
    }

    // Restore sidebar state
    const isMinimized = localStorage.getItem('sidebarMinimized') === 'true';
    if (isMinimized) {
        sidebar.classList.add('minimized');
        mainPanel.classList.add('expanded');
    }

    // Handle dropdown menus
    const dropdownToggles = document.querySelectorAll('[data-bs-toggle="collapse"]');
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.classList.toggle('show');
                this.setAttribute('aria-expanded', target.classList.contains('show'));
            }
        });
    });
}

/**
 * Initialize Tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize Animations
 */
function initAnimations() {
    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe fade-in elements
    document.querySelectorAll('.fade-in').forEach(el => {
        observer.observe(el);
    });

    // Animate counters
    animateCounters();
}

/**
 * Animate Counters
 */
function animateCounters() {
    const counters = document.querySelectorAll('.stat-value');

    counters.forEach(counter => {
        const target = parseInt(counter.innerText);
        const increment = target / 50;
        let current = 0;

        const updateCounter = () => {
            current += increment;
            if (current < target) {
                counter.innerText = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.innerText = target;
            }
        };

        // Start animation when element is visible
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                updateCounter();
                observer.disconnect();
            }
        });

        observer.observe(counter);
    });
}

/**
 * Initialize Search
 */
function initSearch() {
    const searchDropdown = document.getElementById('searchDropdown');

    if (searchDropdown) {
        searchDropdown.addEventListener('click', function(e) {
            e.preventDefault();
            showSearchModal();
        });
    }
}

/**
 * Show Search Modal
 */
function showSearchModal() {
    // Create search modal if it doesn't exist
    let searchModal = document.getElementById('searchModal');

    if (!searchModal) {
        searchModal = document.createElement('div');
        searchModal.className = 'modal fade';
        searchModal.id = 'searchModal';
        searchModal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-search me-2"></i>Ricerca Globale
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="input-group mb-3">
                            <input type="text" class="form-control" id="globalSearchInput"
                                   placeholder="Cerca date, santi, preghiere...">
                            <button class="btn btn-primary" onclick="performSearch()">
                                <i class="fas fa-search"></i> Cerca
                            </button>
                        </div>
                        <div id="searchResults"></div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(searchModal);
    }

    const modal = new bootstrap.Modal(searchModal);
    modal.show();

    // Focus on search input
    setTimeout(() => {
        document.getElementById('globalSearchInput').focus();
    }, 500);
}

/**
 * Perform Search
 */
function performSearch() {
    const searchInput = document.getElementById('globalSearchInput');
    const searchResults = document.getElementById('searchResults');
    const query = searchInput.value.trim();

    if (query.length < 2) {
        searchResults.innerHTML = `
            <div class="alert alert-warning">
                Inserisci almeno 2 caratteri per la ricerca
            </div>
        `;
        return;
    }

    // Show loading
    searchResults.innerHTML = `
        <div class="text-center py-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Ricerca in corso...</span>
            </div>
        </div>
    `;

    // Simulate search (in real app, this would be an API call)
    setTimeout(() => {
        searchResults.innerHTML = `
            <div class="list-group">
                <a href="#" class="list-group-item list-group-item-action">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">Lunedì 1 Ottobre 2025</h6>
                        <small class="text-muted">Data</small>
                    </div>
                    <p class="mb-1">Lodi e Vespri disponibili</p>
                </a>
                <a href="#" class="list-group-item list-group-item-action">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">San Francesco d'Assisi</h6>
                        <small class="text-muted">Santo</small>
                    </div>
                    <p class="mb-1">4 Ottobre - Patrono d'Italia</p>
                </a>
            </div>
        `;
    }, 1000);
}

/**
 * Initialize Notifications
 */
function initNotifications() {
    // Check for new notifications periodically
    setInterval(checkNotifications, 60000); // Every minute
}

/**
 * Check Notifications
 */
function checkNotifications() {
    // In real app, this would be an API call
    console.log('Checking for new notifications...');
}

/**
 * Show Date Picker
 */
function showDatePicker() {
    // Fetch available dates
    fetch('/api/search-dates')
        .then(response => response.json())
        .then(dates => {
            showDatePickerModal(dates);
        })
        .catch(error => {
            console.error('Error fetching dates:', error);
            alert('Errore nel caricamento delle date');
        });
}

/**
 * Show Date Picker Modal
 */
function showDatePickerModal(dates) {
    let datePickerModal = document.getElementById('datePickerModal');

    if (!datePickerModal) {
        datePickerModal = document.createElement('div');
        datePickerModal.className = 'modal fade';
        datePickerModal.id = 'datePickerModal';
        document.body.appendChild(datePickerModal);
    }

    // Build options
    let optionsHtml = '';
    dates.forEach(date => {
        optionsHtml += `
            <option value="${date.value}">${date.label}</option>
        `;
    });

    datePickerModal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-gradient-primary text-white">
                    <h5 class="modal-title">
                        <i class="fas fa-calendar-day me-2"></i>Seleziona Data
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="dateSelect" class="form-label">Scegli una data:</label>
                        <select class="form-select" id="dateSelect">
                            ${optionsHtml}
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annulla</button>
                    <button type="button" class="btn btn-primary" onclick="goToSelectedDate()">
                        <i class="fas fa-arrow-right me-2"></i>Vai alla Data
                    </button>
                </div>
            </div>
        </div>
    `;

    const modal = new bootstrap.Modal(datePickerModal);
    modal.show();
}

/**
 * Go to Selected Date
 */
function goToSelectedDate() {
    const dateSelect = document.getElementById('dateSelect');
    const selectedDate = dateSelect.value;

    if (selectedDate) {
        window.location.href = `/giorno/${selectedDate}`;
    }
}

/**
 * Export Data
 */
function exportData(format) {
    const url = `/api/export?format=${format}`;
    window.open(url, '_blank');
}

/**
 * Print Page
 */
function printPage() {
    window.print();
}

/**
 * Toggle Dark Mode
 */
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
}

/**
 * Load Theme Preference
 */
function loadThemePreference() {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    }
}

// Load theme preference on page load
loadThemePreference();

/**
 * Utility Functions
 */

// Format date
function formatDate(dateString) {
    const options = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    return new Date(dateString).toLocaleDateString('it-IT', options);
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    toastContainer.appendChild(toastElement.firstElementChild);

    const toast = new bootstrap.Toast(toastElement.firstElementChild);
    toast.show();
}

// Smooth scroll to element
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}