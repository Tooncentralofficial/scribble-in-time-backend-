// Admin Dashboard JavaScript
// This file contains all the interactive functionality for the admin dashboard

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize navigation
    initNavigation();
    
    // Initialize modals
    initModals();
    
    // Initialize file uploads
    initFileUploads();
    
    // Initialize real-time updates
    initRealTimeUpdates();
});

// Initialize tooltips using Tippy.js
function initTooltips() {
    // Check if Tippy is loaded
    if (typeof tippy !== 'undefined') {
        tippy('[data-tippy-content]', {
            placement: 'top',
            animation: 'scale',
            theme: 'light',
            arrow: true,
            delay: [100, 0]
        });
    }
}

// Handle navigation between dashboard sections
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    
    // Set first nav item as active by default if none is active
    if (!document.querySelector('.nav-link.active') && navLinks.length > 0) {
        navLinks[0].classList.add('active');
        const target = navLinks[0].getAttribute('data-page');
        showSection(target);
    }
    
    // Add click event listeners to nav links
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(navLink => navLink.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show corresponding section
            const target = this.getAttribute('data-page');
            showSection(target);
            
            // Update URL without reloading the page
            history.pushState({}, '', `?page=${target}`);
        });
    });
    
    // Handle browser back/forward buttons
    window.addEventListener('popstate', function() {
        const urlParams = new URLSearchParams(window.location.search);
        const page = urlParams.get('page') || 'dashboard';
        showSection(page);
        
        // Update active nav link
        navLinks.forEach(link => {
            if (link.getAttribute('data-page') === page) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    });
}

// Show a specific section and hide others
function showSection(sectionId) {
    // Hide all content sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.add('hidden');
    });
    
    // Show the selected section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.remove('hidden');
        
        // Load section-specific content if needed
        switch(sectionId) {
            case 'conversations':
                loadConversations();
                break;
            case 'documents':
                loadDocuments();
                break;
            case 'settings':
                loadSettings();
                break;
            default:
                loadDashboardStats();
        }
    }
}

// Initialize modal dialogs
function initModals() {
    // Close modals when clicking the close button or outside the modal
    document.querySelectorAll('.modal').forEach(modal => {
        const closeButton = modal.querySelector('.modal-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                modal.classList.add('hidden');
            });
        }
        
        // Close when clicking outside the modal content
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    });
    
    // Close modals with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal').forEach(modal => {
                modal.classList.add('hidden');
            });
        }
    });
}

// Initialize file upload functionality
function initFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        // Show file name when a file is selected
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'No file selected';
            const fileNameElement = this.nextElementSibling;
            
            if (fileNameElement && fileNameElement.classList.contains('file-name')) {
                fileNameElement.textContent = fileName;
            }
        });
        
        // Handle drag and drop
        const dropZone = input.closest('.file-upload-dropzone');
        if (dropZone) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, preventDefaults, false);
            });
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, unhighlight, false);
            });
            
            dropZone.addEventListener('drop', handleDrop, false);
        }
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        this.classList.add('border-indigo-500', 'bg-indigo-50');
    }
    
    function unhighlight() {
        this.classList.remove('border-indigo-500', 'bg-indigo-50');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            const input = this.querySelector('input[type="file"]');
            if (input) {
                input.files = files;
                const event = new Event('change');
                input.dispatchEvent(event);
            }
        }
    }
}

// Initialize real-time updates using polling
function initRealTimeUpdates() {
    // Use polling for updates
    pollForUpdates();
}

// Poll for updates
function pollForUpdates() {
    // Poll every 30 seconds
    setInterval(() => {
        // Check for new messages
        fetch('/api/admin/updates/')
            .then(response => response.json())
            .then(data => {
                if (data.new_messages > 0) {
                    showNotification('New Messages', `You have ${data.new_messages} new messages`, 'info');
                    // Refresh conversations if on the conversations page
                    if (window.location.pathname.includes('conversations')) {
                        loadConversations();
                    }
                }
            })
            .catch(error => console.error('Error checking for updates:', error));
    }, 30000); // 30 seconds
}

// Show a notification to the user
function showNotification(title, message, level = 'info') {
    // Check if notification container exists, if not create it
    let container = document.getElementById('notifications-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notifications-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2 w-80';
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    const levels = {
        'success': 'bg-green-100 border-green-400 text-green-700',
        'error': 'bg-red-100 border-red-400 text-red-700',
        'warning': 'bg-yellow-100 border-yellow-400 text-yellow-700',
        'info': 'bg-blue-100 border-blue-400 text-blue-700'
    };
    
    notification.className = `border-l-4 p-4 ${levels[level] || levels['info']} shadow-lg rounded-r`;
    notification.role = 'alert';
    
    notification.innerHTML = `
        <div class="flex">
            <div class="flex-shrink-0">
                ${level === 'success' ? '<i class="fas fa-check-circle"></i>' : ''}
                ${level === 'error' ? '<i class="fas fa-exclamation-circle"></i>' : ''}
                ${level === 'warning' ? '<i class="fas fa-exclamation-triangle"></i>' : ''}
                ${!['success', 'error', 'warning'].includes(level) ? '<i class="fas fa-info-circle"></i>' : ''}
            </div>
            <div class="ml-3">
                <p class="font-bold">${title}</p>
                <p class="text-sm">${message}</p>
            </div>
            <div class="ml-auto pl-3">
                <button class="text-gray-500 hover:text-gray-700" onclick="this.parentElement.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
    
    // Add notification to container
    container.appendChild(notification);
    
    // Auto-remove notification after 5 seconds
    setTimeout(() => {
        notification.classList.add('opacity-0', 'transition-opacity', 'duration-300');
        setTimeout(() => {
            notification.remove();
            
            // Remove container if no notifications left
            if (container.children.length === 0) {
                container.remove();
            }
        }, 300);
    }, 5000);
}

// Export functions to global scope for use in HTML
window.showNotification = showNotification;
