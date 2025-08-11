/**
 * GourmetGuide - JavaScript principal
 * Fonctionnalités communes et utilitaires
 */

// Configuration globale
const GourmetGuide = {
    config: {
        apiBaseUrl: '/api/',
        mapOptions: {
            center: { lat: 6.1319, lng: 1.2228 }, // Lomé, Togo
            zoom: 13,
            styles: [] // Styles de carte personnalisés
        }
    },
    
    // Utilitaires
    utils: {
        // Formatage de la monnaie
        formatCurrency: function(amount) {
            return new Intl.NumberFormat('fr-TG', {
                style: 'currency',
                currency: 'XOF'
            }).format(amount);
        },
        
        // Formatage de la date
        formatDate: function(date) {
            return new Intl.DateTimeFormat('fr-TG', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(new Date(date));
        },
        
        // Debounce pour les recherches
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Validation d'email
        isValidEmail: function(email) {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(email);
        },
        
        // Validation de téléphone togolais
        isValidPhone: function(phone) {
            const re = /^(\+228)?[0-9]{8}$/;
            return re.test(phone.replace(/\s/g, ''));
        }
    },
    
    // Gestion des notifications
    notifications: {
        show: function(message, type = 'info', duration = 5000) {
            const toastHtml = `
                <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">
                            <i class="fas fa-${this.getIcon(type)} me-2"></i>${message}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>
            `;
            
            const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
            toastContainer.insertAdjacentHTML('beforeend', toastHtml);
            
            const toastElement = toastContainer.lastElementChild;
            const toast = new bootstrap.Toast(toastElement, { delay: duration });
            toast.show();
            
            // Supprimer automatiquement après affichage
            toastElement.addEventListener('hidden.bs.toast', () => {
                toastElement.remove();
            });
        },
        
        getIcon: function(type) {
            const icons = {
                'success': 'check-circle',
                'error': 'exclamation-triangle',
                'warning': 'exclamation-circle',
                'info': 'info-circle'
            };
            return icons[type] || 'info-circle';
        },
        
        createToastContainer: function() {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
            return container;
        }
    },
    
    // Gestion du panier
    cart: {
        addItem: function(itemId, quantity = 1) {
            return fetch('/api/orders/cart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    item_id: itemId,
                    quantity: quantity
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.updateCartCount();
                    GourmetGuide.notifications.show('Article ajouté au panier', 'success');
                } else {
                    GourmetGuide.notifications.show(data.error || 'Erreur lors de l\'ajout', 'error');
                }
                return data;
            });
        },
        
        updateCartCount: function() {
            fetch('/api/orders/cart/')
                .then(response => response.json())
                .then(data => {
                    const countElement = document.getElementById('cart-count');
                    if (countElement) {
                        countElement.textContent = data.total_items || 0;
                        countElement.style.display = data.total_items > 0 ? 'inline' : 'none';
                    }
                });
        },
        
        getCsrfToken: function() {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        }
    },
    
    // Gestion de la géolocalisation
    location: {
        getCurrentPosition: function() {
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error('Géolocalisation non supportée'));
                    return;
                }
                
                navigator.geolocation.getCurrentPosition(
                    position => resolve(position),
                    error => reject(error),
                    {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 300000 // 5 minutes
                    }
                );
            });
        },
        
        calculateDistance: function(lat1, lng1, lat2, lng2) {
            const R = 6371; // Rayon de la Terre en km
            const dLat = this.deg2rad(lat2 - lat1);
            const dLng = this.deg2rad(lng2 - lng1);
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                     Math.cos(this.deg2rad(lat1)) * Math.cos(this.deg2rad(lat2)) *
                     Math.sin(dLng/2) * Math.sin(dLng/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return R * c;
        },
        
        deg2rad: function(deg) {
            return deg * (Math.PI/180);
        }
    },
    
    // Gestion des recherches
    search: {
        init: function() {
            const searchInputs = document.querySelectorAll('[data-search]');
            searchInputs.forEach(input => {
                input.addEventListener('input', 
                    GourmetGuide.utils.debounce((e) => {
                        this.performSearch(e.target.value, e.target.dataset.search);
                    }, 300)
                );
            });
        },
        
        performSearch: function(query, type) {
            if (query.length < 2) return;
            
            fetch(`/api/core/search/?q=${encodeURIComponent(query)}&type=${type}`)
                .then(response => response.json())
                .then(data => {
                    this.displayResults(data, type);
                })
                .catch(error => {
                    console.error('Erreur de recherche:', error);
                });
        },
        
        displayResults: function(data, type) {
            const resultsContainer = document.getElementById(`${type}-results`);
            if (!resultsContainer) return;
            
            resultsContainer.innerHTML = '';
            
            if (data.results && data.results.length > 0) {
                data.results.forEach(item => {
                    const resultElement = this.createResultElement(item, type);
                    resultsContainer.appendChild(resultElement);
                });
            } else {
                resultsContainer.innerHTML = '<p class="text-muted">Aucun résultat trouvé</p>';
            }
        },
        
        createResultElement: function(item, type) {
            const div = document.createElement('div');
            div.className = 'list-group-item list-group-item-action';
            div.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${item.name}</h6>
                    <small>${item.category || ''}</small>
                </div>
                <p class="mb-1">${item.description || ''}</p>
                <small class="text-muted">${item.address || ''}</small>
            `;
            return div;
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les fonctionnalités
    GourmetGuide.search.init();
    
    // Mettre à jour le compteur du panier
    if (document.getElementById('cart-count')) {
        GourmetGuide.cart.updateCartCount();
    }
    
    // Initialiser les tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialiser les popovers Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Animation des éléments au scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observer les éléments avec la classe animate-on-scroll
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
});

// Gestion des erreurs globales
window.addEventListener('error', function(e) {
    console.error('Erreur JavaScript:', e.error);
    // Optionnel: envoyer l'erreur au serveur pour monitoring
});

// Gestion des erreurs de fetch
window.addEventListener('unhandledrejection', function(e) {
    console.error('Promesse rejetée:', e.reason);
});

// Export pour utilisation dans d'autres scripts
window.GourmetGuide = GourmetGuide;