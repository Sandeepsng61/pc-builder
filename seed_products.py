from pymongo import MongoClient
from simple_app import Product, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_from_mongodb():
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017")
        mongodb = client['your_database_name']
        mongo_products = mongodb.products
        
        # Retrieve products from MongoDB
        products_data = list(mongo_products.find())
        
        if not products_data:
            logger.warning("No products found in MongoDB")
            return
        
        # Convert MongoDB products to SQLAlchemy models
        for product_data in products_data:
            # Skip if product with same name already exists
            existing_product = Product.query.filter_by(name=product_data['name']).first()
            if existing_product:
                logger.info(f"Product {product_data['name']} already exists, skipping")
                continue
                
            # Create new product
            new_product = Product(
                name=product_data['name'],
                category=product_data.get('category', 'other'),
                price=product_data.get('price', 0),
                image_url=product_data.get('image_url', ''),
                specs={k: v for k, v in product_data.items() if k not in ['_id', 'name', 'category', 'price', 'image_url']}
            )
            
            db.session.add(new_product)
        
        db.session.commit()
        logger.info(f"Successfully imported {len(products_data)} products from MongoDB")
        
    except Exception as e:
        logger.error(f"Error seeding products from MongoDB: {e}")
        db.session.rollback()

if __name__ == '__main__':
    from simple_app import app
    
    with app.app_context():
        seed_from_mongodb()
