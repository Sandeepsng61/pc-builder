from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import datetime
from datetime import datetime
from zoneinfo import ZoneInfo
import pytz
import os
import logging
import uuid
import json
import stripe

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "supersecret123")  # Use env var in prod
CORS(app)

# Configure Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///pc_assembler.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(256))
    specs = db.Column(db.JSON)
    stock = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(16), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(32), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(32), default="pending")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    
    # Relationship
    user = db.relationship('User', backref=db.backref('orders', lazy=True))

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    
    # Relationships
    order = db.relationship('Order', backref=db.backref('items', lazy=True))
    product = db.relationship('Product')

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    
    # Relationships
    user = db.relationship('User', backref=db.backref('wishlist_items', lazy=True))
    product = db.relationship('Product')

# Initialize database
with app.app_context():
    db.create_all()
    
    # Force reset products to ensure components are available
    Product.query.delete()
    
    # Add sample data
    # Create a demo user if it doesn't exist
    demo_user = User.query.filter_by(username="demo").first()
    if not demo_user:
        demo_user = User(username="demo", email="demo@example.com")
        demo_user.set_password("password")
        db.session.add(demo_user)
    
    # Create some products
    products = [
        # Intel Gaming PCs
        Product(
                name="Intel Gaming PC - Ultimate Edition",
                price=1299.99,
                category="prebuilt",
                description="High-performance gaming PC with Intel Core i7 processor",
                image_url="https://via.placeholder.com/300x200?text=Intel+Gaming+PC",
                specs={
                    "cpu": "Intel Core i7-12700K",
                    "ram": "32GB DDR4 3200MHz",
                    "storage": "1TB NVMe SSD",
                    "gpu": "NVIDIA RTX 3070"
                }
            ),
            Product(
                name="Intel Pro Gaming Rig",
                price=1799.99,
                category="prebuilt",
                description="Professional-grade gaming PC with top-tier Intel CPU",
                image_url="https://via.placeholder.com/300x200?text=Intel+Pro+Gaming",
                specs={
                    "cpu": "Intel Core i9-12900K",
                    "ram": "64GB DDR5 4800MHz",
                    "storage": "2TB NVMe SSD",
                    "gpu": "NVIDIA RTX 3080 Ti"
                }
            ),
            Product(
                name="Intel Budget Gamer",
                price=899.99,
                category="prebuilt",
                description="Affordable gaming PC with Intel Core i5 processor",
                image_url="https://via.placeholder.com/300x200?text=Intel+Budget+PC",
                specs={
                    "cpu": "Intel Core i5-12400F",
                    "ram": "16GB DDR4 3000MHz",
                    "storage": "500GB NVMe SSD + 1TB HDD",
                    "gpu": "NVIDIA RTX 3060"
                }
            ),
            
            # AMD Gaming PCs
            Product(
                name="AMD Gaming PC - Pro Series",
                price=1199.99,
                category="prebuilt",
                description="High-performance gaming PC with AMD Ryzen processor",
                image_url="https://via.placeholder.com/300x200?text=AMD+Gaming+PC",
                specs={
                    "cpu": "AMD Ryzen 7 5800X",
                    "ram": "32GB DDR4 3600MHz",
                    "storage": "1TB NVMe SSD",
                    "gpu": "AMD Radeon RX 6800 XT"
                }
            ),
            Product(
                name="AMD Threadripper Workstation",
                price=2499.99,
                category="prebuilt",
                description="Extreme performance workstation with AMD Threadripper CPU",
                image_url="https://via.placeholder.com/300x200?text=AMD+Workstation",
                specs={
                    "cpu": "AMD Threadripper 3970X",
                    "ram": "128GB DDR4 3200MHz",
                    "storage": "4TB NVMe SSD RAID",
                    "gpu": "AMD Radeon Pro W6800"
                }
            ),
            Product(
                name="AMD Budget Gaming PC",
                price=799.99,
                category="prebuilt",
                description="Affordable gaming PC with AMD Ryzen 5 processor",
                image_url="https://via.placeholder.com/300x200?text=AMD+Budget+PC",
                specs={
                    "cpu": "AMD Ryzen 5 5600X",
                    "ram": "16GB DDR4 3200MHz",
                    "storage": "500GB NVMe SSD + 1TB HDD",
                    "gpu": "AMD Radeon RX 6600 XT"
                }
            ),
            Product(
                name="PlayStation 5",
                price=499.99,
                category="console",
                description="Next-generation gaming console from Sony",
                image_url="https://via.placeholder.com/300x200?text=PlayStation+5",
                specs={
                    "cpu": "8-core AMD Zen 2",
                    "gpu": "AMD RDNA 2",
                    "storage": "825GB SSD"
                }
            ),
            Product(
                name="Xbox Series X",
                price=499.99,
                category="console",
                description="Next-generation gaming console from Microsoft",
                image_url="https://via.placeholder.com/300x200?text=Xbox+Series+X",
                specs={
                    "cpu": "8-core AMD Zen 2",
                    "gpu": "AMD RDNA 2",
                    "storage": "1TB SSD"
                }
            )
    ]
    
    # Add individual components
    components = [
        # CPUs
        Product(
                name="Intel Core i5-13600K",
                price=299.99,
                category="cpu",
                description="12 cores (6P + 6E), 20 threads, up to 5.1 GHz",
                image_url="https://via.placeholder.com/300x200?text=Intel+i5+13600K",
                specs={
                    "brand": "Intel",
                    "cores": 12,
                    "threads": 20,
                    "base_clock": "3.5 GHz",
                    "boost_clock": "5.1 GHz",
                    "socket": "LGA 1700",
                    "tdp": "125W"
                },
                stock=15
            ),
            Product(
                name="AMD Ryzen 7 7800X3D",
                price=449.99,
                category="cpu",
                description="8 cores, 16 threads, up to 5.0 GHz with 3D V-Cache",
                image_url="https://via.placeholder.com/300x200?text=AMD+Ryzen+7+7800X3D",
                specs={
                    "brand": "AMD",
                    "cores": 8,
                    "threads": 16,
                    "base_clock": "4.2 GHz",
                    "boost_clock": "5.0 GHz",
                    "socket": "AM5",
                    "tdp": "120W",
                    "cache": "96MB"
                },
                stock=10
            ),
            Product(
                name="AMD Ryzen 5 5600G",
                price=189.99,
                category="cpu",
                description="6 cores, 12 threads, up to 4.4 GHz with integrated Radeon graphics",
                image_url="https://via.placeholder.com/300x200?text=AMD+Ryzen+5+5600G",
                specs={
                    "brand": "AMD",
                    "cores": 6,
                    "threads": 12,
                    "base_clock": "3.9 GHz",
                    "boost_clock": "4.4 GHz",
                    "socket": "AM4",
                    "tdp": "65W",
                    "integrated_graphics": "Radeon Vega 7"
                },
                stock=20
            ),
            
            # GPUs
            Product(
                name="NVIDIA RTX 4070",
                price=599.99,
                category="gpu",
                description="12GB GDDR6X, ray tracing, DLSS 3.0",
                image_url="https://via.placeholder.com/300x200?text=NVIDIA+RTX+4070",
                specs={
                    "brand": "NVIDIA",
                    "memory": "12GB GDDR6X",
                    "memory_bus": "192-bit",
                    "cuda_cores": "5888",
                    "boost_clock": "2.48 GHz",
                    "power": "200W"
                },
                stock=8
            ),
            Product(
                name="AMD Radeon RX 7800 XT",
                price=549.99,
                category="gpu",
                description="16GB GDDR6, ray tracing, FSR 3.0",
                image_url="https://via.placeholder.com/300x200?text=AMD+RX+7800+XT",
                specs={
                    "brand": "AMD",
                    "memory": "16GB GDDR6",
                    "memory_bus": "256-bit",
                    "stream_processors": "3840",
                    "boost_clock": "2.43 GHz",
                    "power": "263W"
                },
                stock=5
            ),
            
            # Motherboards
            Product(
                name="ASUS ROG Strix Z790-E Gaming WiFi",
                price=399.99,
                category="motherboard",
                description="Intel Z790 ATX motherboard with DDR5, PCIe 5.0, WiFi 6E",
                image_url="https://via.placeholder.com/300x200?text=ASUS+ROG+Z790",
                specs={
                    "brand": "ASUS",
                    "chipset": "Intel Z790",
                    "socket": "LGA 1700",
                    "form_factor": "ATX",
                    "memory_type": "DDR5",
                    "max_memory": "128GB",
                    "pcie_slots": "3x PCIe 5.0 x16",
                    "m2_slots": "4x M.2"
                },
                stock=7
            ),
            Product(
                name="MSI MAG B650 TOMAHAWK WIFI",
                price=219.99,
                category="motherboard",
                description="AMD B650 ATX motherboard with DDR5, PCIe 4.0, WiFi 6E",
                image_url="https://via.placeholder.com/300x200?text=MSI+B650+TOMAHAWK",
                specs={
                    "brand": "MSI",
                    "chipset": "AMD B650",
                    "socket": "AM5",
                    "form_factor": "ATX",
                    "memory_type": "DDR5",
                    "max_memory": "128GB",
                    "pcie_slots": "1x PCIe 4.0 x16",
                    "m2_slots": "3x M.2"
                },
                stock=12
            ),
            
            # RAM
            Product(
                name="Corsair Vengeance RGB Pro 32GB (2x16GB) DDR4-3600",
                price=129.99,
                category="ram",
                description="High-performance DDR4 memory with RGB lighting",
                image_url="https://via.placeholder.com/300x200?text=Corsair+Vengeance+RGB",
                specs={
                    "brand": "Corsair",
                    "capacity": "32GB (2x16GB)",
                    "type": "DDR4",
                    "speed": "3600MHz",
                    "cas_latency": "18",
                    "voltage": "1.35V",
                    "rgb": "Yes"
                },
                stock=25
            ),
            Product(
                name="G.Skill Trident Z5 RGB 32GB (2x16GB) DDR5-6000",
                price=189.99,
                category="ram",
                description="High-speed DDR5 memory with RGB lighting",
                image_url="https://via.placeholder.com/300x200?text=G.Skill+Trident+Z5",
                specs={
                    "brand": "G.Skill",
                    "capacity": "32GB (2x16GB)",
                    "type": "DDR5",
                    "speed": "6000MHz",
                    "cas_latency": "36",
                    "voltage": "1.35V",
                    "rgb": "Yes"
                },
                stock=15
            ),
            
            # Storage
            Product(
                name="Samsung 980 Pro 1TB NVMe SSD",
                price=119.99,
                category="storage",
                description="High-performance PCIe 4.0 NVMe SSD",
                image_url="https://via.placeholder.com/300x200?text=Samsung+980+Pro",
                specs={
                    "brand": "Samsung",
                    "capacity": "1TB",
                    "type": "NVMe SSD",
                    "interface": "PCIe 4.0 x4",
                    "read_speed": "7000 MB/s",
                    "write_speed": "5000 MB/s",
                    "endurance": "600 TBW"
                },
                stock=30
            ),
            Product(
                name="WD Black 2TB HDD",
                price=79.99,
                category="storage",
                description="High-performance hard drive for gaming",
                image_url="https://via.placeholder.com/300x200?text=WD+Black+2TB",
                specs={
                    "brand": "Western Digital",
                    "capacity": "2TB",
                    "type": "HDD",
                    "interface": "SATA 3",
                    "rpm": "7200 RPM",
                    "cache": "64MB",
                    "form_factor": "3.5 inch"
                },
                stock=40
            ),
            
            # Power Supplies
            Product(
                name="Corsair RM850x 850W 80+ Gold",
                price=149.99,
                category="psu",
                description="Fully modular power supply with 80+ Gold efficiency",
                image_url="https://via.placeholder.com/300x200?text=Corsair+RM850x",
                specs={
                    "brand": "Corsair",
                    "wattage": "850W",
                    "efficiency": "80+ Gold",
                    "modular": "Fully Modular",
                    "fan_size": "135mm",
                    "protection": "OVP, UVP, OCP, OPP, SCP",
                    "warranty": "10 years"
                },
                stock=18
            ),
            
            # Cases
            Product(
                name="Lian Li O11 Dynamic EVO",
                price=169.99,
                category="case",
                description="Premium mid-tower case with tempered glass panels",
                image_url="https://via.placeholder.com/300x200?text=Lian+Li+O11",
                specs={
                    "brand": "Lian Li",
                    "type": "Mid Tower",
                    "colors": "Black/White",
                    "side_panel": "Tempered Glass",
                    "dimensions": "465 x 285 x 459 mm",
                    "max_gpu_length": "423mm",
                    "radiator_support": "Up to 360mm"
                },
                stock=10
            ),
            
            # Cooling
            Product(
                name="NZXT Kraken X63 RGB 280mm AIO",
                price=159.99,
                category="cooling",
                description="280mm all-in-one liquid CPU cooler with RGB",
                image_url="https://via.placeholder.com/300x200?text=NZXT+Kraken+X63",
                specs={
                    "brand": "NZXT",
                    "type": "AIO Liquid Cooler",
                    "radiator_size": "280mm",
                    "fan_size": "2x 140mm",
                    "rgb": "Yes",
                    "compatibility": "Intel & AMD",
                    "noise_level": "21-38 dBA"
                },
                stock=12
            ),
            
            # Peripherals
            Product(
                name="Logitech G Pro X Superlight",
                price=129.99,
                category="peripherals",
                description="Ultra-lightweight wireless gaming mouse",
                image_url="https://via.placeholder.com/300x200?text=Logitech+G+Pro+X",
                specs={
                    "brand": "Logitech",
                    "type": "Gaming Mouse",
                    "connectivity": "Wireless",
                    "dpi": "25600",
                    "weight": "63g",
                    "buttons": "5",
                    "battery_life": "70 hours"
                },
                stock=35
            )
    ]
    
    for product in products + components:
        db.session.add(product)
    
    db.session.commit()
    logger.info("Database initialized with sample data")

# Helper function
def generate_order_id():
    return str(uuid.uuid4())[:8].upper()

# Routes
@app.route('/')
def index():
    featured_products = Product.query.filter(Product.category.in_(['prebuilt', 'console'])).limit(6).all()
    return render_template('index.html', products=featured_products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/prebuilt')
def prebuilt_pcs():
    prebuilt_pcs = Product.query.filter_by(category='prebuilt').all()
    return render_template('prebuilt_pcs.html', products=prebuilt_pcs)

@app.route('/intel')
def intel_pcs():
    try:
        intel_pcs = Product.query.filter_by(category='prebuilt').all()
        # Filter for Intel products on the application side
        intel_products = []
        for pc in intel_pcs:
            if pc.specs and 'processor' in pc.specs and 'Intel' in pc.specs['processor']:
                intel_products.append(pc)
        return render_template('intel_pcs.html', products=intel_products)
    except Exception as e:
        logger.error(f"Error in intel_pcs route: {e}")
        flash('Could not load Intel PCs. Please try again later.', 'danger')
        return redirect(url_for('index'))

@app.route('/amd')
def amd_pcs():
    try:
        amd_pcs = Product.query.filter_by(category='prebuilt').all()
        # Filter for AMD products on the application side
        amd_products = []
        for pc in amd_pcs:
            if pc.specs and 'processor' in pc.specs and 'AMD' in pc.specs['processor']:
                amd_products.append(pc)
        return render_template('amd_pcs.html', products=amd_products)
    except Exception as e:
        logger.error(f"Error in amd_pcs route: {e}")
        flash('Could not load AMD PCs. Please try again later.', 'danger')
        return redirect(url_for('index'))

@app.route('/consoles')
def gaming_consoles():
    consoles = Product.query.filter_by(category='console').all()
    return render_template('gaming_consoles.html', products=consoles)

@app.route('/components')
def components():
    category = request.args.get('category', 'all')
    
    if category == 'all':
        products = Product.query.filter(Product.category.in_(['cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu', 'case', 'cooling', 'peripherals'])).all()
    else:
        products = Product.query.filter_by(category=category).all()
    
    categories = ['all', 'cpu', 'gpu', 'motherboard', 'ram', 'storage', 'psu', 'case', 'cooling', 'peripherals']
    return render_template('components.html', products=products, categories=categories, selected_category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/custom-pc')
def custom_pc_builder():
    cpus = Product.query.filter_by(category='cpu').all()
    motherboards = Product.query.filter_by(category='motherboard').all()
    gpus = Product.query.filter_by(category='gpu').all()
    rams = Product.query.filter_by(category='ram').all()
    storages = Product.query.filter_by(category='storage').all()
    psus = Product.query.filter_by(category='psu').all()
    cases = Product.query.filter_by(category='case').all()
    coolings = Product.query.filter_by(category='cooling').all()
    
    components = {
        'cpu': cpus,
        'motherboard': motherboards,
        'gpu': gpus,
        'ram': rams,
        'storage': storages,
        'psu': psus,
        'case': cases,
        'cooling': coolings
    }
    
    return render_template('custom_pc_builder.html', components=components)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    if not product_id:
        flash('Invalid product', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    # Initialize cart if it doesn't exist
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if item already in cart
    cart = session['cart']
    item_found = False
    
    for item in cart:
        if item['product_id'] == int(product_id):
            item['quantity'] += quantity
            item_found = True
            break
    
    if not item_found:
        cart.append({
            'product_id': int(product_id),
            'name': product.name,
            'price': product.price,
            'image_url': product.image_url,
            'quantity': quantity
        })
    
    session['cart'] = cart
    flash(f'{product.name} added to cart!', 'success')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/cart')
def view_cart():
    cart_items = session.get('cart', [])
    cart = []
    total = 0
    
    # Fetch actual product data for each cart item
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            cart_item = {
                'product': product,
                'quantity': item['quantity']
            }
            cart.append(cart_item)
            total += product.price * item['quantity']
    
    return render_template('cart.html', cart=cart, total=total)

@app.route('/update-cart', methods=['POST'])
def update_cart():
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity'))
    
    cart = session.get('cart', [])
    
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] = quantity
            break
    
    session['cart'] = cart
    flash('Cart updated successfully', 'success')
    
    return redirect(url_for('view_cart'))

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    product_id = int(request.form.get('product_id'))
    
    cart = session.get('cart', [])
    cart = [item for item in cart if item['product_id'] != product_id]
    session['cart'] = cart
    
    flash('Item removed from cart', 'success')
    return redirect(url_for('view_cart'))

@app.route('/clear-cart', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    flash('Cart cleared successfully', 'success')
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please log in to checkout', 'danger')
        return redirect(url_for('login'))
    
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty', 'info')
        return redirect(url_for('index'))
    
    # Process cart items to include product details
    cart = []
    subtotal = 0
    
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            cart_item = {
                'product': product,
                'quantity': item['quantity']
            }
            cart.append(cart_item)
            subtotal += product.price * item['quantity']
    
    # Calculate totals
    shipping = 100  # ₹100 flat shipping fee
    tax = subtotal * 0.18  # 18% GST
    total = subtotal + shipping + tax
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address_line1 = request.form.get('address_line1')
        address_line2 = request.form.get('address_line2', '')
        city = request.form.get('city')
        state = request.form.get('state')
        pincode = request.form.get('pincode')
        payment_method = request.form.get('payment_method')
        
        # Format complete address
        address = f"{address_line1}, {address_line2}\n{city}, {state} - {pincode}\nPhone: {phone}"
        
        # Create order
        order = Order(
            order_id=generate_order_id(),
            user_id=session['user_id'],
            name=name,
            email=email,
            address=address,
            payment_method=payment_method,
            total_price=total,
            status='pending'
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Add order items
        for item in cart:
            product = item['product']
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item['quantity'],
                price=product.price
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # Clear cart
        session.pop('cart', None)
        
        if payment_method == 'card':
            return redirect(url_for('create_checkout_session'))
        else:
            flash('Order placed successfully!', 'success')
            return redirect(url_for('confirmation', order_id=order.order_id))
    
    return render_template('checkout.html', cart=cart, user=user, subtotal=subtotal, 
                           shipping=shipping, tax=tax, total=total)

@app.route('/create-checkout-session')
def create_checkout_session():
    if 'user_id' not in session:
        flash('Please log in to checkout', 'danger')
        return redirect(url_for('login'))
    
    # Get the latest order for the user
    user_id = session['user_id']
    order = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).first()
    
    if not order:
        flash('No order found', 'danger')
        return redirect(url_for('index'))
    
    # Update order payment method
    order.payment_method = 'card'
    db.session.commit()
    
    # For Stripe integration
    YOUR_DOMAIN = request.host_url.rstrip('/')
    
    try:
        # Get order items
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        line_items = []
        
        for item in order_items:
            product = Product.query.get(item.product_id)
            line_items.append({
                'price_data': {
                    'currency': 'inr',  # Indian Rupees
                    'product_data': {
                        'name': product.name,
                        'description': product.description[:100] if product.description else '',
                    },
                    'unit_amount': int(item.price * 100),  # Convert to paise
                },
                'quantity': item.quantity,
            })
        
        # Add shipping and tax as line items
        shipping_amount = 100 * 100  # ₹100 in paise
        tax_amount = int(order.total_price * 0.18 * 100)  # 18% GST in paise
        
        line_items.append({
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': 'Shipping',
                },
                'unit_amount': shipping_amount,
            },
            'quantity': 1,
        })
        
        line_items.append({
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': 'GST (18%)',
                },
                'unit_amount': tax_amount,
            },
            'quantity': 1,
        })
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + url_for('payment_success'),
            cancel_url=YOUR_DOMAIN + url_for('payment_cancel'),
        )
        
        # Redirect to Stripe checkout
        return redirect(checkout_session.url, code=303)
    
    except Exception as e:
        logger.error(f"Error creating Stripe checkout session: {e}")
        flash('Payment processing error. Please try again.', 'danger')
        return redirect(url_for('checkout'))

@app.route('/payment-success')
def payment_success():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get the latest order for the user
    user_id = session['user_id']
    order = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).first()
    
    if order:
        # Update order status
        order.status = 'completed'
        db.session.commit()
        
        flash('Payment successful! Your order has been placed.', 'success')
        return redirect(url_for('confirmation', order_id=order.order_id))
    
    flash('Order not found', 'danger')
    return redirect(url_for('index'))

@app.route('/payment-cancel')
def payment_cancel():
    flash('Payment was cancelled. You can try again later.', 'warning')
    return redirect(url_for('view_cart'))

@app.route('/confirmation/<order_id>')
def confirmation(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    
    items = []
    for item in order_items:
        product = Product.query.get(item.product_id)
        items.append({
            'name': product.name,
            'price': item.price,
            'quantity': item.quantity,
            'total': item.price * item.quantity
        })
    
    return render_template('confirmation.html', order=order, items=items)

@app.route('/wishlist')
def wishlist():
    if 'user_id' not in session:
        flash('Please log in to view your wishlist', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    wishlist_items = Wishlist.query.filter_by(user_id=user_id).all()
    
    return render_template('wishlist.html', wishlist_items=wishlist_items)

@app.route('/add-to-wishlist', methods=['POST'])
def add_to_wishlist():
    if 'user_id' not in session:
        flash('Please log in to add to wishlist', 'danger')
        return redirect(url_for('login'))
    
    product_id = request.form.get('product_id')
    if not product_id:
        flash('Invalid product', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    user_id = session['user_id']
    
    # Check if item already in wishlist
    existing_item = Wishlist.query.filter_by(
        user_id=user_id, product_id=product_id).first()
    
    if existing_item:
        flash('Product already in your wishlist', 'info')
    else:
        wishlist_item = Wishlist(user_id=user_id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash('Product added to your wishlist', 'success')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/remove-from-wishlist', methods=['POST'])
def remove_from_wishlist():
    if 'user_id' not in session:
        flash('Please log in to manage your wishlist', 'danger')
        return redirect(url_for('login'))
    
    product_id = request.form.get('product_id')
    if not product_id:
        flash('Invalid product', 'danger')
        return redirect(url_for('wishlist'))
    
    user_id = session['user_id']
    
    wishlist_item = Wishlist.query.filter_by(
        user_id=user_id, product_id=product_id).first()
    
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash('Product removed from your wishlist', 'success')
    
    return redirect(url_for('wishlist'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to view your dashboard', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    wishlist_items = Wishlist.query.filter_by(user_id=user.id).all()
    
    return render_template('dashboard.html', user=user, orders=orders, wishlist_items=wishlist_items)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error='Server error'), 500
