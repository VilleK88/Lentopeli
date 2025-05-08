// Customer Database Manager
const CustomerDatabaseManager = {
    customers: [],

    // Initialize the customer database
    init: function() {
        console.log('Customer Database Manager initialized');
        this.loadCustomersFromServer();
        this.setupEventListeners();
    },

    // Set up event listeners for customer database actions
    setupEventListeners: function() {
        // Add event listeners for database actions if needed
        document.addEventListener('customersLoaded', () => {
            this.renderCustomerTable();

            // Add a button at the top of the customer table for random selection
            this.addRandomCustomerButton();
        });
    },

    // Add a random customer button
    addRandomCustomerButton: function() {
        const customerTableHeader = document.querySelector('.customer-database h2');
        if (!customerTableHeader) return;

        // Check if the button already exists
        if (!document.getElementById('random-customer-btn')) {
            const randomButton = document.createElement('button');
            randomButton.id = 'random-customer-btn';
            randomButton.className = 'random-customer-btn';
            randomButton.innerHTML = '<i class="fas fa-random"></i> Random Customer';

            // Style the button
            randomButton.style.backgroundColor = '#27ae60';
            randomButton.style.color = 'white';
            randomButton.style.border = 'none';
            randomButton.style.borderRadius = '4px';
            randomButton.style.padding = '8px 12px';
            randomButton.style.marginLeft = '10px';
            randomButton.style.cursor = 'pointer';

            // Add event listener
            randomButton.addEventListener('click', () => {
                if (window.CustomerManager) {
                    window.CustomerManager.selectRandomCustomer();
                }
            });

            customerTableHeader.appendChild(randomButton);
        }
    },

    // Load customers from the server
    loadCustomersFromServer: function() {
        // Try to fetch customers, but load fallback data immediately
        // to ensure the app works even without backend connection
        this.loadFallbackCustomers();

        // Attempt to fetch from server - this can update the data if server responds
        fetch('/get_all_customers')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.customers = data.customers;
                    console.log(`Loaded ${this.customers.length} customers from server`);

                    // Trigger event when customers are loaded
                    const event = new CustomEvent('customersLoaded');
                    document.dispatchEvent(event);
                } else {
                    console.error('Failed to load customers:', data.message);
                }
            })
            .catch(error => {
                console.error('Error loading customers:', error);
                // Fallback already loaded
            });
    },

    // Fallback method to load customers from a static list
    loadFallbackCustomers: function() {
        // Create a simple sample of customers for demo purposes
        this.customers = [
            {
                name: "John Smith",
                destination: "EGLL",
                destination_name: "London Heathrow Airport",
                likes: ["water", "alcohol"],
                dislikes: ["meals", "snacks"],
                mood: 5
            },
            {
                name: "Emma Johnson",
                destination: "KJFK",
                destination_name: "John F. Kennedy International Airport",
                likes: ["soda"],
                dislikes: ["fruits"],
                mood: 5
            },
            {
                name: "Liam Brown",
                destination: "EDDF",
                destination_name: "Frankfurt Airport",
                likes: ["snacks", "alcohol"],
                dislikes: ["fruits", "meals"],
                mood: 5
            },
            {
                name: "Olivia Jones",
                destination: "RJAA",
                destination_name: "Narita International Airport",
                likes: ["alcohol"],
                dislikes: ["meals"],
                mood: 5
            },
            {
                name: "Noah Garcia",
                destination: "YSSY",
                destination_name: "Sydney Airport",
                likes: ["soda"],
                dislikes: ["meals"],
                mood: 5
            }
        ];

        // Render the table with our fallback data
        this.renderCustomerTable();

        // Dispatch the customersLoaded event
        const event = new CustomEvent('customersLoaded');
        document.dispatchEvent(event);
    },

    // Render the customer table with current customer data
    renderCustomerTable: function() {
        const tableBody = document.getElementById('customer-database-body');
        if (!tableBody) return;

        // Clear existing rows
        tableBody.innerHTML = '';

        if (this.customers.length === 0) {
            const noDataRow = document.createElement('tr');
            noDataRow.innerHTML = '<td colspan="5" class="text-center">No customers found</td>';
            tableBody.appendChild(noDataRow);
            return;
        }

        // Add customer rows
        this.customers.forEach(customer => {
            const row = document.createElement('tr');

            // Format likes and dislikes as spans
            const likesHtml = this.formatPreferences(customer.likes || [], 'like');
            const dislikesHtml = this.formatPreferences(customer.dislikes || [], 'dislike');

            // Create the customer row
            row.innerHTML = `
                <td>${customer.name || 'Unknown'}</td>
                <td>${customer.destination || 'N/A'} ${customer.destination_name ? `(${customer.destination_name})` : ''}</td>
                <td>${likesHtml || 'None'}</td>
                <td>${dislikesHtml || 'None'}</td>
                <td>
                    <button class="select-customer-btn" data-customer-name="${customer.name}">
                        <i class="fas fa-user-check"></i> Select
                    </button>
                </td>
            `;

            tableBody.appendChild(row);
        });

        // Add event listeners to the select buttons
        document.querySelectorAll('.select-customer-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const customerName = e.target.getAttribute('data-customer-name') ||
                                    (e.target.parentElement && e.target.parentElement.getAttribute('data-customer-name'));

                if (customerName) {
                    this.selectCustomer(customerName);
                }
            });
        });
    },

    // Format preferences (likes/dislikes) as HTML
    formatPreferences: function(preferences, type) {
        if (!preferences || preferences.length === 0) return 'None';

        return preferences.map(pref =>
            `<span class="preference-item ${type}">${pref}</span>`
        ).join(' ');
    },

    // Select a customer from the database
    selectCustomer: function(customerName) {
        // First try to find the customer by name
        const selectedCustomer = this.customers.find(c => c.name === customerName);

        if (selectedCustomer) {
            // Add destination if it's missing (for demo purposes)
            if (!selectedCustomer.destination) {
                selectedCustomer.destination = "KJFK";
                selectedCustomer.destination_name = "John F. Kennedy International Airport";
            }

            // Store as current customer
            if (window.CustomerManager) {
                // Create a clone of the customer to prevent reference issues
                const customerClone = JSON.parse(JSON.stringify(selectedCustomer));

                // Reset current customer to force UI update
                window.CustomerManager.currentCustomer = null;

                // Set the new customer
                window.CustomerManager.currentCustomer = customerClone;
                window.CustomerManager.updateCustomerDisplay(customerClone);

                // Show customer section and hide no-customer message
                const customerSection = document.getElementById('customer-section');
                const noCustomerMessage = document.getElementById('no-customer-message');

                if (customerSection) {
                    customerSection.classList.remove('hidden');
                }

                if (noCustomerMessage) {
                    noCustomerMessage.classList.add('hidden');
                }

                window.CustomerManager.showNotification(`Customer ${customerName} selected`, 'success');
            }

            // Try to notify the server (but don't rely on it)
            fetch('/select_customer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ customer_name: customerName })
            })
            .catch(error => {
                console.error('Error sending selection to server:', error);
                // Already handled with the local selection
            });
        } else {
            console.error(`Customer "${customerName}" not found in the database`);
            if (window.CustomerManager) {
                window.CustomerManager.showNotification(`Customer "${customerName}" not found`, 'error');
            }
        }
    }
};

// Initialize customer database manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Make sure the CustomerManager is available globally
    window.CustomerDatabaseManager = CustomerDatabaseManager;
    CustomerDatabaseManager.init();
});