// Cart functionality
document.addEventListener('DOMContentLoaded', function() {
    // Update cart item quantity
    const quantityInputs = document.querySelectorAll('.cart-quantity-input');
    
    if (quantityInputs.length > 0) {
        quantityInputs.forEach(input => {
            input.addEventListener('change', function() {
                const productId = this.dataset.productId;
                const quantity = parseInt(this.value);
                
                if (quantity < 1) {
                    this.value = 1;
                    return;
                }
                
                // Get the update form and submit it
                const form = document.querySelector(`#update-form-${productId}`);
                if (form) {
                    const quantityInput = form.querySelector('input[name=quantity]');
                    quantityInput.value = quantity;
                    form.submit();
                }
            });
        });
    }
    
    // Remove item from cart
    const removeButtons = document.querySelectorAll('.remove-from-cart');
    
    if (removeButtons.length > 0) {
        removeButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const productId = this.dataset.productId;
                
                // Get the remove form and submit it
                const form = document.querySelector(`#remove-form-${productId}`);
                if (form) {
                    form.submit();
                }
            });
        });
    }
    
    // Update cart total
    function updateCartTotal() {
        const cartItems = document.querySelectorAll('.cart-item');
        let total = 0;
        
        cartItems.forEach(item => {
            const price = parseFloat(item.dataset.price);
            const quantity = parseInt(item.querySelector('.cart-quantity-input').value);
            const itemTotal = price * quantity;
            total += itemTotal;
            
            // Update item total
            const itemTotalElement = item.querySelector('.item-total');
            if (itemTotalElement) {
                itemTotalElement.textContent = '$' + itemTotal.toFixed(2);
            }
        });
        
        // Update cart total
        const cartTotalElement = document.getElementById('cart-total');
        if (cartTotalElement) {
            cartTotalElement.textContent = '$' + total.toFixed(2);
        }
    }
    
    // Call updateCartTotal when the page loads
    if (document.querySelector('.cart-item')) {
        updateCartTotal();
        
        // Add event listeners to quantity inputs for live updating totals
        document.querySelectorAll('.cart-quantity-input').forEach(input => {
            input.addEventListener('change', updateCartTotal);
        });
    }
    
    // Add to cart animation
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
    
    if (addToCartButtons.length > 0) {
        addToCartButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Add a class to animate the button
                this.classList.add('btn-success');
                
                // Add a checkmark icon
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Added!';
                
                // Reset after a delay
                setTimeout(() => {
                    this.classList.remove('btn-success');
                    this.innerHTML = originalText;
                }, 1500);
            });
        });
    }
    
    // Show confirmation modal when emptying cart
    const emptyCartButton = document.getElementById('empty-cart-button');
    
    if (emptyCartButton) {
        emptyCartButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const confirmed = confirm('Are you sure you want to empty your cart?');
            
            if (confirmed) {
                window.location.href = this.getAttribute('href');
            }
        });
    }
});
