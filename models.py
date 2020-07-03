from main import db,app
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime



login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'

product_orders = db.Table('product_orders',db.Column('product_id', db.Integer, db.ForeignKey('product.id')),db.Column('orders_id', db.Integer, db.ForeignKey('orders.id')))
product_purchases = db.Table('product_purchases',db.Column('product_id', db.Integer, db.ForeignKey('product.id')),db.Column('purchases_id', db.Integer, db.ForeignKey('purchases.id')))

class User(UserMixin, db.Model):  
    """ User model """  
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)


class Customer(db.Model):  
    """ Customers model """  
    __tablename__ = "customer"
    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.Date(), default=datetime.utcnow)
    name=db.Column(db.String(), nullable=True)
    age=db.Column(db.Integer,nullable=True)
    gender=db.Column(db.String(), nullable=True)
    patient_phone=db.Column(db.Integer, unique=True,nullable=False)
    nhif_no=db.Column(db.Integer, unique=True,nullable=False)
    National_id=db.Column(db.Integer, unique=True,nullable=False)
    debt=db.Column(db.Integer,default=0)
    orders = db.relationship('Order', backref='customer')
    
class Supplier(db.Model):  
    """ Suppliers model """  
    __tablename__ = "supplier"
    id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(25), unique=True, nullable=False)
    supplier_phone=db.Column(db.Integer, unique=True,nullable=False)
    openbalance=db.Column(db.Integer,default=0)
    purchases = db.relationship('Purchase', backref='supplier')
    
class Purchase(db.Model):  
    """ Purchases model """  
    __tablename__ = "purchases"
    id = db.Column(db.Integer, primary_key=True)
    purchase_date = db.Column(db.Date(), nullable=False)
    invoice_no=db.Column(db.Integer,nullable=False)
    supplier_name = db.Column(db.String(), nullable=False)
    payment_type=db.Column(db.String(25),nullable=False)
    payment_amount=db.Column(db.Integer, nullable=False)
    total_amount= db.Column(db.Integer, nullable=False)
    due_balance=db.Column(db.Integer, nullable=False)
    paydue_amount=db.Column(db.Integer, nullable=False)
    supplier_id = db.Column(db.Integer(), db.ForeignKey('supplier.id'))
    purchaseitem_line = db.relationship('PurchaseItems', backref='purchase')

class PurchaseItems(db.Model):  
    """ purchaseitems model """  
    __tablename__ = "purchaseitems"
    id = db.Column(db.Integer, primary_key=True)
    invoice_no=db.Column(db.Integer,nullable=False)
    product_name = db.Column(db.String(25), nullable=True)
    expiry_date = db.Column(db.Date(), nullable=False)
    quantity=db.Column(db.Integer, nullable=True)
    in_quantity=db.Column(db.Integer, nullable=True)
    buying_price=db.Column(db.Integer, nullable=True)
    sell_price=db.Column(db.Integer, nullable=True)
    total_amount=db.Column(db.Integer, nullable=True)
    purchase_id = db.Column(db.Integer(), db.ForeignKey('purchases.id'))  # Foreign key
    product_id = db.Column(db.Integer(), db.ForeignKey('product.id'))
   


class Product(db.Model):  
    """ Product model """  
    __tablename__ = "product"
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(), unique=True, nullable=False)
    product_type= db.Column(db.String(), nullable=True)
    sell_price=db.Column(db.Integer, nullable=True)
    reoder_level=db.Column(db.Integer, nullable=False)
    purchaseitems_line = db.relationship('PurchaseItems', backref='product')
    orderitems_line = db.relationship('OrderItems', backref='product')
   

class Order(db.Model):  
    """ Orders model """  
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.Date(), nullable=False)
    customer_name = db.Column(db.String(), nullable=False)
    previous=db.Column(db.Integer, nullable=False)
    total_amount= db.Column(db.Integer, nullable=False)
    net_total= db.Column(db.Integer, nullable=False)
    payment_amount=db.Column(db.Integer, nullable=False)
    payment_type=db.Column(db.String(25),nullable=False)
    due_balance=db.Column(db.Integer, nullable=False)
    paydue_amount=db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer(), db.ForeignKey('customer.id'))
    orderitems_line = db.relationship('OrderItems', backref='order')


class OrderItems(db.Model):  
    """ orderitems model """  
    __tablename__ = "orderitems"
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(25), nullable=True)
    product_type = db.Column(db.String(25), nullable=False)
    expiry_date = db.Column(db.Date(), nullable=True)
    quantity=db.Column(db.Integer, nullable=True)
    buying_price=db.Column(db.Integer, nullable=True)
    total_amount=db.Column(db.Integer, nullable=True)
    order_id = db.Column(db.Integer(), db.ForeignKey('orders.id'))  # Foreign key
    product_id = db.Column(db.Integer(), db.ForeignKey('product.id'))


class Expense(db.Model):  
    """ Expense model """  
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    ExpenseCategory_name = db.Column(db.String(100), unique=True, nullable=False)
    trackexpenses = db.relationship('TrackExpense', backref='expense')
    
class TrackExpense(db.Model):  
    """ TrackExpense model """  
    __tablename__ = "trackexpense"
    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.Date(), nullable=False)
    amount= db.Column(db.Integer, nullable=False)
    payment_type=db.Column(db.String(25),nullable=False)
    expense_type=db.Column(db.String(25),nullable=False)
    expense_id = db.Column(db.Integer(), db.ForeignKey('expenses.id'))  # Foreign key


   

    
   

