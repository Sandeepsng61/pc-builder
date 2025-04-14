// PC Builder functionality
document.addEventListener('DOMContentLoaded', function() {
    // Track selected components and their prices
    const selectedComponents = {
        cpu: null,
        motherboard: null,
        gpu: null,
        ram: null,
        storage: null,
        psu: null,
        case: null,
        cooling: null
    };
    
    let totalPrice = 0;
    
    // Update total price and compatibility information
    function updateBuildSummary() {
        totalPrice = 0;
        
        // Calculate total price
        for (const component in selectedComponents) {
            if (selectedComponents[component]) {
                totalPrice += selectedComponents[component].price;
            }
        }
        
        // Update price display
        const totalPriceElement = document.getElementById('total-price');
        if (totalPriceElement) {
            totalPriceElement.textContent = '₹' + totalPrice.toFixed(2);
        }
        
        // Update build progress
        const selectedCount = Object.values(selectedComponents).filter(component => component !== null).length;
        const progressBar = document.getElementById('build-progress');
        if (progressBar) {
            const progressPercentage = (selectedCount / Object.keys(selectedComponents).length) * 100;
            progressBar.style.width = progressPercentage + '%';
            progressBar.setAttribute('aria-valuenow', progressPercentage);
        }
        
        // Enable/disable add to cart button
        const addToCartBtn = document.getElementById('add-build-to-cart');
        if (addToCartBtn) {
            // Only enable if CPU, motherboard, and RAM are selected at minimum
            const essentialComponents = selectedComponents.cpu && selectedComponents.motherboard && selectedComponents.ram;
            addToCartBtn.disabled = !essentialComponents;
        }
        
        // Check compatibility
        checkCompatibility();
    }
    
    // Select a component
    function selectComponent(category, component) {
        // Update selected component
        selectedComponents[category] = component;
        
        // Update UI to show selected component
        const componentSlot = document.getElementById(`${category}-slot`);
        if (componentSlot) {
            componentSlot.classList.remove('empty');
            componentSlot.classList.add('filled');
            
            const componentName = componentSlot.querySelector('.component-name');
            if (componentName) {
                componentName.textContent = component.name;
            }
            
            const componentPrice = componentSlot.querySelector('.component-price');
            if (componentPrice) {
                componentPrice.textContent = '₹' + component.price.toFixed(2);
            }
        }
        
        // Close the modal if it exists
        const modal = bootstrap.Modal.getInstance(document.getElementById(`${category}-modal`));
        if (modal) {
            modal.hide();
        }
        
        // Update build summary
        updateBuildSummary();
    }
    
    // Check compatibility between components
    function checkCompatibility() {
        const compatibilityWarnings = document.getElementById('compatibility-warnings');
        if (!compatibilityWarnings) return;
        
        // Clear existing warnings
        compatibilityWarnings.innerHTML = '';
        
        // Check CPU and motherboard socket compatibility
        if (selectedComponents.cpu && selectedComponents.motherboard) {
            const cpuSocket = selectedComponents.cpu.specs?.socket;
            const motherboardSocket = selectedComponents.motherboard.specs?.socket;
            
            if (cpuSocket && motherboardSocket && cpuSocket !== motherboardSocket) {
                const warning = document.createElement('div');
                warning.className = 'alert alert-warning';
                warning.textContent = `CPU socket (${cpuSocket}) is not compatible with motherboard socket (${motherboardSocket})`;
                compatibilityWarnings.appendChild(warning);
            }
        }
        
        // Check RAM and motherboard compatibility
        if (selectedComponents.ram && selectedComponents.motherboard) {
            const ramType = selectedComponents.ram.specs?.type;
            const motherboardMemoryType = selectedComponents.motherboard.specs?.memory_type;
            
            if (ramType && motherboardMemoryType && ramType !== motherboardMemoryType) {
                const warning = document.createElement('div');
                warning.className = 'alert alert-warning';
                warning.textContent = `RAM type (${ramType}) is not compatible with motherboard memory type (${motherboardMemoryType})`;
                compatibilityWarnings.appendChild(warning);
            }
        }
        
        // Check power supply wattage (simplified check)
        if (selectedComponents.psu && selectedComponents.gpu) {
            const psuWattage = parseInt(selectedComponents.psu.specs?.wattage);
            const gpuPower = parseInt(selectedComponents.gpu.specs?.power);
            
            if (psuWattage && gpuPower && psuWattage < gpuPower + 200) {  // Adding 200W for other components
                const warning = document.createElement('div');
                warning.className = 'alert alert-warning';
                warning.textContent = `Power supply (${psuWattage}W) may not be sufficient for the selected components`;
                compatibilityWarnings.appendChild(warning);
            }
        }
    }
    
    // Initialize component selection buttons
    document.querySelectorAll('.component-select-btn').forEach(button => {
        button.addEventListener('click', function() {
            console.log('Component selection button clicked');
            const category = this.dataset.category;
            const componentId = parseInt(this.dataset.componentId);
            console.log('Category:', category, 'Component ID:', componentId);
            
            // Get component data (in a real app, you might fetch this from an API)
            const componentElement = this.closest('.component-card');
            console.log('Component element found:', !!componentElement);
            if (componentElement) {
                console.log('Component data attributes:', 
                    componentElement.dataset.name,
                    componentElement.dataset.price,
                    componentElement.dataset.specs);
                
                const component = {
                    id: componentId,
                    name: componentElement.dataset.name,
                    price: parseFloat(componentElement.dataset.price),
                    specs: JSON.parse(componentElement.dataset.specs || '{}')
                };
                console.log('Component object:', component);
                
                selectComponent(category, component);
            }
        });
    });
    
    // Clear component selection
    document.querySelectorAll('.component-clear-btn').forEach(button => {
        button.addEventListener('click', function() {
            const category = this.dataset.category;
            
            // Clear selected component
            selectedComponents[category] = null;
            
            // Update UI
            const componentSlot = document.getElementById(`${category}-slot`);
            if (componentSlot) {
                componentSlot.classList.remove('filled');
                componentSlot.classList.add('empty');
                
                const componentName = componentSlot.querySelector('.component-name');
                if (componentName) {
                    componentName.textContent = 'Select a ' + category;
                }
                
                const componentPrice = componentSlot.querySelector('.component-price');
                if (componentPrice) {
                    componentPrice.textContent = '';
                }
            }
            
            // Update build summary
            updateBuildSummary();
        });
    });
    
    // Add complete build to cart
    const addBuildToCartBtn = document.getElementById('add-build-to-cart');
    if (addBuildToCartBtn) {
        addBuildToCartBtn.addEventListener('click', function() {
            // Create a list of selected component IDs
            const componentIds = [];
            for (const category in selectedComponents) {
                if (selectedComponents[category]) {
                    componentIds.push(selectedComponents[category].id);
                }
            }
            
            // Send request to add all components to cart
            componentIds.forEach(id => {
                // Create and submit a form for each component
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '/add-to-cart';
                form.style.display = 'none';
                
                const productIdInput = document.createElement('input');
                productIdInput.type = 'hidden';
                productIdInput.name = 'product_id';
                productIdInput.value = id;
                
                const quantityInput = document.createElement('input');
                quantityInput.type = 'hidden';
                quantityInput.name = 'quantity';
                quantityInput.value = 1;
                
                form.appendChild(productIdInput);
                form.appendChild(quantityInput);
                document.body.appendChild(form);
                form.submit();
            });
        });
    }
    
    // Initialize build summary
    updateBuildSummary();
});
