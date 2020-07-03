from flask import  render_template,url_for,redirect,flash,request,jsonify,make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from main import app,db
from forms import LoginForm,RegisterForm
from models import User,Product,Supplier,product_orders,product_purchases,Purchase,Order,Expense,TrackExpense,\
    PurchaseItems,Customer,OrderItems
import time,datetime
from sqlalchemy import desc,asc
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
import itertools
from operator import itemgetter 
from datetime import date,datetime
from werkzeug.security import generate_password_hash, check_password_hash

login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
@app.route('/')
@app.route('/login', methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=True)
                return redirect(url_for('dashbord'))
            else:
                flash(f'Incorrect Username or password','danger')
        flash(f'Incorrect Username or password','danger')
        return redirect(url_for('signup'))
    return render_template('login.html',form=form)

@app.route('/signup/',methods=['GET','POST'])
def signup():
    form=RegisterForm()
    if form.validate_on_submit():
        hashed_password= generate_password_hash(form.password.data, method='sha256')
        newuser = User(username=form.username.data, password=hashed_password )
        db.session.add(newuser)
        try:
            db.session.commit()
            flash(f' {newuser.username} Successfully Added!', 'success')
            return redirect(url_for('dashbord'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This User already exists','danger')
            return redirect(url_for('signup'))
    return render_template('adduser.html', form=form)

@app.route('/Dashboard/',methods=['GET','POST'])
@login_required
def dashbord():
    return render_template('dashboard.html')


# Patients
#all patients
@app.route('/allpatients/',methods=['GET','POST'])
@login_required
def AllCustomers():
    customers=Customer.query.all()
    return render_template('allCustomers.html',customers=customers)

#add patient
@app.route('/addpatient/',methods=['GET','POST'])
@login_required
def AddCustomer():
    if request.method == 'POST':
        newcustomer = Customer(name=request.form['patient_name'],age=request.form['age'],gender=request.form['gendertype'],patient_phone=request.form['patient_phone'],\
            nhif_no=request.form['patient_nhif_no'],National_id=request.form['patient_National_id'])
        db.session.add(newcustomer)
        try:
            db.session.commit()
            flash(f' {newcustomer.name} Successfully Added!', 'success')
            return redirect(url_for('AllCustomers'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This customer already exists','danger')
            return redirect(url_for('AddCustomer'))
    else:
        return render_template('addCustomer.html')
    
#Edit Patient
@app.route('/patients/<int:customer_id>/edit/', methods = ['GET', 'POST'])
@login_required
def editPatient(customer_id):
    editedItem = Customer.query.filter_by(id = customer_id).one()
    if request.method == 'POST':
        if request.form['patient_name']:
          editedItem.name = request.form['patient_name']
        if request.form['age']:
          editedItem.age = request.form['age']
        if request.form['gendertype']:
          editedItem.gender = request.form['gendertype']
        if request.form['patient_phone']:
          editedItem.patient_phone = request.form['patient_phone']  
        if request.form['patient_nhif_no']:
            editedItem.nhif_no = request.form['patient_nhif_no'] 
        if request.form['patient_National_id']:
            editedItem.National_id = request.form['patient_National_id'] 
        db.session.add(editedItem)
        db.session.commit() 
        flash(f'{editedItem.name}record has been updated!', 'success')
        return redirect(url_for('AllCustomers'))
    else:
        return render_template('editCustomer.html',customer_id=customer_id, patient= editedItem)

#Delete Patient
@app.route('/patient/<int:patient_id>/delete/', methods = ['POST'])
@login_required
def deletePatient(patient_id):
        patientToDelete =Customer.query.filter_by(id = patient_id).one()
        db.session.delete(patientToDelete)
        db.session.commit()
        flash(f'Patient successfully Deleted!','danger')
        return redirect(url_for('AllCustomers', patient_id = patient_id))


# Invoices
@app.route('/addinvoices/',methods=['GET'])
@login_required
def AddInvoice():
    products=[p.product_name for p in Product.query.all()]
    patients=[s.name for s in Customer.query.all()]
    return render_template('addInvoice.html',products=products,patients=patients)

# CUSTOMEZ API ENDPOINT
@app.route('/patientdata/<patient>')
def Patientdata(patient):
    data= Customer.query.filter_by(name=patient).all()
    dataArray=[]
    for patient in data:
        patientobj={}
        patientobj['id']=patient.id
        patientobj['name']=patient.name
        patientobj['debt']=patient.debt
        dataArray.append(patientobj)
    return jsonify({'Patient': dataArray})

# PurchaseItems API ENDPOINT
@app.route('/productdata/<product>')
def Productdata(product):
    data=PurchaseItems.query.filter_by(product_name=product).filter(PurchaseItems.quantity > 0).all()
    dataArray=[]
    for product in data:
        productobj={}
        productobj['id']=product.id
        productobj['product_name']=product.product_name
        productobj['expiry_date']=product.expiry_date
        productobj['quantity']=product.quantity
        dataArray.append(productobj)
    return jsonify({'Product': dataArray})

# API
@app.route('/productqty/<int:product_id>')
def Productqty(product_id):
    data=PurchaseItems.query.filter_by(id=product_id).all()
    dataArray=[]
    for product in data:
        productobj={}
        productobj['id']=product.id
        productobj['quantity']=product.quantity
        dataArray.append(productobj)
    return jsonify({'ProductQty': dataArray})

# process incoming order 
@app.route('/processinvoicedata', methods=['POST'])
def processinvoicedata():
    table= request.json
    key_list = [] 
    filter_key=[]
    product_list=[]
    product_type=[]
    quantityarray=[]
    expiry_array=[]
    price=[]
    total_price=[]
    for dic in table:
        for key in dic:
            key_list.append(key)
    [filter_key.append(x) for x in key_list if x not in filter_key]     
    
    for data in table:
            for i in data:
                if i=="patient_name":
                    patient_name=data[i]
                elif i=="invoice_date":
                    invoice_date=data[i]
                elif i=="paytype":
                    paytype=data[i]
                elif i=="productname":
                    product_list.append(data[i])
                elif i=="producttype":
                    product_type.append(data[i])
                elif i=="expirydata":
                    if i:
                        expiry_array.append(data[i])
                    else:
                        expiry_array.append(0)
                elif i=="quantity":
                    quantityarray.append(data[i])
                elif i=="selling_price":
                    price.append(data[i])
                elif i=="total_amount":
                    total_price.append(data[i])
                elif i=="grand_total_price":
                    grand_total_price=data[i]
                elif i=="previous":
                    previous=data[i]
                elif i=="nettotal":
                    nettotal=data[i]
                elif i=="paid_amount":
                    paid_amount=data[i]
                elif i=="balance":
                    balance=data[i]
                elif i=="debt_pay":
                    debt_pay=data[i]
                
    patientToAdd=Customer.query.filter_by(name=patient_name).one()
    patientToAdd.debt +=int(balance)
    patientToAdd.debt -=int(debt_pay)

    invoiceDate = invoice_date
    invoiceDate_object = datetime.strptime(invoiceDate, "%Y-%m-%d").date()

    newinvoice=Order(customer_name=patient_name,created_on=invoiceDate_object,payment_type=paytype,\
        payment_amount=paid_amount,total_amount=grand_total_price,previous=previous,net_total=nettotal,due_balance=balance,paydue_amount=debt_pay,customer=patientToAdd)
    
    for (prod,prodtyp,expry,qty,price,total) in zip(product_list,product_type,expiry_array,quantityarray,price,total_price):
        
        product_name=Product.query.filter_by(product_name=prod).one()
        
        if expry:
            purchaseitem=PurchaseItems.query.filter_by(id=expry).one()
            expry_date_object=purchaseitem.expiry_date
            expry_date= expry_date_object
        
    
        productToreduce=PurchaseItems.query.filter_by(id=expry).filter(PurchaseItems.quantity > 0).first()

        if (productToreduce is not None) and (expry_date is not None):
           
            productToreduce.quantity -=int(qty)
            itemlines=OrderItems(product_name=prod,expiry_date=expry_date,product_type=prodtyp,quantity=qty,buying_price=price,\
            total_amount=total,order=newinvoice,product=product_name)

            db.session.add(newinvoice)
            db.session.add(itemlines)
            db.session.add(patientToAdd)
            db.session.add(productToreduce)

            db.session.commit()
            db.session.commit()
            db.session.commit()
            db.session.commit()
        else:
            itemlines=OrderItems(product_name=prod,product_type=prodtyp,quantity=qty,buying_price=price,\
            total_amount=total,order=newinvoice,product=product_name)

            db.session.add(newinvoice)
            db.session.add(itemlines)
            db.session.add(patientToAdd)

            db.session.commit()
            db.session.commit()
            db.session.commit()
    return "Success"


# show all orders 
@app.route('/allinvoices/',methods=['GET','POST'])
@login_required
def AllInvoices():
    allinvoices=Order.query.all()
    return render_template('allInvoices.html',allinvoices=allinvoices)

@app.route('/delete/<int:invoice_id>/delete/', methods = ['POST'])
@login_required
def deleteInvoice(invoice_id):
        InvoiceToDelete =Order.query.filter_by(id = invoice_id).one()
        customerId=InvoiceToDelete.customer_id
        balance=InvoiceToDelete.due_balance
        debt_pay=InvoiceToDelete.paydue_amount
        
        patientToAdd=Customer.query.filter_by(id=customerId).one()
        patientToAdd.debt -=int(balance)
        patientToAdd.debt +=int(debt_pay)
       
        
        orderitems=OrderItems.query.filter_by(order_id=invoice_id,product_type='Medication').all()
        print(orderitems)
        for item in orderitems:
            prodname=item.product_name
            prodexpiry=item.expiry_date
            prodquanty=item.quantity

            stock_item=PurchaseItems.query.filter_by(product_name=prodname,expiry_date=prodexpiry).first()
            print(stock_item.quantity)
            stock_item.quantity += prodquanty

            db.session.add(stock_item)
            db.session.commit()

            db.session.delete(item)
            db.session.commit()

        allorderservice=OrderItems.query.filter_by(order_id=invoice_id,product_type='Service').all()
        for service in allorderservice:
            db.session.delete(service)
            db.session.commit()
            
        db.session.add(patientToAdd)
        db.session.commit()

        db.session.delete(InvoiceToDelete)
        db.session.commit()

        flash(f'Invoice  successfully Deleted!','danger')
        return redirect(url_for('AllInvoices'))
# show all items in an order
@app.route('/InvoiceDetails/<int:invoice_id>/',methods=['GET','POST'])
@login_required
def InvoiceDetail(invoice_id):
    product_purchase=OrderItems.query.filter_by(order_id=invoice_id).all()
    order=Order.query.filter_by(id=invoice_id).one()
    patient=order.customer_id
    patientdetails=Customer.query.filter_by(id=patient).one()
    return render_template('invoiceDetails.html',product_purchase=product_purchase,invoice_id=invoice_id,order=order,patientdetails=patientdetails)
    
# Products
@app.route('/products/',methods=['GET','POST'])
@login_required
def allProducts():
    products = Product.query.all()
    
    return render_template('allProducts.html', products = products) 


# Add Product 
@app.route('/addProduct/',methods=['GET','POST'])
@login_required
def Addproduct():
    if request.method == 'POST':
        newItem = Product(product_name=request.form['product_name'],product_type=request.form['product_type'],sell_price=request.form['sell_price'],reoder_level=request.form['reoder_level'])
        db.session.add(newItem)
        try:
            db.session.commit()
            flash(f' {newItem.product_name} Successfully Created!', 'success')
            return redirect(url_for('allProducts'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This product already exists','danger')
            return redirect(url_for('Addproduct'))
    else:
        return render_template('addProduct.html')

#Edit a  product
@app.route('/product/<int:product_id>/edit/', methods = ['GET', 'POST'])
@login_required
def editProduct(product_id):
    editedItem = Product.query.filter_by(id = product_id).one()
    if request.method == 'POST':
        if request.form['product_name']:
          editedItem.product_name = request.form['product_name']
        if request.form['product_type']:
          editedItem.product_type = request.form['product_type']
        if request.form['sell_price']:
          editedItem.sell_price = request.form['sell_price'] 
        if request.form['reoder_level']:
            editedItem.reoder_level = request.form['reoder_level'] 

        db.session.add(editedItem)
        db.session.commit() 
        flash(f'Your product {editedItem.product_name}   has been updated!', 'success')
        return redirect(url_for('allProducts'))
    else:
        return render_template('editProduct.html',product_id=product_id, d = editedItem)


#Delete a product
@app.route('/products/<int:product_id>/delete/', methods = ['POST'])
@login_required
def deleteProduct(product_id):
        productToDelete = Product.query.filter_by(id = product_id).one()
        db.session.delete(productToDelete)
        db.session.commit()
        flash(f'product successfully Delete!','danger')
        return redirect(url_for('allProducts', product_id = product_id))
# API ENDPOINT
@app.route('/productprice/<product>')
def Productprice(product):
    data=Product.query.filter_by(product_name=product).all()
    dataArray=[]
    for product in data:
        productobj={}
        productobj['id']=product.id
        productobj['product_type']=product.product_type
        productobj['sell_price']=product.sell_price
        dataArray.append(productobj)
    return jsonify({'Productprice': dataArray})


# Supplier
@app.route('/suppliers/')
@login_required
def AllSuppliers():
    suppliers = Supplier.query.all()
    return render_template('allSuppliers.html',suppliers=suppliers)
    
# Add Supplier
@app.route('/addSupplier/',methods=['GET','POST'])
@login_required
def AddSupplier():
    if request.method == 'POST':
        newItem = Supplier(supplier_name=request.form['supplier_name'],supplier_phone=request.form['supplier_phone'])
        db.session.add(newItem)
        try:
            db.session.commit()
            flash(f' {newItem.supplier_name} Successfully Created!', 'success')
            return redirect(url_for('AllSuppliers'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This Supplier already exists','danger')
            return redirect(url_for('AddSupplier'))
    else:
        return render_template('addSupplier.html')

# Edit suppliers
@app.route('/supplier/<int:supplier_id>/edit/', methods = ['GET', 'POST'])
@login_required
def EditSupplier(supplier_id):
    editedItem = Supplier.query.filter_by(id = supplier_id).one()
    if request.method == 'POST':
        if request.form['supplier_name']:
          editedItem.supplier_name = request.form['supplier_name']
        if request.form['supplier_phone']:
          editedItem.supplier_phone = request.form['supplier_phone']
    
        db.session.add(editedItem)
        db.session.commit() 
        flash(f' {editedItem.supplier_name} record has been updated!', 'success')
        return redirect(url_for('AllSuppliers'))
    else:
        return render_template('editSupplier.html',supplier_id=supplier_id, s= editedItem)

@app.route('/supplier/<int:supplier_id>/delete/', methods = ['POST'])
@login_required
def deleteSupplier(supplier_id):
        supplierToDelete = Supplier.query.filter_by(id = supplier_id).one()
        db.session.delete(supplierToDelete)
        db.session.commit()
        flash(f'Supplier successfully Deleted!','danger')
        return redirect(url_for('AllSuppliers', supplier_id = supplier_id))
# Supplier API
@app.route('/supplierdata/<supplier>')
def supplierdata(supplier):
    data= Supplier.query.filter_by(supplier_name=supplier).all()
    dataArray=[]
    for supplier in data:
        supplierobj={}
        supplierobj['id']=supplier.id
        supplierobj['supplier_name']=supplier.supplier_name
        supplierobj['openbalance']=supplier.openbalance
        dataArray.append(supplierobj)
    return jsonify({'Supplies': dataArray})


# SALES
@app.route('/productsalesreport/<product>',methods=['GET'])
@login_required
def ProductSale(product):
    productsale=OrderItems.query.filter_by(product_name=product).all()
    return render_template('productsales.html',productsale=productsale,product=product)

# Purchases
@app.route('/addPurchase/',methods=['GET'])
@login_required
def AddPurchase():
    products=[p.product_name for p in Product.query.filter_by(product_type='Medication')]
    suppliers=[s.supplier_name for s in Supplier.query.all()]
    return render_template('purchase.html',products=products,suppliers=suppliers)
      
#ProcessPurchaseData
@app.route('/processpurchasedata', methods=['POST'])
def processdata():
    table= request.json
    key_list = [] 
    filter_key=[]
    product_list=[]
    date=[]
    quantityarray=[]
    price=[]
    total_amount=[]
    for dic in table:
        for key in dic:
            key_list.append(key)
    [filter_key.append(x) for x in key_list if x not in filter_key]     
    
    for data in table:
            for i in data:
                if i=="suplier_name":
                    suplier_name=data[i]
                elif i=="invoice":
                    invoice=data[i]
                elif i=="date_purchase":
                    date_purchase=data[i]
                elif i=="paytype":
                    paytype=data[i]
                elif i=="productname":
                    product_list.append(data[i])
                elif i=="expirydata":
                    date.append(data[i])
                elif i=="quantity":
                    quantityarray.append(data[i])
                elif i=="buying_price":
                    price.append(data[i])
                elif i=="total_price":
                    total_amount.append(data[i])
                elif i=="grand_total_price":
                    grand_total_price=data[i]
                elif i=="paid_amount":
                    paid_amount=data[i]
                elif i=="balance":
                    balance=data[i]
                elif i=="OpenBalance":
                    OpenBalance=data[i]
    

    invoiceNo=int(invoice)
    supplierToAdd=Supplier.query.filter_by(supplier_name=suplier_name).one()
    supplierToAdd.openbalance +=int(balance)
    supplierToAdd.openbalance -=int(OpenBalance)

    purchasez_date = date_purchase
    purchasedate_object = datetime.strptime(purchasez_date, "%Y-%m-%d").date()

    newpurchase=Purchase(purchase_date=purchasedate_object,supplier_name=suplier_name,invoice_no=invoiceNo,\
        payment_type=paytype,total_amount=grand_total_price,due_balance=balance,paydue_amount=OpenBalance,payment_amount=paid_amount,supplier=supplierToAdd)
    for (prod,expiry,qty,price,total) in zip(product_list,date,quantityarray,price,total_amount):
        expiry_date = expiry
        expirydate_object = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        product_name=Product.query.filter_by(product_name=prod).one()
        seling_price=product_name.sell_price

        itemlines=PurchaseItems(product_name=prod,invoice_no=invoiceNo,expiry_date=expirydate_object,quantity=qty,in_quantity=qty,buying_price=price,\
            total_amount=total,sell_price=seling_price,purchase=newpurchase,product=product_name)
    
    db.session.add(newpurchase)
    db.session.add(itemlines)
    db.session.add(supplierToAdd)
    try:
        db.session.commit()
        db.session.commit()
        db.session.commit()
        return jsonify({'name' : suplier_name}) 
    except IntegrityError:
        db.session.rollback()
        flash(f'Try Again ','danger')
        return jsonify({'error' : 'Invoice No already used!'})

    return jsonify({'error' : 'Invoice No already used!'})
    
# allPurchase
@app.route('/allPurchase/',methods=['GET','POST'])
@login_required
def AllPurchase():
    Purchases=Purchase.query.all()
    return render_template('allPurchases.html',Purchases=Purchases)

# ProductPuchaseDetails
@app.route('/PurchaseDetails/<int:purchase_id>/',methods=['GET','POST'])
@login_required
def PurchaseDetail(purchase_id):
    product_purchase=PurchaseItems.query.filter_by(purchase_id=purchase_id).all()
    purchase=Purchase.query.filter_by(id=purchase_id).one()
    return render_template('purchaseDetails.html',product_purchase=product_purchase,purchase_id=purchase_id,purchase=purchase)

# ProductPuchaseDetails
@app.route('/ProductPuchaseDetails/<product>/',methods=['GET','POST'])
@login_required
def ProductPurchaseDetail(product):
    product_purchase=PurchaseItems.query.filter_by(product_name=product).all()
    productPurchased=Product.query.filter_by(product_name=product).one()
    return render_template('productpurchaseinfo.html',product_purchase=product_purchase,product=product,productPurchased=productPurchased)

# Delete Purchase order
@app.route('/Purchase/<int:purchase_id>/delete',methods=['POST'])
@login_required
def DeletePurchase(purchase_id):
    # PurchaseToDelete =Purchase.query.filter_by(id = purchase_id).one()
    #     supplierId=PurchaseToDelete.supplier_id
    #     balance=PurchaseToDelete.due_balance
    #     debt_pay=PurchaseToDelete.paydue_amount
        
    #     patientToAdd=Customer.query.filter_by(id=customerId).one()
    #     patientToAdd.debt -=int(balance)
    #     patientToAdd.debt +=int(debt_pay)
       
        
    #     orderitems=OrderItems.query.filter_by(order_id=invoice_id,product_type='Medication').all()
    #     print(orderitems)
    #     for item in orderitems:
    #         prodname=item.product_name
    #         prodexpiry=item.expiry_date
    #         prodquanty=item.quantity

    #         stock_item=PurchaseItems.query.filter_by(product_name=prodname,expiry_date=prodexpiry).first()
    #         print(stock_item.quantity)
    #         stock_item.quantity += prodquanty

    #         db.session.add(stock_item)
    #         db.session.commit()

    #         db.session.delete(item)
    #         db.session.commit()

    #     allorderservice=OrderItems.query.filter_by(order_id=invoice_id,product_type='Service').all()
    #     for service in allorderservice:
    #         db.session.delete(service)
    #         db.session.commit()
            
    #     db.session.add(patientToAdd)
    #     db.session.commit()

    #     db.session.delete(InvoiceToDelete)
    #     db.session.commit()

    flash(f'Puchase  successfully Deleted!','danger')
    return redirect(url_for('AllPurchase'))

# Add Expences
@app.route('/addexpensecategory/',methods=['GET','POST'])
@login_required
def AddExpenseCategory():
    if request.method == 'POST':
        newItem = Expense(ExpenseCategory_name=request.form['ExpenseCategory_name'])
        db.session.add(newItem)
        try:
            db.session.commit()
            flash(f' {newItem.ExpenseCategory_name} Successfully Added!', 'success')
            return redirect(url_for('AllExpenses'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This Expense Category already exists','danger')
            return redirect(url_for('AddExpenseCategory'))
    else:
        return render_template('addExpenseCategory.html')

# all Expences
@app.route('/allexpenses/')
@login_required
def AllExpenses():
    Expensecategory = Expense.query.all()
    return render_template('allExpenseCategory.html',Expensecategory=Expensecategory)


# edit expense
@app.route('/expense/<int:expense_id>/edit/', methods = ['POST'])
@login_required
def editexpe(expense_id):

    editedItem = Expense.query.filter_by(id =expense_id).one()
    editedItem.ExpenseCategory_name = request.form['expense']
    db.session.add(editedItem)
    db.session.commit() 
    flash(f'expense has been updated!', 'success')
    return redirect(url_for('AllExpenses'))
    

# delete expense
@app.route('/expense/<int:expense_id>/delete/', methods = ['POST'])
@login_required
def deleteExpense(expense_id):
        expenseToDelete = Expense.query.filter_by(id = expense_id).one()
        db.session.delete(expenseToDelete)
        db.session.commit()
        flash(f'Expense successfully Deleted!','danger')
        return redirect(url_for('AllExpenses', expense_id = expense_id))

# TrackExpense
@app.route('/trackexpenses/',methods=['GET','POST'])
@login_required
def TrackExpenses():
    entries=[E.ExpenseCategory_name for E in Expense.query.all()]
    if request.method == 'POST':
        date_str = request.form['dtpDate']
        date_object = datetime.strptime(date_str, "%Y-%m-%d").date()
        newItem = TrackExpense(created_on=date_object,expense_type=request.form['expense_type'],payment_type=request.form['paytype'],amount=int(request.form['amount']))
        db.session.add(newItem)
        try:
            db.session.commit()
            flash(f' {newItem.expense_type} Successfully Added!', 'success')
            return redirect(url_for('AllTrackedExpenses'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This Expense Category already exists','danger')
            return redirect(url_for('TrackExpenses'))
    else:
        return render_template('trackExpense.html',entries=entries)

# all tracked Expences
@app.route('/alltrackedexpenses/',methods=['GET','POST'])
@login_required
def AllTrackedExpenses():
    trackedexpense=TrackExpense.query.all()
    return render_template("expenseStatement.html",trackedexpense=trackedexpense)

# All stock
@app.route('/stockreport/',methods=['GET','POST'])
@login_required
def StockReport():
    stock=PurchaseItems.query.all()
    return render_template("stockreport.html",stock=stock)

@app.route('/salesreport/',methods=['GET','POST'])
@login_required
def ProductDetailsReport():
    return render_template("productReport.html")

# sales report (med)
@app.route('/medicationsalesreport/',methods=['GET','POST'])
@login_required
def MedicationSalesReport():
    sales=OrderItems.query.with_entities(OrderItems.product_name,OrderItems.buying_price,func.sum(OrderItems.quantity).label('total_quantity') ,func.sum(OrderItems.total_amount).label('total_amount')).group_by(OrderItems.product_name).filter_by(product_type='Medication').all()
    return render_template("medsalesreport.html",sales=sales)


# Invoicereceipt
@app.route('/receipt/',methods=['GET','POST'])
@login_required
def Receipt():
    return render_template("receipt.html")

# account reports

@app.route('/profitlossreport/',methods=['GET','POST'])
@login_required
def IncomeExpense():
    return render_template('incomeExpense.html')

@app.route('/statementreceipt/',methods=['POST'])
@login_required
def StatementReceipt():
    if request.method == 'POST':
        startdate_object = request.form['Start_Date']
        startdate = datetime.strptime(startdate_object, "%Y-%m-%d").date()

        enddate_object = request.form['End_Date']
        endDate = datetime.strptime(enddate_object, "%Y-%m-%d").date()

     
        qry=Order.query.filter(Order.created_on.between(startdate,endDate))

        if qry:
            ordIdlist=[x.id for x in qry]
            def retprodamntlist():
                allpodlist=[]
                for x in ordIdlist:
                    orderlines=OrderItems.query.filter(and_(OrderItems.order_id== x, OrderItems.product_type == 'Medication')).all()
                    prodsaleamnt=[x.total_amount for x in orderlines]
                    
                    def retprdamoun():
                        return[x for x in prodsaleamnt]
                    a=retprdamoun()
                    sums=sum(a)
                    allpodlist.append(sums)
                return allpodlist
            def retseramntlist():
                allserlilist=[]
                for x in ordIdlist:
                    orderlines=OrderItems.query.filter(and_(OrderItems.order_id== x, OrderItems.product_type == 'Service')).all()
                    servsaleamnt=[x.total_amount for x in orderlines]
                    def retseramoun():
                        return[x for x in servsaleamnt]
                    a=retseramoun()
                    sums=sum(a)
                    allserlilist.append(sums)
                return allserlilist
                
        productsale_list = retprodamntlist()
        servicesale_list = retseramntlist()
        Totalproductsale_Amount=sum(productsale_list)
        Totalservsale_Amount=sum(servicesale_list)
        
       
        productpurchasedata =Purchase.query.filter((Purchase.purchase_date.between(startdate,endDate)))
        costofpurchase=[x.total_amount for x in productpurchasedata]
        totalpurchasecost=sum(costofpurchase)

    
        allexpenses=TrackExpense.query.filter(TrackExpense.created_on.between(startdate,endDate))
        def dictexpes():
            mainexpdic=[]
            for x in allexpenses:
                dic={x.expense_type : x.amount}
                mainexpdic.append(dic)
            return mainexpdic
                
        expenses=dictexpes()
    
        expensesresult={"Cost of goods Sold":totalpurchasecost}
        for x in expenses:
            for i in x.keys():
                expensesresult[i]=expensesresult.get(i, 0) + x[i]

        allexpenses_values=[]
        for key,value in expensesresult.items():
            allexpenses_values.append(value)
        
        total_expense_amount=sum(allexpenses_values)
        total_income=Totalservsale_Amount+Totalproductsale_Amount 
        Profit_loss=total_income-total_expense_amount
        
        header_startdate=startdate.strftime("%A, %d %b %Y")
        header_enddate=endDate.strftime("%A, %d %b %Y")
    return render_template('incomeExpenseStatemnt.html',Totalproductsale_Amount=Totalproductsale_Amount,\
        Totalservsale_Amount=Totalservsale_Amount,expensesresult=expensesresult,header_startdate=header_startdate,header_enddate=header_enddate,\
            total_income=total_income,total_expense_amount=total_expense_amount,Profit_loss=Profit_loss)

@app.route('/processprofitlossreport/',methods=['POST'])
@login_required
def ProcessIncomeExpenseData():

    data_obj= request.get_json()

    startdate=data_obj['start_date']
    endDate=data_obj['end_date']
   
    qry=Order.query.filter(Order.created_on.between(startdate,endDate))

    if qry:
        ordIdlist=[x.id for x in qry]
        def retprodamntlist():
            allpodlist=[]
            for x in ordIdlist:
                orderlines=OrderItems.query.filter(and_(OrderItems.order_id== x, OrderItems.product_type == 'Medication')).all()
                prodsaleamnt=[x.total_amount for x in orderlines]
                
                def retprdamoun():
                    return[x for x in prodsaleamnt]
                a=retprdamoun()
                sums=sum(a)
                allpodlist.append(sums)
            return allpodlist
        def retseramntlist():
            allserlilist=[]
            for x in ordIdlist:
                orderlines=OrderItems.query.filter(and_(OrderItems.order_id== x, OrderItems.product_type == 'Service')).all()
                servsaleamnt=[x.total_amount for x in orderlines]
                def retseramoun():
                    return[x for x in servsaleamnt]
                a=retseramoun()
                sums=sum(a)
                allserlilist.append(sums)
            return allserlilist
            
    productsale_list = retprodamntlist()
    servicesale_list = retseramntlist()
    Totalproductsale_Amount=sum(productsale_list)
    Totalservsale_Amount=sum(servicesale_list)

   

    productpurchasedata =Purchase.query.filter((Purchase.purchase_date.between(startdate,endDate)))
    costofpurchase=[x.total_amount for x in productpurchasedata]
    totalpurchasecost=sum(costofpurchase)
   
    incomepurchasedata={"productsale":Totalproductsale_Amount,"servsale":Totalservsale_Amount}

    allexpenses=TrackExpense.query.filter(TrackExpense.created_on.between(startdate,endDate))
    def dictexpes():
        mainexpdic=[]
        for x in allexpenses:
            dic={x.expense_type : x.amount}
            mainexpdic.append(dic)
        return mainexpdic
            
    expenses=dictexpes()
 
    expensesresult={"productpurchase":totalpurchasecost}
    for x in expenses:
        for i in x.keys():
            expensesresult[i]=expensesresult.get(i, 0) + x[i]

    def mergeDict(d1, d2):
        merged = d1.copy()
        merged.update(d2)
        return merged

    mrgDictdata= mergeDict(incomepurchasedata,expensesresult)
    data=[]
    data.append(mrgDictdata)
    
    respnd= make_response(jsonify(data),200)

    return respnd

# logout 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
