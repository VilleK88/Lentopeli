// Main customer management functionality
const CustomerManager = {
    currentCustomer: null,

    // Initialize the customer management system
    init: function() {
        console.log('Customer Manager initialized');
        this.loadCustomerInfo();
        this.setupEventListeners();
        this.loadCustomerDatabase(); // Load customer database on init

        // Refresh customer info every 5 seconds
        setInterval(() => this.loadCustomerInfo(), 5000);
    },

    // Set up event listeners for customer-related actions
    setupEventListeners: function() {
        // Event listeners for product offerings
        document.querySelectorAll('.product-offer-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const productName = e.currentTarget.dataset.product;
                this.offerProduct(productName);
            });
        });
    },

    // Load current customer information from the server
    loadCustomerInfo: function() {
        // First check if we already have a current customer (local state)
        if (this.currentCustomer) {
            this.updateCustomerDisplay(this.currentCustomer);
            this.updateCustomerMood(this.currentCustomer);
            document.getElementById('customer-section').classList.remove('hidden');
            document.getElementById('no-customer-message').classList.add('hidden');
            return; // Use existing customer data
        }

        // Try to get customer from server
        fetch('/get_customer_info')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.has_customer) {
                    this.currentCustomer = data;
                    this.updateCustomerDisplay(data);
                    this.updateCustomerMood(data); // Use the mood data from the customer info
                    document.getElementById('customer-section').classList.remove('hidden');
                    document.getElementById('no-customer-message').classList.add('hidden');
                } else {
                    this.currentCustomer = null;
                    document.getElementById('customer-section').classList.add('hidden');
                    document.getElementById('no-customer-message').classList.remove('hidden');
                }
            })
            .catch(error => {
                console.error('Error loading customer info:', error);

                // If no current customer is set, use a fallback
                if (!this.currentCustomer) {
                    // Display "No customer" message if we don't have a customer
                    document.getElementById('customer-section').classList.add('hidden');
                    document.getElementById('no-customer-message').classList.remove('hidden');
                }
            });
    },

    // Load a fallback customer for development/testing
    loadFallbackCustomer: function() {
        const fallbackCustomer = {
            name: "John Smith",
            destination: "EGLL",
            destination_name: "London Heathrow Airport",
            likes: ["water", "alcohol"],
            dislikes: ["meals", "snacks"],
            mood: 5,
            has_customer: true
        };

        this.currentCustomer = fallbackCustomer;
        this.updateCustomerDisplay(fallbackCustomer);
        this.updateCustomerMood(fallbackCustomer);
        document.getElementById('customer-section').classList.remove('hidden');
        document.getElementById('no-customer-message').classList.add('hidden');
    },

    // Update customer mood display with the provided mood data
    updateCustomerMood: function(customerData) {
        if (!customerData.hasOwnProperty('mood')) return;

        const mood = customerData.mood;
        const moodElement = document.getElementById('customer-mood');
        if (moodElement) {
            // Set appropriate emoji based on mood level
            let moodEmoji = '😐';
            let moodText = 'Neutral';

            if (mood >= 8) {
                moodEmoji = '😊';
                moodText = 'Excellent';
            } else if (mood >= 6) {
                moodEmoji = '🙂';
                moodText = 'Good';
            } else if (mood >= 4) {
                moodEmoji = '😐';
                moodText = 'Neutral';
            } else if (mood >= 2) {
                moodEmoji = '🙁';
                moodText = 'Bad';
            } else {
                moodEmoji = '😠';
                moodText = 'Terrible';
            }

            moodElement.textContent = `${moodEmoji} ${mood}/10`;

            // Update mood bar
            const moodBar = document.getElementById('mood-bar-fill');
            if (moodBar) {
                const moodPercent = (mood / 10) * 100;
                moodBar.style.width = `${moodPercent}%`;

                // Change color based on mood
                if (mood >= 8) {
                    moodBar.className = 'mood-bar-fill mood-excellent';
                } else if (mood >= 6) {
                    moodBar.className = 'mood-bar-fill mood-good';
                } else if (mood >= 4) {
                    moodBar.className = 'mood-bar-fill mood-neutral';
                } else if (mood >= 2) {
                    moodBar.className = 'mood-bar-fill mood-bad';
                } else {
                    moodBar.className = 'mood-bar-fill mood-terrible';
                }
            }
        }
    },

    // Update the customer display with information
    updateCustomerDisplay: function(customerData) {
        const customerNameElement = document.getElementById('customer-name');
        const customerDestinationElement = document.getElementById('customer-destination');
        const customerLikesElement = document.getElementById('customer-likes');
        const customerDislikesElement = document.getElementById('customer-dislikes');

        if (customerNameElement) {
            customerNameElement.textContent = customerData.name || 'Unknown';
        }

        if (customerDestinationElement) {
            const destinationText = customerData.destination || 'Unknown';
            const destinationName = customerData.destination_name ? ` (${customerData.destination_name})` : '';
            customerDestinationElement.textContent = `${destinationText}${destinationName}`;
        }

        if (customerLikesElement) {
            customerLikesElement.innerHTML = this.formatPreferences(customerData.likes || [], 'like');
        }

        if (customerDislikesElement) {
            customerDislikesElement.innerHTML = this.formatPreferences(customerData.dislikes || [], 'dislike');
        }
    },

    // Format preferences as HTML
    formatPreferences: function(preferences, type) {
        if (!preferences || preferences.length === 0) {
            return '<span class="no-preferences">None</span>';
        }

        return preferences.map(pref =>
            `<span class="preference-item ${type}">${pref}</span>`
        ).join(' ');
    },

    // Offer a product to the customer
    offerProduct: function(productName) {
        if (!this.currentCustomer) {
            this.showNotification('No active customer to offer products to', 'error');
            return;
        }

        // Try to send to server first
        fetch('/offer_product', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ product: productName })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show reaction
                this.showCustomerReaction(data.reaction);

                // Update mood
                if (data.new_mood) {
                    this.currentCustomer.mood = data.new_mood;
                    this.updateCustomerMood({ mood: data.new_mood });
                }

                // Update money if available
                if (data.hasOwnProperty('money') && window.updateMoneyDisplay) {
                    window.updateMoneyDisplay(data.money);
                }

                this.showNotification(`Offered ${productName} to customer`, 'success');
            } else {
                this.showNotification(data.message || 'Failed to offer product', 'error');
            }
        })
        .catch(error => {
            console.error('Error offering product:', error);

            // Fallback - simulate product offer locally
            this.simulateProductOffer(productName);
        });
    },

    // Simulate product offering (for development/testing)
    simulateProductOffer: function(productName) {
        if (!this.currentCustomer) return;

        const likes = this.currentCustomer.likes || [];
        const dislikes = this.currentCustomer.dislikes || [];

        let reaction = 'neutral';
        let moodChange = 0;
        let moneyChange = 0;

        if (likes.includes(productName)) {
            reaction = 'happy';
            moodChange = 2;
            moneyChange = 10; // Customer pays for liked product
            this.showNotification(`Customer liked the ${productName}!`, 'success');
        } else if (dislikes.includes(productName)) {
            reaction = 'unhappy';
            moodChange = -1;
            this.showNotification(`Customer disliked the ${productName}`, 'error');
        } else {
            moneyChange = 5; // Neutral products still generate revenue
            this.showNotification(`Customer had no preference for ${productName}`, 'info');
        }

        this.showCustomerReaction(reaction);

        // Update mood if customer exists
        if (this.currentCustomer && this.currentCustomer.mood !== undefined) {
            const newMood = Math.max(1, Math.min(10, this.currentCustomer.mood + moodChange));
            this.currentCustomer.mood = newMood;
            this.updateCustomerMood({ mood: newMood });
        }

        // Update money display if the function exists
        if (window.updateMoneyDisplay && moneyChange > 0) {
            // We need to get the current money amount and update it
            // Since we don't have direct access, let's use a custom event
            const moneyUpdateEvent = new CustomEvent('moneyUpdated', {
                detail: { moneyChange: moneyChange }
            });
            document.dispatchEvent(moneyUpdateEvent);
        }
    },

    // Show customer reaction to a product
    showCustomerReaction: function(reaction) {
        const reactionElement = document.getElementById('customer-reaction');
        if (!reactionElement) return;

        // Clear existing reaction classes
        reactionElement.className = 'reaction';

        // Set emoji and class based on reaction type
        if (reaction === 'happy') {
            reactionElement.textContent = '😊';
            reactionElement.classList.add('happy');
        } else if (reaction === 'unhappy') {
            reactionElement.textContent = '😠';
            reactionElement.classList.add('unhappy');
        } else {
            reactionElement.textContent = '😐';
        }

        // Show the reaction
        reactionElement.style.display = 'block';

        // Hide after 3 seconds
        setTimeout(() => {
            reactionElement.style.display = 'none';
        }, 3000);
    },

    // Load the customer database
    loadCustomerDatabase: function() {
        // This function loads customer database from the CustomerDatabaseManager
        console.log('Loading customer database');
    },

    // Select a random customer
    selectRandomCustomer: function() {
        // First try the server endpoint
        fetch('/select_random_customer')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reset current customer to force a reload
                    this.currentCustomer = null;
                    this.loadCustomerInfo();
                    this.showNotification('Random customer selected', 'success');
                } else {
                    this.showNotification(data.message || 'Failed to select random customer', 'error');
                }
            })
            .catch(error => {
                console.error('Error selecting random customer:', error);

                // Fallback - use local data to select a random customer
                if (window.CustomerDatabaseManager && window.CustomerDatabaseManager.customers.length > 0) {
                    const randomIndex = Math.floor(Math.random() * window.CustomerDatabaseManager.customers.length);
                    const randomCustomer = window.CustomerDatabaseManager.customers[randomIndex];

                    // Set as current customer - with a clone to ensure we have a new object
                    const clonedCustomer = JSON.parse(JSON.stringify(randomCustomer));

                    // Reset current customer first to ensure UI updates properly
                    this.currentCustomer = null;

                    // Set the new customer data
                    this.currentCustomer = clonedCustomer;
                    this.updateCustomerDisplay(clonedCustomer);
                    this.updateCustomerMood(clonedCustomer);

                    // Update UI
                    document.getElementById('customer-section').classList.remove('hidden');
                    document.getElementById('no-customer-message').classList.add('hidden');

                    this.showNotification(`Random customer selected: ${clonedCustomer.name}`, 'success');
                } else {
                    // If no database manager or no customers, use fallback
                    this.loadFallbackCustomer();
                    this.showNotification('Loaded fallback customer', 'info');
                }
            });
    },

    // Show notification
    showNotification: function(message, type = 'info') {
        const notificationArea = document.getElementById('notification-area');
        if (!notificationArea) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        notificationArea.appendChild(notification);

        // Remove notification after 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notificationArea.removeChild(notification);
            }, 500); // Match the CSS fade-out animation duration
        }, 5000);
    }
};

// Expose the CustomerManager to the global scope for other scripts
window.CustomerManager = CustomerManager;

// Initialize customer manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    CustomerManager.init();
});