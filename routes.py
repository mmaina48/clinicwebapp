from flask import  render_template,url_for,redirect,flash,request,jsonify,make_response,session,g
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from main import app,db
from forms import LoginForm,RegisterForm,allroles,changepassForm
from models import User,Product,Supplier,product_orders,product_purchases,Purchase,Order,Expense,TrackExpense,\
    PurchaseItems,Customer,OrderItems,Visits,Consultation,LabResult
import time,datetime
from sqlalchemy import desc,asc
from sqlalchemy import and_,or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
import itertools
import re
from operator import itemgetter 
from datetime import date,datetime,timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'






@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def before_request():
    g.user = current_user

# functions to DEFINE PERMISSIONS
def required_roles(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if get_current_user_role() not in roles:
                flash(f'You are not authorised to access this page.','danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapped
    return wrapper
    
def get_current_user_role():
    return g.user.role

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)

# ---------------------------------------------------------------------------------------------

# User login
@app.route('/')
@app.route('/login', methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(username=form.username.data).first()
        print(user)
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=True)
                if user.role=="Admin":
                    return redirect(url_for('Admindashbord'))
                elif user.role=="Cashier":
                    return redirect(url_for('Cashierdashboard'))
                elif user.role=="Nurse":
                    return redirect(url_for('Nursesdashbord'))
                elif user.role=="Doctor":
                    return redirect(url_for('Doctorsdashboard'))
                elif user.role=="Labtech":
                    return redirect(url_for('Labtechdashbord'))
                elif user.role=="Pharmacist":
                    return redirect(url_for('Pharmacistdashboard'))
            else:
                flash(f'Incorrect Username or password','danger')
                return redirect(url_for('login'))
        return redirect(url_for('login'))
    return render_template('login.html',form=form)  


# -------------------------------------------------------------------------------------------------

# Users
#all system Users
@app.route('/allusers/',methods=['GET','POST'])
@login_required
def AllUsers():
    users=User.query.all()
    return render_template('allusers.html',users=users)

# add users 
@app.route('/signup/',methods=['GET','POST'])
# @login_required
# @required_roles('Admin')
def signup():
    form=RegisterForm()
    if form.validate_on_submit():
        hashed_password= generate_password_hash(form.password.data, method='sha256')
        newuser = User(username=form.username.data,role=dict(allroles).get(form.memberrole.data), password=hashed_password )
        db.session.add(newuser)
        try:
            db.session.commit()
            flash(f' {newuser.username} Successfully Added!', 'success')
            return redirect(url_for('AllUsers'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This User already exists','danger')
            return redirect(url_for('signup'))
    return render_template('adduser.html', form=form)

#Edit User
@app.route('/users/<int:user_id>/edit/', methods = ['GET', 'POST'])
@login_required
@required_roles('Admin')
def editUser(user_id):
    form = changepassForm()
    editeduser =User.query.filter_by(id = user_id).one()
    hashed_password= generate_password_hash(form.editpassword.data, method='sha256')
    if request.method == 'POST':
        if form.editusername.data:
          editeduser.username = form.editusername.data
        if form.editpassword.data:
          editeduser.password = hashed_password
        if form.editmemberrole.data:
          editeduser.password = form.editmemberrole.data
        db.session.add(editeduser)
        db.session.commit() 
        flash(f'{form.editusername.data}  has been updated!', 'success')
        return redirect(url_for('AllUsers'))
    else:
        return render_template('edituser.html',user_id=user_id,editeduser = editeduser,form=form)

#Delete Patient
@app.route('/user/<int:user_id>/delete/', methods = ['POST'])
@login_required
def deleteUser(user_id):
        userToDelete =User.query.filter_by(id = user_id).one()
        db.session.delete(userToDelete)
        db.session.commit()
        flash(f'User successfully Deleted!','danger')
        return redirect(url_for('AllUsers'))

# ----------------------------------------------------------------------------------------------
# ALL DASHBOARDS
# admins
@app.route('/AdminDashboard/',methods=['GET','POST'])
@login_required
def Admindashbord():
    return render_template('admindashboard.html',username=current_user.username)




# Cashiers
@app.route('/CashierDashboard/',methods=['GET','POST'])
@login_required
def Cashierdashbord():
    return render_template('cashierdashboard.html',username=current_user.username)


# ----------------------------------------------------------------------------------------------
# Patients
#all patients
@app.route('/allpatients/',methods=['GET','POST'])
@login_required
def AllCustomers():
    customers=Customer.query.all()
    return render_template('allCustomers.html',customers=customers)


#add patient by save 
@app.route('/addpatient/',methods=['GET','POST'])
@login_required
def AddCustomer():
    # generating a patient id function
    

    if request.method == 'POST':

        
       
        try:
            pid=db.session.query(db.func.max(Customer.id)).one()


            def patientid(setids):
                import datetime
                id=['0' if v is None else v for v in setids]
                year=str(datetime.date.today().year) + '/100'
                patient_id=year+ str(id[0])
                return patient_id
            opd=patientid(pid)

            newcustomer = Customer(patient_id=opd,name=request.form['patient_name'],\
            age=request.form['age'],gender=request.form['gendertype'],\
            patient_phone=request.form['patient_phone'],nhif_no=request.form['patient_nhif_no'],\
            National_id=request.form['patient_National_id'])
            db.session.add(newcustomer)
            db.session.commit()
            flash(f' {newcustomer.name} Successfully Added!', 'success')
            return redirect(url_for('AddCustomer'))
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


# ------------------------------------------------------------------------------------------
# Vitals

# Nurse's
@app.route('/NursesDashboard/',methods=['GET','POST'])
@login_required
def Nursesdashbord():
    return render_template('nursedashboard.html',username=current_user.username)


#Nurser View  all patient data
@app.route('/viewallpatientdata/',methods=['GET','POST'])
@login_required
def NurseAllPatientview():
    allpatients=Customer.query.all()
    return render_template('nurseviewallpatients.html',username=current_user.username,allpatients=allpatients)

#Nurser View  all patient vitals
@app.route('/Allpatientview/',methods=['GET','POST'])
@login_required
def NurseAllPatient():
    allvitals=Visits.query.all()
    return render_template('allpatientnurse.html',username=current_user.username,allvitals=allvitals)


@app.route('/CaptureVitalsWaitingList', methods=['GET','POST'])
@login_required
def CaptureVitalQueue():
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    todays_captured_vital=Visits.query.filter(Visits.inserted_on>yesterday).all()
    patientids=[vital.order_id for vital in todays_captured_vital]
    
    print(patientids)
    # get all walkins
    walkins=db.session.query(Order).filter(and_( Order.inserted_on>yesterday,\
    Order.customer_name=="WALK-IN")).all()
    walkinsids=[otc.id for otc in walkins]
    if not walkinsids:
        walkinsids.append(0)

    print(walkinsids)
    patient_with_no_conslt=db.session.query(Order).filter(and_( Order.inserted_on>yesterday,\
        ~Order.id.in_(patientids),~Order.id.in_(walkinsids))).order_by(desc(Order.inserted_on)).all()
    exists= bool(patient_with_no_conslt)
    if exists == False:
        flash(f'NO PATIENT ON THE WAITING QUEUE','danger')
    return render_template('vitalqueue.html',patient_with_no_conslt=patient_with_no_conslt)


@app.route('/CaptureVital/<int:patient_id>/', methods=['GET','POST'])
@login_required
def PatientVital(patient_id):

    patient=Customer.query.filter_by(id=patient_id).first()
    patientname=patient.name.upper()
    clinicid=patient.id

    
    if request.method == 'POST':

        # convert stringto date object because SQLite Date type only accepts Python date objects as input
        today = date.today()
        yesterday = today - timedelta(days = 1) 
        todays_captured_vital=Visits.query.filter(Visits.inserted_on>yesterday).all()
        patientids=[vital.order_id for vital in todays_captured_vital]

        todaysinvoice=db.session.query(Order).filter(and_( Order.inserted_on >yesterday,Order.customer_id== clinicid,\
            ~Order.id.in_(patientids))).first()

        print(todaysinvoice)
        order_id=todaysinvoice.id
        vitalDate = request.form['invoice_date']
        vitalDate_object = datetime.strptime(vitalDate, "%Y-%m-%d").date()
        newvital=Visits(patient_name=request.form['patient_name'],\
            patient_id=request.form['patient_Id'],visit_type=request.form['visittype'],visit_date=vitalDate_object,\
            height=request.form['patient_height'],weight=request.form['patient_weight'],\
            bmi=request.form['patient_BMI'],temparature=request.form['patient_Temp'],\
            bloodpressure=request.form['patient_BP'],pulse=request.form['patient_Pulse'],\
            respiratory_rate=request.form['patient_Rrate'],oxygesaturation=request.form['patient_BOS'],\
            customer_id=patient.id,order_id=order_id)
        
        print(newvital)
        db.session.add(newvital)
        try:
            db.session.commit()
            flash(f' {newvital.patient_name} record Successfully Added!', 'success')
            return redirect(url_for('PatientVital',patient_id=patient_id))
        except IntegrityError:
            db.session.rollback()
            flash(f'Try Again ','danger')
            return redirect(url_for('PatientVital',patient_id=patient_id))
    else:
        return render_template('vitals.html',patient_id=patient_id,patient=patient,\
            patientname=patientname)

#new patient vital
@app.route('/patients/<int:patient_id>/')
@app.route('/patients/<int:patient_id>/vitals/')
@login_required
def showallvitals(patient_id):
    print(patient_id)
    patient=Customer.query.filter_by(id=patient_id).one()
    patvisits=Visits.query.filter_by(customer_id=patient_id).order_by(desc(Visits.inserted_on)).all()
    exists= bool(Visits.query.filter_by(customer_id=patient_id).all())
    if exists == False:
        flash(f'No Vitals  for {patient.name},Click Add Vitals','info')
    return render_template('AllpatientVitals.html',patient=patient,patvisits=patvisits,patient_id=patient_id)

# -------------------------------
# Admin Nurse View
@app.route('/AdminCaptureVitalsWaitingList/Admin/view/', methods=['GET','POST'])
@login_required
def AdminCaptureVitalQueue():
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    todays_captured_vital=Visits.query.filter(Visits.inserted_on>yesterday).all()
    patientids=[vital.order_id for vital in todays_captured_vital]
    
    print(patientids)
    # get all walkins
    walkins=db.session.query(Order).filter(and_( Order.inserted_on>yesterday,\
    Order.customer_name=="WALK-IN")).all()
    walkinsids=[otc.id for otc in walkins]
    if not walkinsids:
        walkinsids.append(0)

    print(walkinsids)
    patient_with_no_conslt=db.session.query(Order).filter(and_( Order.inserted_on>yesterday,\
        ~Order.id.in_(patientids),~Order.id.in_(walkinsids))).order_by(desc(Order.inserted_on)).all()
    exists= bool(patient_with_no_conslt)
    if exists == False:
        flash(f'NO PATIENT ON THE WAITING QUEUE','danger')
    return render_template('adminviewvitalqueue.html',patient_with_no_conslt=patient_with_no_conslt)


# Admin Enter Vitals
@app.route('/Admin/CaptureVital/<int:patient_id>/', methods=['GET','POST'])
@login_required
def AdminAddPatientVital(patient_id):
    patient=Customer.query.filter_by(id=patient_id).first()
    patientname=patient.name.upper()
    clinicid=patient.id

    
    if request.method == 'POST':

        # convert stringto date object because SQLite Date type only accepts Python date objects as input
        today = date.today()
        yesterday = today - timedelta(days = 1) 
        todays_captured_vital=Visits.query.filter(Visits.inserted_on>yesterday).all()
        patientids=[vital.order_id for vital in todays_captured_vital]

        todaysinvoice=db.session.query(Order).filter(and_( Order.inserted_on >yesterday,Order.customer_id== clinicid,\
            ~Order.id.in_(patientids))).first()

        print(todaysinvoice)
        order_id=todaysinvoice.id
        vitalDate = request.form['invoice_date']
        vitalDate_object = datetime.strptime(vitalDate, "%Y-%m-%d").date()
        newvital=Visits(patient_name=request.form['patient_name'],\
            patient_id=request.form['patient_Id'],visit_type=request.form['visittype'],visit_date=vitalDate_object,\
            height=request.form['patient_height'],weight=request.form['patient_weight'],\
            bmi=request.form['patient_BMI'],temparature=request.form['patient_Temp'],\
            bloodpressure=request.form['patient_BP'],pulse=request.form['patient_Pulse'],\
            respiratory_rate=request.form['patient_Rrate'],oxygesaturation=request.form['patient_BOS'],\
            customer_id=patient.id,order_id=order_id)
        
        print(newvital)
        db.session.add(newvital)
        try:
            db.session.commit()
            flash(f' {newvital.patient_name} record Successfully Added!', 'success')
            return redirect(url_for('AdminAddPatientVital',patient_id=patient_id))
        except IntegrityError:
            db.session.rollback()
            flash(f'Try Again ','danger')
            return redirect(url_for('AdminAddPatientVital',patient_id=patient_id))
    else:
        return render_template('adminaddvitals.html',patient_id=patient_id,patient=patient,\
            patientname=patientname)

#Admin View all vitals taken for a patient
@app.route('/patients/<int:patient_id>/')
@app.route('/patients/<int:patient_id>/Admin/vitals/')
@login_required
def AdminViewallvitalsFor(patient_id):
    print(patient_id)
    patient=Customer.query.filter_by(id=patient_id).one()
    patvisits=Visits.query.filter_by(customer_id=patient_id).order_by(desc(Visits.inserted_on)).all()
    exists= bool(Visits.query.filter_by(customer_id=patient_id).all())
    if exists == False:
        flash(f'No Vitals  for {patient.name},Click Add Vitals','info')
    return render_template('adminviewAllVitalsfor.html',patient=patient,patvisits=patvisits,patient_id=patient_id)


# ---------------------------------------------------------------------------------------------

# Doctorsdashboard
@app.route('/DoctorsDashboard/',methods=['GET','POST'])
@login_required
def Doctorsdashboard():
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    todays_consultations=Consultation.query.filter(Consultation.inserted_on>yesterday).all()
    patientids=[conslt.order_id for conslt in todays_consultations]
    
    todays_captured_vital=Visits.query.filter(Visits.inserted_on>yesterday).all()
    vitalids=[vital.order_id for vital in todays_captured_vital]

    patient_with_no_conslt_with_vitals=db.session.query(Order).filter(and_( Order.inserted_on>yesterday,\
        ~Order.id.in_(patientids),Order.id.in_(vitalids))).order_by(desc(Order.inserted_on)).all()
    
    exists= bool(patient_with_no_conslt_with_vitals)
    if exists == False:
        flash(f'NO PATIENT ON THE WAITING QUEUE','danger')

    # count the number of requests
    requests=[req.id for req in patient_with_no_conslt_with_vitals]
    notification=len(requests)

    # results queue
    # get all order
    orderliine_with_lab=Order.query.filter(Order.inserted_on > yesterday).all()
    
    # get all ids 
    order_with_lab_med=[item.id for item in orderliine_with_lab]
    
    
    orders_dispensed=db.session.query(OrderItems).filter(and_(OrderItems.inserted_on >yesterday,\
        OrderItems.order_id.in_(order_with_lab_med),OrderItems.product_type=="Medication")).all()
    
    ids_with_meds=[item.order_id for item in orders_dispensed]

    doct_lab_results=db.session.query(LabResult).filter(and_(LabResult.inserted_on >yesterday,\
        ~LabResult.order_id.in_(ids_with_meds)))

    resultsback=[x.id for x in doct_lab_results]
    notifcations_results_back=len(resultsback)
    return render_template('doctordashboard.html',username=current_user.username,\
        patient_with_no_conslt_with_vitals=patient_with_no_conslt_with_vitals,notification=notification,\
            notifcations_results_back=notifcations_results_back)


# doctoraddconsultation
@app.route('/addconsultation/<int:patient_id>/', methods=['GET','POST'])
@login_required
def DoctorAddVisitNotes(patient_id):
    patient=Customer.query.filter_by(id=patient_id).one()
    capital_name=patient.name.upper()
    patientID=patient.id
    today = date.today()

    invoice=db.session.query(Order).filter(or_( Order.inserted_on ==today,Order.customer_id== patientID)).order_by(desc(Order.inserted_on)).first()
    if invoice is None:
        flash(f'{patient.name} has not paid for consultation', 'danger')
        return redirect(url_for('AllCustomers'))
    else:
        invoice_id=invoice.id
        clinicid=patient.patient_id
        vital=db.session.query(Visits).filter(or_( Visits.inserted_on ==today,Visits.patient_id== clinicid)).order_by(desc(Visits.inserted_on)).first()

        exists=bool(vital)
        if exists == False:
            flash(f'PATIENT VITALS NOT CAPTURED','danger')
    
        todaysinvoice=db.session.query(Order).filter(or_( Order.inserted_on ==today,Order.patient_id== clinicid)).first()
        if todaysinvoice:
            vistType=todaysinvoice.visit_type
        else:
            vistType='OPD'

        return render_template('doctoraddconsul.html',patient_id=patient_id,patient=patient,\
                vistType=vistType,vital=vital,invoice_id=invoice_id,capital_name=capital_name)


# ajax POST call
@app.route('/processconsultatonnotes', methods=['POST'])
@login_required
def processvisitnotes():
    table= request.json
    print(table)

    for data in table:
        for i in data:
            if i=="patient_name":
                patient_name=data[i]
            elif i=="visittype":
                visittype=data[i]
            elif i=="patient_Id":
                patient_Id=data[i]
            elif i=="invoice_date":
                invoice_date=data[i]
            elif i=="invoice_id":
                invoice_id=data[i]
            elif i=="chief_complain":
                chief_complain=data[i]
            elif i=="patient_history":
                patient_history=data[i]
            elif i=="clinical_note":
                clinical_note=data[i]
            elif i=="height":
                height=data[i]
            elif i=="weight":
                weight=data[i]
            elif i=="BMI":
                BMI=data[i]
            elif i=="temp":
                temp=data[i]
            elif i=="BP":
                BP=data[i]
            elif i=="pulse":
                pulse=data[i]
            elif i=="respRate":
                respRate=data[i]
            elif i=="BOS":
                BOS=data[i]
            elif i=="primary_diagnosis":
                primary_diagnosis=data[i]
            elif i=="Secondary_diagnosis":
                Secondary_diagnosis=data[i]

    # Get customer_id 
    patient=Customer.query.filter_by(patient_id=patient_Id).first()
   
    # convert date to python date object
    invoiceDate = invoice_date
    invoiceDate_object = datetime.strptime(invoiceDate, "%Y-%m-%d").date()

    # save data into db
    newvisit=Consultation(patient_name=patient_name,patient_id=patient_Id,visit_type=visittype,visit_date=invoiceDate_object,height=height,weight=weight,bmi=BMI,temparature=temp,\
        bloodpressure=BP,pulse=pulse,respiratory_rate=respRate,oxygesaturation=BOS,\
        chiefcomplain=chief_complain,patienthistory=patient_history,clinicalnote=clinical_note,\
        diagnosis=primary_diagnosis,secondarydiagnosis=Secondary_diagnosis,customer_id=patient.id,order_id=invoice_id)
    db.session.add(newvisit)
    db.session.commit()

    return jsonify({'result':'sucesss'}) 


# View previews visit note for specific patient
# Update Visit
@app.route('/patients/<int:patient_id>/visits/<int:visit_id>/edit',methods=['GET', 'POST'])
@login_required
def updatePatientVisit(patient_id,visit_id):
    print(patient_id,visit_id)
    patient=Customer.query.filter_by(id=patient_id).one()
    clinicid=patient.patient_id
    today = date.today()

    todaysinvoice=db.session.query(Order).filter(or_( Order.inserted_on ==today,Order.patient_id== clinicid)).first()
    if todaysinvoice:
        vistType=todaysinvoice.visit_type
    else:
        vistType='OPD'
    invoice_id=todaysinvoice.id
    editedVisit = Consultation.query.filter_by(id=visit_id).one()

    return render_template('docviewconsultation.html',patient_id=patient_id,patient=patient,\
            vistType=vistType,visit=editedVisit,invoice_id=invoice_id,visit_id=visit_id)


# use ajax call to update consultation
@app.route('/updateconsultatonnotes', methods=['POST'])
@login_required
def updatevisitnotes():
    table= request.json
    print(table)

    for data in table:
        for i in data:
            if i=="visittype":
                visittype=data[i]
            elif i=="invoice_date":
                invoice_date=data[i]
            elif i=="visit_id":
                visit_id=data[i]
            elif i=="chief_complain":
                chief_complain=data[i]
            elif i=="patient_history":
                patient_history=data[i]
            elif i=="clinical_note":
                clinical_note=data[i]
            elif i=="primary_diagnosis":
                primary_diagnosis=data[i]
            elif i=="Secondary_diagnosis":
                Secondary_diagnosis=data[i]

    # Get visit to edit
    editedVisit = Consultation.query.filter_by(id=visit_id).one()

    visitDate = invoice_date
    visitDate_object = datetime.strptime(visitDate, "%Y-%m-%d").date()

    if visittype:
        editedVisit.visit_type = visittype

    if visitDate_object:
        editedVisit.visit_date = visitDate_object

    if chief_complain:
        editedVisit.chiefcomplain = chief_complain

    if patient_history:
        editedVisit.patienthistory = patient_history

    if clinical_note:
        editedVisit.clinicalnote = clinical_note

    if primary_diagnosis:
        editedVisit.diagnosis = primary_diagnosis

    if Secondary_diagnosis:
        editedVisit.secondarydiagnosis =Secondary_diagnosis
    

    db.session.add(editedVisit)
    db.session.commit()

    return jsonify({'result':'sucesss'}) 


# Doctor add treatment and LabResult
@app.route('/doctoraddtreatment/<int:invoice_id>/add',methods=['GET','POST'])
@login_required
def DoctorAddPrescription(invoice_id):
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    product_purchase=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.order_id==invoice_id)).order_by(asc(OrderItems.inserted_on)).all()
    order=Order.query.filter_by(id=invoice_id).one()
    patient_id=order.customer_id
    patient_name=order.customer_name
    patient_data=Customer.query.filter_by(name=patient_name).first()
    current_debt=patient_data.debt
    patients=[s.name for s in Customer.query.all()]
    products=[p.product_name for p in Product.query.all()]
    patientdetails=Customer.query.filter_by(id=patient_id).one()
    patvisits=Consultation.query.filter_by(customer_id=patient_id).order_by(desc(Consultation.inserted_on)).first()
    return render_template('doctoraddprescription.html',patients=patients,product_purchase=product_purchase,invoice_id=invoice_id,order=order,patientdetails=patientdetails,\
        products=products,current_debt=current_debt,patvisits=patvisits,patient_id=patient_id)


# doctor view treatemnt and lab request
@app.route('/viewtreatment/<int:invoice_id>/view',methods=['GET','POST'])
@login_required
def DoctorViewTreatment(invoice_id):
    consultation_list=db.session.query(OrderItems).filter(and_( OrderItems.order_id==invoice_id,\
        OrderItems.product_name.like('Consulta%'))).all()
    consultation_list_id=[]
    for consult in consultation_list:
        consultation_list_id.append(consult.id)
    
    product_purchase=db.session.query(OrderItems).filter(and_( OrderItems.order_id==invoice_id,\
        ~OrderItems.id.in_(consultation_list_id))).all()
    order=Order.query.filter_by(id=invoice_id).one()
    patient_id=order.customer_id
    patient_name=order.customer_name
    patvisits=Consultation.query.filter_by(customer_id=patient_id).order_by(desc(Consultation.inserted_on)).first()
    return render_template('doctorviewtreatment.html',product_purchase=product_purchase,\
        invoice_id=invoice_id,order=order,patient_name=patient_name,patient_id=patient_id,\
            patvisits=patvisits)


@app.route('/viewpatientlabresult/<int:invoice_id>/view/<int:patient_id>/',methods=['GET','POST'])
@login_required
def DoctorViewPatientLabResult(invoice_id,patient_id):
    
    patient_lab_results=LabResult.query.filter_by(order_id=invoice_id).order_by(desc(LabResult.inserted_on)).all()
    exists= bool(patient_lab_results)

    if exists == False:
        flash(f'No Results Yet','danger')
    order=Order.query.filter_by(id=invoice_id).first()
    
    visit=db.session.query(Consultation).filter(or_(Consultation.visit_date ==order.created_on,Consultation.customer_id== patient_id)).first()
    return render_template('doctorviewlabresult.html',patient_lab_results=patient_lab_results,invoice_id=invoice_id,\
        patient_id=patient_id,visit=visit,order=order)


@app.route('/patients/<int:patient_id>/')
@app.route('/patients/<int:patient_id>/visits/')
@login_required
def Doctorshowallvisits(patient_id):
    patient=Customer.query.filter_by(id=patient_id).one()
    today = date.today()
    invoice=db.session.query(Order).filter(or_( Order.inserted_on ==today,Order.customer_id== patient_id)).order_by(desc(Order.inserted_on)).first()
    invoice_id=invoice.id
    patvisits=Consultation.query.filter_by(customer_id=patient_id).order_by(desc(Consultation.inserted_on)).all()
    exists= bool(Consultation.query.filter_by(customer_id=patient_id).all())
    if exists == False:
        flash(f'No Visits  for {patient.name},Click START NEW VISIT','danger')
    return render_template('doctorviewAllpatientvisit.html',patient=patient,patvisits=patvisits,patient_id=patient_id,invoice_id=invoice_id)


# doctor view all visits
@app.route('/allvisits/')
@login_required
def DoctorallvisitsView():
    allvisitscompleted=Consultation.query.order_by(desc(Consultation.inserted_on)).all()

    exists= bool(allvisitscompleted)
    if exists == False:
        flash(f'NO VISITS RECORDS FOUND! ','danger')
    return render_template('doctorallvisitsview.html',allvisitscompleted=allvisitscompleted)


# LAB RESULTS QUEUE
@app.route('/labresultsqueue/',methods=['GET','POST'])
@login_required
def DoctorLabResultQueue():
    today = date.today()
    yesterday = today - timedelta(days = 1) 

    # get all order
    orderliine_with_lab=Order.query.filter(Order.inserted_on > yesterday).all()
    
    # get all ids 
    order_with_lab_med=[item.id for item in orderliine_with_lab]
    
    
    orders_dispensed=db.session.query(OrderItems).filter(and_(OrderItems.inserted_on >yesterday,\
        OrderItems.order_id.in_(order_with_lab_med),OrderItems.product_type=="Medication")).all()
    
    ids_with_meds=[item.order_id for item in orders_dispensed]

    doct_lab_results=db.session.query(LabResult).filter(and_(LabResult.inserted_on >yesterday,\
        ~LabResult.order_id.in_(ids_with_meds)))
    
    exists= bool(doct_lab_results)
    if exists == False:
        flash(f'NO LAB RESULTS FOUND !','danger')
    resultsback=[x.id for x in doct_lab_results]
    notifcations_results_back=len(resultsback)
    return render_template('doctorlabresultqueue.html',doct_lab_results=doct_lab_results)


# ---------------

# ADMIN CONSULTATION VIEWS
# Add Consultation
@app.route('/consultationwaitinglist', methods=['GET','POST'])
@login_required
def ConsultationQue():
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    todays_consultations=Consultation.query.filter(Consultation.inserted_on>yesterday).all()
    patientids=[conslt.order_id for conslt in todays_consultations]
    
    print(patientids)

    todays_captured_vital=Visits.query.filter(Visits.inserted_on>yesterday).all()
    vitalids=[vital.order_id for vital in todays_captured_vital]

    print(vitalids)

    patient_with_no_conslt_with_vitals=db.session.query(Order).filter(and_( Order.inserted_on>yesterday,\
        ~Order.id.in_(patientids),Order.id.in_(vitalids))).order_by(desc(Order.inserted_on)).all()
    
    print(patient_with_no_conslt_with_vitals)

    exists= bool(patient_with_no_conslt_with_vitals)
    if exists == False:
        flash(f'NO PATIENT ON THE WAITING QUEUE','danger')
    return render_template('consultationqueue.html',patient_with_no_conslt_with_vitals=patient_with_no_conslt_with_vitals)


@app.route('/Addpatientconsultation/<int:patient_id>/', methods=['GET','POST'])
@login_required
def PatientConsultation(patient_id):
    patient=Customer.query.filter_by(id=patient_id).one()
    capital_name=patient.name.upper()
    patientID=patient.id
    today = date.today()

    invoice=db.session.query(Order).filter(or_( Order.inserted_on ==today,Order.customer_id== patientID)).order_by(desc(Order.inserted_on)).first()
    if invoice is None:
        flash(f'{patient.name} has not paid for consultation', 'danger')
        return redirect(url_for('AllCustomers'))
    else:
        invoice_id=invoice.id
        clinicid=patient.patient_id
        vital=db.session.query(Visits).filter(or_( Visits.inserted_on ==today,Visits.patient_id== clinicid)).order_by(desc(Visits.inserted_on)).first()

        exists=bool(vital)
        if exists == False:
            flash(f'PATIENT VITALS NOT CAPTURED','danger')
    
        todaysinvoice=db.session.query(Order).filter(or_( Order.inserted_on ==today,Order.patient_id== clinicid)).first()
        if todaysinvoice:
            vistType=todaysinvoice.visit_type
        else:
            vistType='OPD'

        if request.method == 'POST':

            # convert stringto date object because SQLite Date type only accepts Python date objects as input

            visitDate = request.form['invoice_date']
            visitDate_object = datetime.strptime(visitDate, "%Y-%m-%d").date()
            newvisit=Consultation(patient_name=request.form['patient_name'],\
                patient_id=request.form['patient_Id'],visit_type=request.form['visittype'],visit_date=visitDate_object,\
                height=request.form['patient_height'],weight=request.form['patient_weight'],\
                bmi=request.form['patient_BMI'],temparature=request.form['patient_Temp'],\
                bloodpressure=request.form['patient_BP'],pulse=request.form['patient_Pulse'],\
                respiratory_rate=request.form['patient_Rrate'],oxygesaturation=request.form['patient_BOS'],\
                chiefcomplain=request.form['chief_complain'],patienthistory=request.form['patient_history'],\
                clinicalnote=request.form['clinical_note'],diagnosis=request.form['primary_diagnosis'],\
                secondarydiagnosis=request.form['Secondary_diagnosis'],customer_id=patient.id,order_id=invoice_id)
            db.session.add(newvisit)
            print(newvisit.clinicalnote)
            try:

                db.session.commit()
                flash(f' {newvisit.patient_name} Visit Note Successfully Added!', 'success')
                return redirect(url_for('PatientConsultation',patient_id=patient_id))

            except IntegrityError:
                db.session.rollback()
                flash(f'Try Again ','danger')
                return redirect(url_for('PatientConsultation',patient_id=patient_id))
        else:
            return render_template('consultation.html',patient_id=patient_id,patient=patient,\
                vistType=vistType,vital=vital,invoice_id=invoice_id,capital_name=capital_name)

# all Consultations
@app.route('/patients/<int:patient_id>/')
@app.route('/patients/<int:patient_id>/allvisits/')
@login_required
def showallvisits(patient_id):
    print(patient_id)
    patient=Customer.query.filter_by(id=patient_id).one()
    today = date.today()
    invoice=db.session.query(Order).filter(or_( Order.inserted_on ==today,Order.customer_id== patient_id)).order_by(desc(Order.inserted_on)).first()
    invoice_id=invoice.id
    patvisits=Consultation.query.filter_by(customer_id=patient_id).order_by(desc(Consultation.inserted_on)).all()
    exists= bool(Consultation.query.filter_by(customer_id=patient_id).all())
    if exists == False:
        flash(f'No Visits  for {patient.name},Click START NEW VISIT','danger')
    return render_template('Allpatientvisit.html',patient=patient,patvisits=patvisits,patient_id=patient_id,invoice_id=invoice_id)

# Update Visit
@app.route('/patients/<int:patient_id>/visits/<int:visit_id>/VIEW',methods=['GET', 'POST'])
@login_required
def editPatientVisit(patient_id,visit_id):
    patient=Customer.query.filter_by(id=patient_id).one()
    clinicid=patient.patient_id
    today = date.today()



    todaysinvoice=db.session.query(Order).filter(or_( Order.inserted_on ==today,Order.patient_id== clinicid)).first()

    if todaysinvoice:
        vistType=todaysinvoice.visit_type
    else:
        vistType='OPD'
    invoice_id=todaysinvoice.id
    editedVisit = Consultation.query.filter_by(id=visit_id).one()

    if request.method == 'POST':

        # convert stringto date object because SQLite Date type only accepts Python date objects as input

        visitDate = request.form['invoice_date']
        visitDate_object = datetime.strptime(visitDate, "%Y-%m-%d").date()

        if request.form['visittype']:
            editedVisit.visit_type = request.form['visittype']

        if visitDate_object:
            editedVisit.visit_date = visitDate_object

        if request.form['chief_complain']:
            editedVisit.chiefcomplain = request.form['chief_complain']

        if request.form['patient_history']:
            editedVisit.patienthistory = request.form['patient_history']

        if request.form['clinical_note']:
            editedVisit.clinicalnote = request.form['clinical_note']

        if request.form['primary_diagnosis']:
            editedVisit.diagnosis = request.form['primary_diagnosis']

        if request.form['Secondary_diagnosis']:
            editedVisit.secondarydiagnosis = request.form['Secondary_diagnosis']
    
        try:
            db.session.add(editedVisit)
            db.session.commit() 
            flash(f'visit has been updated!', 'success')
            return redirect(url_for('editPatientVisit',patient_id=patient_id,visit_id=visit_id))

        except IntegrityError:
            db.session.rollback()
            flash(f'Try Again ','danger')
            return redirect(url_for('editPatientVisit',patient_id=patient_id,visit_id=visit_id))
    else:
        return render_template('viewconsultation.html',patient_id=patient_id,patient=patient,\
            vistType=vistType,visit=editedVisit,invoice_id=invoice_id)

# add prescription
@app.route('/addprescription/<int:invoice_id>/view',methods=['GET','POST'])
@login_required
def AddPrescription(invoice_id):
    # product_purchase=OrderItems.query.filter_by(order_id=invoice_id).all()
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    product_purchase=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.order_id==invoice_id)).order_by(asc(OrderItems.inserted_on)).all()
    order=Order.query.filter_by(id=invoice_id).one()
    patient_id=order.customer_id
    patient_name=order.customer_name
    patient_data=Customer.query.filter_by(name=patient_name).first()
    current_debt=patient_data.debt
    patients=[s.name for s in Customer.query.all()]
    products=[p.product_name for p in Product.query.all()]
    patientdetails=Customer.query.filter_by(id=patient_id).one()
    patvisits=Consultation.query.filter_by(customer_id=patient_id).order_by(desc(Consultation.inserted_on)).first()
    return render_template('addprescription.html',patients=patients,product_purchase=product_purchase,invoice_id=invoice_id,order=order,patientdetails=patientdetails,\
        products=products,current_debt=current_debt,patvisits=patvisits,patient_id=patient_id)

@app.route('/viewpatienttreatment/<int:invoice_id>/view',methods=['GET','POST'])
@login_required
def ViewPreviousTreatment(invoice_id):
    consultation_list=db.session.query(OrderItems).filter(and_( OrderItems.order_id==invoice_id,\
        OrderItems.product_name.like('Consulta%'))).all()
    consultation_list_id=[]
    for consult in consultation_list:
        consultation_list_id.append(consult.id)
    
    product_purchase=db.session.query(OrderItems).filter(and_( OrderItems.order_id==invoice_id,\
        ~OrderItems.id.in_(consultation_list_id))).all()
    order=Order.query.filter_by(id=invoice_id).one()
    patient_id=order.customer_id
    patient_name=order.customer_name
    patvisits=Consultation.query.filter_by(customer_id=patient_id).order_by(desc(Consultation.inserted_on)).first()
    return render_template('viewtreatment.html',product_purchase=product_purchase,\
        invoice_id=invoice_id,order=order,patient_name=patient_name,patient_id=patient_id,\
            patvisits=patvisits)

@app.route('/Admin/viewpatientlabresult/<int:invoice_id>/view/<int:patient_id>/',methods=['GET','POST'])
@login_required
def ViewPatientLabResult(invoice_id,patient_id):
    
    patient_lab_results=LabResult.query.filter_by(order_id=invoice_id).order_by(desc(LabResult.inserted_on)).all()
    exists= bool(patient_lab_results)
    if exists == False:
        flash(f'No Results Yet','danger')
    order=Order.query.filter_by(id=invoice_id).first()
    
    visit=db.session.query(Consultation).filter(or_(Consultation.visit_date ==order.created_on,Consultation.customer_id== patient_id)).first()

    return render_template('viewlabresult.html',patient_lab_results=patient_lab_results,invoice_id=invoice_id,\
        patient_id=patient_id,visit=visit,order=order)

# --------------------------------------------------------------------------------------

# LabTechdashboard

@app.route('/LabtechDashboard/',methods=['GET','POST'])
@login_required
def Labtechdashbord():
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    todays_labresult=LabResult.query.filter(Consultation.inserted_on>yesterday).all()
    # order with results
    patientids=[labreq.order_id for labreq in todays_labresult]

    # OrderItems with lab service
    orderliine_with_lab=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.product_name.like('Lab%'))).order_by(desc(OrderItems.inserted_on)).all()

    # Orders with both lab results and lab request
    order_with_lab=[item.order_id for item in orderliine_with_lab]
    
    # remove all orders with lab results
    for x in patientids:
        if x in order_with_lab:
            order_with_lab.remove(x)
    
    # Get all orders with lab request 
    labrequest=db.session.query(Order).filter(Order.id.in_(order_with_lab))\
        .order_by(Order.inserted_on.desc()).all()
    
    # count the number of requests
    requests=[req.id for req in labrequest]
    notification=len(requests)

    exists= bool(labrequest)
    if exists == False:
        flash(f'NO PATIENT ON LAB REQUEST QUEUE','danger')
        
    return render_template('labtechdashboard.html',labrequest=labrequest,today=today,\
        notification=notification)

@app.route('/viewlabrequest/<int:invoice_id>/view',methods=['GET','POST'])
@login_required
def LabtechAddResult(invoice_id):
    order=Order.query.filter_by(id=invoice_id).one()
    labtech=User.query.filter_by(role='Labtech').all()
    labservices = db.session.query(Product).filter(Product.product_name.like('lab%')).all()
    patient_name=order.customer_name
    patient_obj=Customer.query.filter_by(id=order.customer_id).first()
    patient_id=patient_obj.id
    orderliine_with_lab=db.session.query(OrderItems).filter(and_( OrderItems.order_id==invoice_id,\
        OrderItems.product_name.like('Lab%'))).order_by(desc(OrderItems.inserted_on)).all()
    return render_template('labtecaddlabresult.html',labtech=labtech,order=order,orderliine_with_lab=orderliine_with_lab,\
    invoice_id=invoice_id,patient_name=patient_name,labservices=labservices,\
        patient_id=patient_id,username=current_user.username)


@app.route('/patientLabResults/<int:patient_id>/')
@app.route('/patientLabResults/<int:patient_id>/labresults/labtech/')
@login_required
def LabtechshowallpatientLabResults(patient_id):
    patient=Customer.query.filter_by(id=patient_id).one()
    patient_name=patient.name
    patient_lab_results=LabResult.query.filter_by(customer_id=patient_id).order_by(desc(LabResult.inserted_on)).all()
    exists= bool(patient_lab_results)
    if exists == False:
        flash(f'No Results found for {patient.name}','danger')

    today = date.today()
    yesterday = today - timedelta(days = 1) 
    orderliine_with_lab=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.product_name.like('Lab%'))).order_by(desc(OrderItems.inserted_on)).all()
    
    exists= bool(orderliine_with_lab)
    if exists == False:
        flash(f'No Lab Requests','warning')
    list_id=[]
    for item in orderliine_with_lab:
        invoice_id=item.order_id
        list_id.append(invoice_id)
    print(list_id,patient.id)

    invoice=db.session.query(Order).filter(and_(Order.id.in_(list_id),Order.customer_id==patient.id)).order_by(desc(Order.inserted_on)).first()
    invoice_id=invoice.id
    print(invoice_id)
    return render_template('labtecviewallpatientlabresults.html',patient_name=patient_name,\
        patient_lab_results=patient_lab_results,patient_id=patient_id,\
            invoice_id=invoice_id)

@app.route('/alltestsdone/')
@login_required
def labtechviewalltestdone():
    alllabtests=LabResult.query.order_by(desc(LabResult.inserted_on)).all()
    exists= bool(alllabtests)
    if exists == False:
        flash(f'NO LAB TESTS DONE ','danger')
    return render_template('laballtestsdone.html',alllabtests=alllabtests)

@app.route('/alllabservice/',methods=['GET','POST'])
@login_required
def LabViewservices():
    products = Product.query.filter(and_(Product.product_type=="Service",\
        ~Product.product_name.like('Consultation'))).all()
    return render_template('laballservices.html', products = products) 
# Add Product 
@app.route('/Lab/addservice/',methods=['GET','POST'])
@login_required
def LabAddservice():
    if request.method == 'POST':
        username=current_user.role
        newItem = Product(product_name=request.form['product_name']\
        ,product_type=request.form['product_type'],sell_price=request.form['sell_price'],\
            inserted_by=username)
        db.session.add(newItem)
        try:
            db.session.commit()
            flash(f' {newItem.product_name} Successfully Created!', 'success')
            return redirect(url_for('LabViewservices'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This product already exists','danger')
            return redirect(url_for('LabAddservice'))
    else:
        return render_template('labaddservice.html')


#Edit a  product
@app.route('/service/<int:product_id>/edit/', methods = ['GET', 'POST'])
@login_required
def LabtecheditProduct(product_id):
    editedItem = Product.query.filter_by(id = product_id).one()
    username=current_user.role
    if request.method == 'POST':
        if request.form['product_name']:
          editedItem.product_name = request.form['product_name']
    
        if request.form['sell_price']:
          editedItem.sell_price = request.form['sell_price'] 
        editedItem.inserted_by=username

        db.session.add(editedItem)
        db.session.commit() 
        flash(f'Your product {editedItem.product_name}   has been updated!', 'success')
        return redirect(url_for('LabViewservices'))
    else:
        return render_template('labtecheditservice.html',product_id=product_id, d = editedItem)


#Delete a product
@app.route('/products/<int:product_id>/labtech/delete/', methods = ['POST'])
@login_required
def LabtechdeleteProduct(product_id):
        productToDelete = Product.query.filter_by(id = product_id,).one()
        db.session.delete(productToDelete)
        db.session.commit()
        flash(f'product successfully Delete!','danger')
        return redirect(url_for('LabViewservices', product_id = product_id))


# ------------

# labADMIN
@app.route('/LabRequests/',methods=['GET','POST'])
@login_required
def AllLabRequest():
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    todays_labresult=LabResult.query.filter(LabResult.inserted_on>yesterday).all()
    # order with results
    patientids=[labreq.order_id for labreq in todays_labresult]
    print(patientids)
    # OrderItems with lab service
    orderliine_with_lab=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.product_name.like('Lab%'))).order_by(desc(OrderItems.inserted_on)).all()

    # Orders with both lab results and lab request
    order_with_lab=[item.order_id for item in orderliine_with_lab]
    
    # remove all orders with lab results
    for x in patientids:
        if x in order_with_lab:
            order_with_lab.remove(x)
    
    # Get all orders with lab request 
    labrequest=db.session.query(Order).filter(Order.id.in_(order_with_lab))\
        .order_by(Order.inserted_on.desc()).all()
    
    
    exists= bool(labrequest)
    if exists == False:
        flash(f'NO PATIENT ON LAB REQUEST QUEUE','danger')
        
    return render_template('labrequest.html',labrequest=labrequest,today=today)

@app.route('/addlabresult/<int:invoice_id>/add',methods=['GET'])
@login_required
def AddLabresult(invoice_id):
    order=Order.query.filter_by(id=invoice_id).one()
    labtech=User.query.filter_by(role='Labtech').all()
    labservices = db.session.query(Product).filter(Product.product_name.like('lab%')).all()
    patient_name=order.customer_name
    patient_obj=Customer.query.filter_by(id=order.customer_id).first()
    patient_id=patient_obj.id
    orderliine_with_lab=db.session.query(OrderItems).filter(and_( OrderItems.order_id==invoice_id,\
        OrderItems.product_name.like('Lab%'))).order_by(desc(OrderItems.inserted_on)).all()
    return render_template('addlabresult.html',labtech=labtech,order=order,orderliine_with_lab=orderliine_with_lab,\
    invoice_id=invoice_id,patient_name=patient_name,labservices=labservices,\
        patient_id=patient_id,username=current_user.username)

# this route is used by both admin and labtech
@app.route('/processlabresult', methods=['POST'])
def processlabresult():
    table= request.json
    print(table)
    test_name=[]
    test_results=[]
    lab_tech=[]
    
    for data in table:
            for i in data:
                if i=="patient_name":
                    patient_name=data[i]
                elif i=="invoice_date":
                    invoice_date=data[i]
                elif i=="patient_Id":
                    patient_Id=data[i]
                elif i=="order_id":
                    order_id=data[i]
                elif i=="visit-type":
                    visittype=data[i]
                elif i=="testname":
                    test_name.append(data[i])
                elif i=="testresult":
                    test_results.append(data[i])
                elif i=="labtech":
                    lab_tech.append(data[i])

    invoiceDate = invoice_date
    invoiceDate_object = datetime.strptime(invoiceDate, "%Y-%m-%d").date() 

    patienttested=Customer.query.filter_by(patient_id=patient_Id).first()
    print(patienttested)
    print(test_name,test_results,lab_tech)
    for (test,result,labtech) in zip(test_name,test_results,lab_tech):
        print(test,result,labtech)
        newlabresult=LabResult(patient_name=patient_name,patient_id=patient_Id,visit_date=invoiceDate_object,visit_type=visittype,\
            testname=test,testresults=result,testedby=labtech,customer=patienttested,order_id=order_id)
        print(newlabresult)
        db.session.add(newlabresult)
        db.session.commit()
        
    return jsonify({'result':'sucesss'}) 

@app.route('/patientLabResults/<int:patient_id>/')
@app.route('/patientLabResults/<int:patient_id>/labresults/')
@login_required
def showallpatientLabResults(patient_id):
    patient=Customer.query.filter_by(id=patient_id).one()
    patient_name=patient.name
    patient_lab_results=LabResult.query.filter_by(customer_id=patient_id).order_by(desc(LabResult.inserted_on)).all()
    exists= bool(patient_lab_results)
    if exists == False:
        flash(f'No Results found for {patient.name}','danger')

    today = date.today()
    yesterday = today - timedelta(days = 1) 
    orderliine_with_lab=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.product_name.like('Lab%'))).order_by(desc(OrderItems.inserted_on)).all()
    
    exists= bool(orderliine_with_lab)
    if exists == False:
        flash(f'No Lab Requests','warning')
    list_id=[]
    for item in orderliine_with_lab:
        invoice_id=item.order_id
        list_id.append(invoice_id)
    print(list_id,patient.id)

    invoice=db.session.query(Order).filter(and_(Order.id.in_(list_id),Order.customer_id==patient.id)).order_by(desc(Order.inserted_on)).first()
    invoice_id=invoice.id
    print(invoice_id)
    return render_template('allpatientlabresults.html',patient_name=patient_name,\
        patient_lab_results=patient_lab_results,patient_id=patient_id,\
            invoice_id=invoice_id)


# -----------------------------------------------------------------------------------------------


# Pharmacistdashboard
@app.route('/Pharmacist/Dashboard/',methods=['GET','POST'])
@login_required
@required_roles('Pharmacist','Admin')
def Pharmacistdashboard():
    username=current_user.username
    # get todays date and yesterdays date
    today = date.today()
    yesterday = today - timedelta(days = 1) 

    # get today orderlines with product type medication
    todays_orderlines_with_med=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.product_type.like('Medication%'))).order_by(desc(OrderItems.inserted_on)).all()
    
    # get all order ids with medications
    order_ids=[item.order_id for item in todays_orderlines_with_med]
    
    # Get all order that have medication but are still active(not dispensed)
    Patient_on_dispense_queue=db.session.query(Order).filter(and_( Order.inserted_on>yesterday,\
        Order.id.in_(order_ids),Order.status=="Active")).order_by(desc(Order.inserted_on)).all()
    
    patients=[x.id for x in Patient_on_dispense_queue]
    
    count=len(patients)
    
    return render_template('pharmdashboard.html',username=username,count=count)

# Pharm dispense queue
@app.route('/Pharmacy/dispenselist/',methods=['GET','POST'])
@login_required
@required_roles('Pharmacist','Admin')
def PharmDispenseLIst():
    # get todays date and yesterdays date
    today = date.today()
    yesterday = today - timedelta(days = 1) 

    # get today orderlines with product type medication
    todays_orderlines_with_med=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.product_type.like('Medication%'))).order_by(desc(OrderItems.inserted_on)).all()
    
    # get all order ids with medications
    order_ids=[item.order_id for item in todays_orderlines_with_med]
    
    # Get all order that have medication but are still active(not dispensed)
    Patient_on_dispense_queue=db.session.query(Order).filter(and_( Order.inserted_on>yesterday,\
        Order.id.in_(order_ids),Order.status=="Active")).order_by(desc(Order.inserted_on)).all()
    
    # Check if their is patients on Pharmacy QUEUE
    exists=bool(Patient_on_dispense_queue)
    if exists == False:
        flash(f'NO PATIENT ON DISPENSE QUEUE','danger')
    
    return render_template('pharmdispenselist.html',Patient_on_dispense_queue=Patient_on_dispense_queue)


@app.route('/pharm/view/allprescriptions/')
@login_required
def PharmViewallprescriptions():
    # get all walkins orders
    allwalkins=Order.query.filter(Order.customer_name=='WALK-IN').all()
    allwalkins_ids=[x.id for x in allwalkins]
 
    # get all orders and remove the walkins
    allinvoices=Order.query.filter(~Order.id.in_(allwalkins_ids)).order_by(Order.inserted_on.desc()).all()

    exists= bool(allinvoices)
    if exists == False:
        flash(f'NO PRESCRIPTIONS FOUND! ','danger')
    return render_template('pharmacyallprescriptions.html',allinvoices=allinvoices)


@app.route('/pharmacy/ViewPrescriptionNote/<int:invoice_id>/VIEW',methods=['GET','POST'])
@login_required
def PharmViewPrescription(invoice_id):
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    product_purchase=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.order_id==invoice_id,OrderItems.product_type.like('Medication%'))).order_by(asc(OrderItems.inserted_on)).all()
    order=Order.query.filter_by(id=invoice_id).one()
    patient_id=order.customer_id
    patient_name=order.customer_name
    patient_data=Customer.query.filter_by(name=patient_name).first()
    current_debt=patient_data.debt
    patients=[s.name for s in Customer.query.all()]
    products=[p.product_name for p in Product.query.all()]
    patientdetails=Customer.query.filter_by(id=patient_id).one()
    patvisits=Consultation.query.filter_by(customer_id=patient_id).order_by(desc(Consultation.inserted_on)).first()
    return render_template('pharmviewprescription.html',patients=patients,product_purchase=product_purchase,invoice_id=invoice_id,order=order,patientdetails=patientdetails,\
        products=products,current_debt=current_debt,patvisits=patvisits,patient_id=patient_id)


@app.route('/pharmviewprescription/<int:invoice_id>/details',methods=['GET','POST'])
@login_required
def PharmInvoiceDetail(invoice_id):
    product_purchase=OrderItems.query.filter(and_(OrderItems.order_id==invoice_id,\
        OrderItems.product_type=="Medication")).all()
    order=Order.query.filter_by(id=invoice_id).one()
    patient=order.customer_id
    patientdetails=Customer.query.filter_by(id=patient).one()
    return render_template('pharmviewprescriptionDetails.html',product_purchase=product_purchase,invoice_id=invoice_id,order=order,patientdetails=patientdetails)

#Pharm Bill OTC
@app.route('/OTCBill/new/', methods=['GET'])
@login_required
@required_roles('Pharmacist','Admin')
def PharmOTCBill():
    patient =Customer.query.filter_by(name='WALK-IN').first()
    exits=bool(patient)
    def patientid(setids):
        import datetime
        id=['0' if v is None else v for v in setids]
        year=str(datetime.date.today().year) + '/100'
        patient_id=year+ str(id[0])
        return patient_id
    if exits==False:
        pid=db.session.query(db.func.max(Customer.id)).one()
        opd=patientid(pid)
        patient1 = Customer(name = "WALK-IN",patient_id = opd,age =0, gender = "0",\
            patient_phone='0',National_id='0',nhif_no='0',debt=0)
        db.session.add(patient1)
        db.session.commit()
    patient =Customer.query.filter_by(name='WALK-IN').first()
    previusdebt=patient.debt
    products=[p.product_name for p in Product.query.all()]
    patientids=patient.patient_id
    previusdebt=patient.debt
    return render_template('pharmwalkinInvoice.html', patient_id=patientids,patient=patient,products=products,previusdebt=previusdebt,patientids=patientids)

#Pharm view all sales report
@app.route('/allWalkinBills/report/', methods=['GET'])
@login_required
@required_roles('Pharmacist','Admin')
def PharmAllOtcBill():
    # Get all WALK-IN Bills
    allotcinvoices=Order.query.filter_by(customer_name="WALK-IN")\
        .order_by(Order.inserted_on.desc()).all()
    return render_template('pharmallwalkinbills.html',allotcinvoices=allotcinvoices)

#Pharm print receipt
@app.route('/PrintOTCReceipt/<int:invoice_id>/', methods=['GET'])
@login_required
@required_roles('Pharmacist','Admin')
def PharmPrintReceipt(invoice_id):
    product_purchase=OrderItems.query.filter_by(order_id=invoice_id).all()
    order=Order.query.filter_by(id=invoice_id).one()
    username=current_user.username
    return render_template('posreceipt.html',product_purchase=product_purchase,\
        order=order,username=username)

# pharm view stock level
@app.route('/pharmstockreport/',methods=['GET','POST'])
@required_roles('Pharmacist')
@login_required
def PharmStockReport():
    stock=PurchaseItems.query.with_entities(PurchaseItems.product_name,func.sum(PurchaseItems.in_quantity).label('In_Quantity') ,func.sum(PurchaseItems.quantity).label('Current_Quantity') ,func.sum(PurchaseItems.total_amount).label('Cost_of_Goods')).group_by(PurchaseItems.product_name).all()
    return render_template("pharmstocklevel.html",stock=stock)

# pharm view stock batch wise
@app.route('/stockreportbybatch/',methods=['GET','POST'])
@login_required
def pharmStockReportbatch():
    stock=PurchaseItems.query.all()
    return render_template("pharmstockreportbatch.html",stock1=stock)


#pharm inventory sold report(cumulative)
@app.route('/inventorysoldreport/',methods=['GET','POST'])
@login_required
def PharmMedicationSalesReport():
    # get todays date and yesterdays date
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    
    orders=Order.query.filter(Order.created_on>yesterday).all()
    orders_idz=[x.id for x in orders]
        
    if request.method == 'POST':
        try:
            startdate_object = request.form['Start_Date']
            startdate = datetime.strptime(startdate_object, "%Y-%m-%d").date()
            
            enddate_object = request.form['End_Date']
            endDate = datetime.strptime(enddate_object, "%Y-%m-%d").date()
            
            orders=Order.query.filter(and_(Order.created_on>=startdate,Order.created_on<=endDate)).all()
            orders_ids=[x.id for x in orders]
        
            sales=db.session.query(OrderItems,PurchaseItems).filter(and_(OrderItems.product_id==PurchaseItems.product_id,\
            OrderItems.order_id.in_(orders_ids))).all()

            return render_template('pharmmedsalesperiod.html',sales=sales,startdate_object=startdate_object,enddate_object=startdate_object)
        except:

            flash(f'StartDate or EndDate is empty','danger')
            return redirect(url_for('PharmMedicationSalesReport'))
    else:
        todaysales=db.session.query(OrderItems,PurchaseItems).filter(and_(OrderItems.product_id==PurchaseItems.product_id,\
            OrderItems.order_id.in_(orders_idz))).all()
        return render_template("pharmmedsalesreport.html",todaysales=todaysales,today=today)


# REORDER LEVEL REPORT
@app.route('/pharm_Reorder_level/',methods=['GET','POST'])
@login_required
def PharmReorderLevelReport():
    reorderproducts=PurchaseItems.query.filter(PurchaseItems.quantity == PurchaseItems.reorder_level).all()
    return render_template('pharmreorderlevel.html',reorderproducts=reorderproducts)


# ALL EXPIRED DRUGS REPORT
@app.route('/pharmacy/allexpired_drugs/',methods=['GET','POST'])
@login_required
def PharmallexpireddrugsReport():
    today = date.today()
    allexpiredproducts=PurchaseItems.query.filter(PurchaseItems.expiry_date == today ).all()
    return render_template('pharmallexpireddrugs.html',allexpiredproducts=allexpiredproducts)


# pharm profit loss report
@app.route('/Pharmacy/Profit_loss_report/',methods=['GET','POST'])
@login_required
def pharmProfitLossReport():
    today = date.today()

    TodaysExpenses=TrackExpense.query.filter(TrackExpense.inserted_by=="Pharmacist").all()
    expense_amount=sum([x.amount for x in TodaysExpenses])

    sales=OrderItems.query.filter(OrderItems.product_type=='Medication').all()
    sales_amount=sum([x.total_amount for x in sales])

    current_stock=PurchaseItems.query.all()
    stock_value=sum([(x.quantity*x.buying_price) for x in current_stock])

    profit =(sales_amount+stock_value)-(expense_amount)
    

    return render_template('pharmprofitloss.html',\
    expense_amount=expense_amount,sales_amount=sales_amount,\
    stock_value=stock_value,profit=profit,\
    startdate=today)

#Pharmacy Enter  Purchases
@app.route('/PharmaddPurchase/',methods=['GET'])
@login_required
def PharmAddPurchase():
    products=[p.product_name for p in Product.query.filter_by(product_type='Medication')]
    suppliers=[s.supplier_name for s in Supplier.query.all()]
    return render_template('pharmaddpurchase.html',products=products,suppliers=suppliers)
      
    
# allPurchase
@app.route('/PharmViewallPurchase/',methods=['GET','POST'])
@login_required
def PharmViewAllPurchase():
    Purchases=Purchase.query.all()
    return render_template('pharmallPurchases.html',Purchases=Purchases)

# ProductPuchaseDetails
@app.route('/PharmViewPurchaseDetails/<int:purchase_id>/',methods=['GET','POST'])
@login_required
def PharmViewPurchaseDetail(purchase_id):
    product_purchase=PurchaseItems.query.filter_by(purchase_id=purchase_id).all()
    purchase=Purchase.query.filter_by(id=purchase_id).one()
    return render_template('pharmviewpurchaseDetails.html',product_purchase=product_purchase,purchase_id=purchase_id,purchase=purchase)


# Pharm Delete Purchase order
@app.route('/PharmDeletePurchase/<int:purchase_id>/delete',methods=['POST'])
@login_required
def PharmDeletePurchases(purchase_id):
    PurchaseToDelete =Purchase.query.filter_by(id = purchase_id).one()

    supplierId=PurchaseToDelete.supplier_id
    balance=PurchaseToDelete.due_balance
    debt_pay=PurchaseToDelete.paydue_amount
        
    # Get the supplier for this purchase
    suppliert_obj=Supplier.query.filter_by(id=supplierId).one()
    suppliert_obj.openbalance -=int(balance)
    suppliert_obj.openbalance +=int(debt_pay)
   
        
    purchaseitems=PurchaseItems.query.filter_by(purchase_id=purchase_id).all()
    for item in purchaseitems:
        db.session.delete(item)
        db.session.commit()
            
    db.session.add(suppliert_obj)
    db.session.commit()

    db.session.delete(PurchaseToDelete)
    db.session.commit()

    flash(f'Purchase Order successfully Deleted!','danger')
    return redirect(url_for('PharmViewAllPurchase'))


#Pharm View all  Supplier
@app.route('/viewallsuppliers/')
@login_required
def PharmViewAllSuppliers():
    suppliers = Supplier.query.all()
    return render_template('pharmviewallSuppliers.html',suppliers=suppliers)
    

#Pharm Add Supplier
@app.route('/pharmaddSupplier/',methods=['GET','POST'])
@login_required
def PharmAddSupplier():
    if request.method == 'POST':
        newItem = Supplier(supplier_name=request.form['supplier_name'],supplier_phone=request.form['supplier_phone'])
        db.session.add(newItem)
        try:
            db.session.commit()
            flash(f' {newItem.supplier_name} Successfully Created!', 'success')
            return redirect(url_for('PharmViewAllSuppliers'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This Supplier already exists','danger')
            return redirect(url_for('PharmAddSupplier'))
    else:
        return render_template('pharmaddSupplier.html')


#Pharm Edit suppliers
@app.route('/supplier/<int:supplier_id>/pharm/edit/', methods = ['GET', 'POST'])
@login_required
def PharmEditSupplier(supplier_id):
    editedItem = Supplier.query.filter_by(id = supplier_id).one()
    if request.method == 'POST':
        if request.form['supplier_name']:
          editedItem.supplier_name = request.form['supplier_name']
        if request.form['supplier_phone']:
          editedItem.supplier_phone = request.form['supplier_phone']
    
        db.session.add(editedItem)
        db.session.commit() 
        flash(f' {editedItem.supplier_name} record has been updated!', 'success')
        return redirect(url_for('PharmViewAllSuppliers'))
    else:
        return render_template('PharmEditSupplier.html',supplier_id=supplier_id, s= editedItem)


# Pharm delete supplier
@app.route('/supplier/<int:supplier_id>/pharm/delete/', methods = ['POST'])
@login_required
def PharmdeleteSupplier(supplier_id):
        supplierToDelete = Supplier.query.filter_by(id = supplier_id).one()
        db.session.delete(supplierToDelete)
        db.session.commit()
        flash(f'Supplier successfully Deleted!','danger')
        return redirect(url_for('PharmViewAllSuppliers', supplier_id = supplier_id))


#Pharm view Products
@app.route('/view/products/',methods=['GET','POST'])
@login_required
def PharmViewallProducts():
    # filter by medication 
    products = Product.query.filter(Product.product_type=="Medication").all()
    return render_template('pharmviewallProducts.html', products = products) 


#Pharm Add Product 
@app.route('/PharmaddProduct/pharm/',methods=['GET','POST'])
@login_required
def PharmAddproduct():
    if request.method == 'POST':
        newItem = Product(product_name=request.form['product_name'],product_type=request.form['product_type'],sell_price=request.form['sell_price'])
        db.session.add(newItem)
        try:
            db.session.commit()
            flash(f' {newItem.product_name} Successfully Created!', 'success')
            return redirect(url_for('PharmViewallProducts'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This product already exists','danger')
            return redirect(url_for('PharmAddproduct'))
    else:
        return render_template('pharmaddProduct.html')


#Pharm Edit a  product
@app.route('/product/<int:product_id>/pharm/edit/', methods = ['GET', 'POST'])
@login_required
def PharmeditProduct(product_id):
    editedItem = Product.query.filter_by(id = product_id).one()
    if request.method == 'POST':
        if request.form['product_name']:
          editedItem.product_name = request.form['product_name']
        if request.form['product_type']:
          editedItem.product_type = request.form['product_type']
        if request.form['sell_price']:
          editedItem.sell_price = request.form['sell_price'] 
       

        db.session.add(editedItem)
        db.session.commit() 
        flash(f'Your product {editedItem.product_name}   has been updated!', 'success')
        return redirect(url_for('PharmViewallProducts'))
    else:
        return render_template('pharmeditProduct.html',product_id=product_id, d = editedItem)


#Pharm Delete a product
@app.route('/products/<int:product_id>/pharm/delete/', methods = ['POST'])
@login_required
def PharmdeleteProduct(product_id):
        productToDelete = Product.query.filter_by(id = product_id).one()
        db.session.delete(productToDelete)
        db.session.commit()
        flash(f'product successfully Delete!','danger')
        return redirect(url_for('PharmViewallProducts', product_id = product_id))


#Pharm Add Expences
@app.route('/pharmaddexpensecategory/',methods=['GET','POST'])
@login_required
def PharmAddExpenseCategory():
    username=current_user.role
    if request.method == 'POST':
        newItem = Expense(ExpenseCategory_name=request.form['ExpenseCategory_name'],inserted_by=username)
        db.session.add(newItem)
        try:
            db.session.commit()
            flash(f' {newItem.ExpenseCategory_name} Successfully Added!', 'success')
            return redirect(url_for('PharmViewAllExpenses'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This Expense Category already exists','danger')
            return redirect(url_for('PharmAddExpenseCategory'))
    else:
        return render_template('pharmaddexpensecategory.html')


#Pharm all Expences
@app.route('/pharmviewallexpenses/')
@login_required
def PharmViewAllExpenses():
    Expensecategory = Expense.query.filter(Expense.inserted_by=='Pharmacist').all()
    return render_template('pharmviewallExpenseCategory.html',Expensecategory=Expensecategory)


#pharm  edit expense
@app.route('/expense/<int:expense_id>/pharm/edit/', methods = ['POST'])
@login_required
def Pharmeditexpe(expense_id):
    username=current_user.role
    editedItem = Expense.query.filter_by(id =expense_id).one()
    editedItem.ExpenseCategory_name = request.form['expense']
    editedItem.inserted_by=username
    db.session.add(editedItem)
    db.session.commit() 
    flash(f'expense has been updated!', 'success')
    return redirect(url_for('PharmViewAllExpenses'))
    

#Pharm delete expense
@app.route('/expense/<int:expense_id>/pharm/delete/', methods = ['POST'])
@login_required
def PharmdeleteExpense(expense_id):
        expenseToDelete = Expense.query.filter_by(id = expense_id).one()
        db.session.delete(expenseToDelete)
        db.session.commit()
        flash(f'Expense successfully Deleted!','danger')
        return redirect(url_for('PharmViewAllExpenses', expense_id = expense_id))


#Pharm TrackExpense
@app.route('/pharmtrackexpenses/',methods=['GET','POST'])
@login_required
def PharmTrackExpenses():
    entries=[E.ExpenseCategory_name for E in Expense.query.all()]
    username=current_user.role
    if request.method == 'POST':
        date_str = request.form['dtpDate']
        date_object = datetime.strptime(date_str, "%Y-%m-%d").date()
        newItem = TrackExpense(created_on=date_object,expense_type=request.form['expense_type'],\
            payment_type=request.form['paytype'],amount=int(request.form['amount']),
            inserted_by=username)
        db.session.add(newItem)
        try:
            db.session.commit()
            flash(f' {newItem.expense_type} Successfully Added!', 'success')
            return redirect(url_for('PharmViewAllTrackedExpenses'))
        except IntegrityError:
            db.session.rollback()
            flash(f'This Expense Category already exists','danger')
            return redirect(url_for('PharmTrackExpenses'))
    else:
        return render_template('PharmTrackExpenses.html',entries=entries)

#Pharm all tracked Expences
@app.route('/pharmviewalltrackedexpenses/',methods=['GET','POST'])
@login_required
def PharmViewAllTrackedExpenses():
    trackedexpense=TrackExpense.query.filter(TrackExpense.inserted_by=='Pharmacist').all()
    return render_template("PharmexpenseStatement.html",trackedexpense=trackedexpense)

#Pharm delete a tracked expense
@app.route('/trackedexpense/<int:Expense_id>/pharm/delete/', methods = ['POST'])
@login_required
def PharmdeleteTrackedExpense(Expense_id):
    expenseToDelete = TrackExpense.query.filter_by(id = Expense_id).one()
    db.session.delete(expenseToDelete)
    db.session.commit()
    flash(f'Expense successfully Deleted!','danger')
    return redirect(url_for('PharmViewAllTrackedExpenses'))

# Pharmacy reports Profit margin per drug
@app.route('/pharm_dashboard/profit_productwise/',methods=['GET','POST'])
@login_required
def PharmrunProductDetailsReport():
    products=[p.product_name for p in Product.query.filter(Product.product_type=='Medication').all()]

    if request.method == 'POST':
        try:
            Medicine_name= request.form['product_name']
            
            startdate_object = request.form['from_date']
            startdate = datetime.strptime(startdate_object, "%Y-%m-%d").date()
            
            enddate_object = request.form['to_date']
            endDate = datetime.strptime(enddate_object, "%Y-%m-%d").date()
            
           
            # order between this dates TrackExpense.created_on.between(startdate,endDate)
            orders=Order.query.filter(Order.created_on.between(startdate,endDate)).all()
            order_ids=[x.id for x in orders]
            
            

            sales=db.session.query(OrderItems,PurchaseItems,func.sum(OrderItems.quantity).label('total_quantity'),\
                func.sum(PurchaseItems.total_amount).label('puchase_cost'),\
                func.sum(OrderItems.total_amount).label('sales_cost'))\
                .filter(and_(OrderItems.product_id==PurchaseItems.product_id,\
            OrderItems.order_id.in_(order_ids),OrderItems.product_name== Medicine_name)).all()
            func.sum(OrderItems.quantity).label('total_quantity') ,func.sum(OrderItems.total_amount)

                
            return render_template('PharmrunproductReport.html',Medicine_name=Medicine_name,sales=sales,products=products,startdate_object=startdate_object,enddate_object=startdate_object)
        except:


            flash(f'NO SALES FOUND FOR {Medicine_name} BETWEEN THE SELECTED DATES !', 'warning')
            return redirect(url_for('PharmrunProductDetailsReport'))
    else:

        return render_template("PharmrunproductReport.html",products=products)
    
# Pharmacy  profit loss reports for all products 
@app.route('/pharm_dashboard/all_profit_productwise/',methods=['GET','POST'])
@login_required
def PharmrunProfitforalldrugsReport():
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    
    def my_function(x):
        return list(dict.fromkeys(x))

    orders=Order.query.filter(Order.created_on >yesterday).all()
    order_ids=[x.id for x in orders]
      

    sales=OrderItems.query.filter(and_(OrderItems.order_id.in_(order_ids),\
    OrderItems.product_type=='Medication')).all()
            
    total_sales=[x.product_name for x in sales]
   
    unique=len(my_function(total_sales))
           
    sales_amount=sum([x.total_amount for x in sales])
    orderlines_id=[x.product_id for x in sales]
    Pucharses=PurchaseItems.query.filter(PurchaseItems.product_id.in_(orderlines_id)).all()
    purchase_cost=sum([(x.in_quantity-x.quantity)*x.buying_price for x in Pucharses])

    profit =sales_amount-purchase_cost
    
    if request.method == 'POST':
        try:
            
            startdate_object = request.form['from_date']
            startdate = datetime.strptime(startdate_object, "%Y-%m-%d").date()
            
            enddate_object = request.form['to_date']
            endDate = datetime.strptime(enddate_object, "%Y-%m-%d").date()
            
           
            # order between this dates TrackExpense.created_on.between(startdate,endDate)
            orders=Order.query.filter(Order.created_on.between(startdate,endDate)).all()
            order_ids=[x.id for x in orders]
            

            sales=OrderItems.query.filter(and_(OrderItems.order_id.in_(order_ids),\
                OrderItems.product_type=='Medication')).all()
            
            total_sales=[x.product_name for x in sales]

            unique=len(my_function(total_sales))
           
            sales_amount=sum([x.total_amount for x in sales])
            orderlines_id=[x.product_id for x in sales]
            Pucharses=PurchaseItems.query.filter(PurchaseItems.product_id.in_(orderlines_id)).all()
            purchase_cost=sum([(x.in_quantity-x.quantity)*x.buying_price for x in Pucharses])

            profit =sales_amount-purchase_cost
            
       
            return render_template('pharmrunprofitforalldrugs.html',\
            total_sales=unique,sales_amount=sales_amount,\
            purchase_cost=purchase_cost,profit=profit,\
            startdate=startdate,endDate=endDate)
        except:


            flash(f'NO SALES FOUND BETWEEN THE SELECTED DATES !', 'warning')
            return redirect(url_for('PharmrunProfitforalldrugsReport'))
    else:

        return render_template('pharmrunprofitforalldrugs.html',\
        total_sales=unique,sales_amount=sales_amount,\
        purchase_cost=purchase_cost,profit=profit,\
        startdate=today)
    

# ----------------------------------
# ADMINPHARMACY VIEWS
# view bill that have mediction and are active
@app.route('/dispenselist/',methods=['GET','POST'])
@login_required
def DispenseLIst():
    # get todays date and yesterdays date
    today = date.today()
    yesterday = today - timedelta(days = 1) 

    # get today orderlines with product type medication
    todays_orderlines_with_med=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.product_type.like('Medication%'))).order_by(desc(OrderItems.inserted_on)).all()
    
    # get all order ids with medications
    order_ids=[item.order_id for item in todays_orderlines_with_med]
    
    # Get all order that have medication but are still active(not dispensed)
    Patient_on_dispense_queue=db.session.query(Order).filter(and_( Order.inserted_on>yesterday,\
        Order.id.in_(order_ids),Order.status=="Active")).order_by(desc(Order.inserted_on)).all()
    
    # Check if their is patients on Pharmacy QUEUE
    exists=bool(Patient_on_dispense_queue)
    if exists == False:
        flash(f'NO PATIENT ON DISPENSE QUEUE','danger')
    
    return render_template('dispenselist.html',Patient_on_dispense_queue=Patient_on_dispense_queue)


@app.route('/ViewPrescriptionNote/<int:invoice_id>/VIEW',methods=['GET','POST'])
@login_required
def ViewPrescription(invoice_id):
    today = date.today()
    yesterday = today - timedelta(days = 1) 
    product_purchase=db.session.query(OrderItems).filter(and_( OrderItems.inserted_on >yesterday,\
        OrderItems.order_id==invoice_id,OrderItems.product_type.like('Medication%'))).order_by(asc(OrderItems.inserted_on)).all()
    order=Order.query.filter_by(id=invoice_id).one()
    patient_id=order.customer_id
    patient_name=order.customer_name
    patient_data=Customer.query.filter_by(name=patient_name).first()
    current_debt=patient_data.debt
    patients=[s.name for s in Customer.query.all()]
    products=[p.product_name for p in Product.query.all()]
    patientdetails=Customer.query.filter_by(id=patient_id).one()
    patvisits=Consultation.query.filter_by(customer_id=patient_id).order_by(desc(Consultation.inserted_on)).first()
    return render_template('viewprescription.html',patients=patients,product_purchase=product_purchase,invoice_id=invoice_id,order=order,patientdetails=patientdetails,\
        products=products,current_debt=current_debt,patvisits=patvisits,patient_id=patient_id)


# End-Patient Visit (deactivate)
@app.route('/dispensedrugs',methods=['POST'])
@login_required
def DispenseMedication():
    table= request.json
     
    # get values from json object
    for data in table:
            for i in data:
                if i=="patient_status":
                    patient_status=data[i]
                elif i=="order_id":
                    order_id=data[i]

    # get the order to update
    order_to_update=Order.query.filter_by(id=order_id).first()
    
    # change status to deactived
    if patient_status:
        order_to_update.status="Deactived"
    
    db.session.add(order_to_update)
    db.session.commit()

    return jsonify({'result':'sucesss'})



# -----------------------------------------------------------------------------------------------


# Invoices
@app.route('/patientBill/<int:patient_id>/new/', methods=['GET'])
@login_required
def newpatientBill(patient_id):
    patient =Customer.query.filter_by(id=patient_id).one()
    previusdebt=patient.debt
    products=[p.product_name for p in Product.query.all()]
    patients=[s.name for s in Customer.query.all()]
    patientids=[s.patient_id for s in Customer.query.all()]
   
    return render_template('addpatientInvoice.html', patient_id=patient_id,patient=patient,products=products,patients=patients,previusdebt=previusdebt,patientids=patientids)


@app.route('/addinvoices/',methods=['GET'])
@login_required
def AddInvoice():
    products=[p.product_name for p in Product.query.all()]
    patients=[s.name for s in Customer.query.all()]
    patientids=[s.patient_id for s in Customer.query.all()]
    return render_template('addInvoice.html',products=products,patients=patients,patientids=patientids)


# Get patient data API ENDPOINT
@app.route('/patientdata/<patient>')
def Patientdata(patient):
    data= Customer.query.filter_by(name=patient).all()
    # data= Customer.query.filter(or_(name=patient,patient_id=patient)).all()
    dataArray=[]
    for patient in data:
        patientobj={}
        patientobj['id']=patient.id
        patientobj['name']=patient.name
        patientobj['patient_Id']=patient.patient_id
        patientobj['debt']=patient.debt
        dataArray.append(patientobj)
    return jsonify({'Patient': dataArray})


# Get patient data API ENDPOINT by patient_id
@app.route('/patientdatabyId/<patientid>')
def PatientIddata(patientid):
    def insert_str(string, str_to_insert, index):
        return string[:index] + str_to_insert + string[index:]
    ids=insert_str(patientid,'/',4)
    data= Customer.query.filter_by(patient_id=ids).all()
    dataArray=[]
    for patient in data:
        patientobj={}
        patientobj['id']=patient.id
        patientobj['name']=patient.name
        patientobj['patient_Id']=patient.patient_id
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
    print(table)
    product_list=[]
    product_type=[]
    quantityarray=[]
    expiry_array=[]
    price=[]
    total_price=[]
        
    
    for data in table:
            for i in data:
                if i=="patient_name":
                    patient_name=data[i]
                elif i=="invoice_date":
                    invoice_date=data[i]
                elif i=="patient_Id":
                    patient_Id=data[i]
                elif i=="paytype":
                    paytype=data[i]
                elif i=="visittype":
                    visittype=data[i]
                elif i=="patient_status":
                    patient_status=data[i]
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
                elif i=="change":
                    change=data[i]
                elif i=="balance":
                    balance=data[i]
                elif i=="debt_pay":
                    debt_pay=data[i]
         
    patientToAdd=Customer.query.filter_by(patient_id=patient_Id).one()
    patientToAdd.debt +=int(balance)
    patientToAdd.debt -=int(debt_pay)

    invoiceDate = invoice_date
    invoiceDate_object = datetime.strptime(invoiceDate, "%Y-%m-%d").date()
    
     # calculate the amount paid for 
    receive_amount=int(paid_amount)- int(change)
    # deactvate if its a walk-in client
    # change status to deactived
    if patient_name=="WALK-IN":
        patient_status="Deactived"
    
    newinvoice=Order(customer_name=patient_name,patient_id=patient_Id,created_on=invoiceDate_object,payment_type=paytype,\
        status=patient_status,payment_amount=receive_amount,visit_type=visittype,total_amount=grand_total_price,previous=previous,net_total=nettotal,due_balance=balance,paydue_amount=debt_pay,customer=patientToAdd)
    
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
    allinvoices=Order.query.order_by(Order.inserted_on.desc()).all()
    return render_template('allInvoices.html',allinvoices=allinvoices)


# edit invoice
@app.route('/updateinvoice/<int:invoice_id>/edit',methods=['GET','POST'])
@login_required
def InvoiceUpdate(invoice_id):
    product_purchase=OrderItems.query.filter_by(order_id=invoice_id).all()
    order=Order.query.filter_by(id=invoice_id).one()
    patient=order.customer_id
    patient_name=order.customer_name
    patient_data=Customer.query.filter_by(name=patient_name).first()
    current_debt=patient_data.debt
    patients=[s.name for s in Customer.query.all()]
    products=[p.product_name for p in Product.query.all()]
    patientdetails=Customer.query.filter_by(id=patient).one()
    return render_template('editinvoice.html',patients=patients,product_purchase=product_purchase,invoice_id=invoice_id,order=order,patientdetails=patientdetails,\
        products=products,current_debt=current_debt)


@app.route('/processUpdatedInvoice',methods=['POST'])
@login_required
def UpdateInvoice():

    table= request.json
    print(table)
    product_list=[]
    product_type=[]
    quantityarray=[]
    expiry_array=[]
    price=[]
    total_price=[]

    for data in table:
            for i in data:
                if i=="patient_name":
                    patient_name=data[i]
                elif i=="invoice_date":
                    invoice_date=data[i]
                elif i=="patient_Id":
                    patient_Id=data[i]
                elif i=="paytype":
                    paytype=data[i]
                elif i=="order_id":
                    order_id=data[i]
                elif i=="patient_status":
                    patient_status=data[i]
                elif i=="visittype":
                    visit_type=data[i]
                elif i=="productname":
                    product_list.append(data[i])
                elif i=="producttype":
                    product_type.append(data[i])
                elif i=="expirydata":

                    if i:
                        expiry_array.append(data[i])
                    else:
                        expiry_array.append(None)
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
                elif i=="change":
                    change=data[i]
                elif i=="balance":
                    balance=data[i]
                elif i=="debt_pay":
                    debt_pay=data[i]
   

    substring = "2020"
    for n, i in enumerate(expiry_array):
        if i.find(substring) != -1:
            expiry_array[n]='None'
        elif expiry_array[n] =='':
            expiry_array[n]='sev'
      
           
    # update patient debt
    patientToAdd=Customer.query.filter_by(patient_id=patient_Id).one()
   
    patientToAdd.debt +=int(balance)
    patientToAdd.debt -=int(debt_pay)

    db.session.add(patientToAdd)
    db.session.commit()

    order_to_update=Order.query.filter_by(id=order_id).first()
    # orderitems_to_update=OrderItems.query.filter_by(order_id=order_id).all()
    
    invoiceDate = invoice_date
    invoiceDate_object = datetime.strptime(invoiceDate, "%Y-%m-%d").date()
    
    # calculate the amount paid for 
    receive_amount=int(paid_amount)- int(change)
 
    if patient_name:
        order_to_update.customer_name=patient_name
    if paytype:
        order_to_update.payment_type=paytype
    if visit_type:
        order_to_update.visit_type=visit_type
    if patient_status:
        order_to_update.status=patient_status
    if patient_Id:
        order_to_update.patient_id=patient_Id
    if invoice_date:
        order_to_update.created_on=invoiceDate_object
    if grand_total_price:
        order_to_update.total_amount=grand_total_price
    if nettotal:
        order_to_update.net_total=nettotal
    if previous:
        order_to_update.previous=previous
    if paid_amount:
        order_to_update.payment_amount=receive_amount
    if balance:
        order_to_update.due_balance=balance
    if debt_pay:
        order_to_update.paydue_amount=debt_pay
    
    for (prod,prodtyp,expry,qty,price,total) in zip(product_list,product_type,expiry_array,quantityarray,price,total_price):
        
        product_name=Product.query.filter_by(product_name=prod).one()
        
        if (expry !='None') and (expry !='sev'):

            purchaseitem=PurchaseItems.query.filter_by(id=expry).one()
            if purchaseitem:
                expry_date_object=purchaseitem.expiry_date
                expry_date= expry_date_object

    
            productToreduce=PurchaseItems.query.filter_by(id=expry).filter(PurchaseItems.quantity > 0).first()
        
       
            if (productToreduce is not None) and (expry_date is not None):

                productToreduce.quantity -=int(qty)
                
                itemlines=OrderItems(product_name=prod,expiry_date=expry_date,product_type=prodtyp,quantity=qty,buying_price=price,\
                total_amount=total,order=order_to_update,product=product_name)
                
                
                db.session.add(itemlines)
                db.session.add(productToreduce)

                db.session.commit()
                db.session.commit()
            
            
        elif expry=='sev':

            itemlines=OrderItems(product_name=prod,product_type=prodtyp,quantity=qty,buying_price=price,\
            total_amount=total,order=order_to_update,product=product_name)
            
            db.session.add(itemlines)
            db.session.add(patientToAdd)

            
            db.session.commit()
            db.session.commit()

    db.session.add(order_to_update)
    db.session.commit()

    return jsonify({'result':'sucesss'})
    

# Delete invoice
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

            print(item.expiry_date)

            stock_item=PurchaseItems.query.filter_by(product_name=prodname,expiry_date=prodexpiry).first()
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


# show invoice details
@app.route('/InvoiceDetails/<int:invoice_id>/',methods=['GET','POST'])
@login_required
def InvoiceDetail(invoice_id):
    product_purchase=OrderItems.query.filter_by(order_id=invoice_id).all()
    order=Order.query.filter_by(id=invoice_id).one()
    patient=order.customer_id
    patientdetails=Customer.query.filter_by(id=patient).one()
    return render_template('invoiceDetails.html',product_purchase=product_purchase,invoice_id=invoice_id,order=order,patientdetails=patientdetails)

# -----------------------------------------------------------------------------------------

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
        newItem = Product(product_name=request.form['product_name'],product_type=request.form['product_type'],sell_price=request.form['sell_price'])
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

# ---------------------------------------------------------------------------------------------
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


# ProductSALES
@app.route('/productsalesreport/<product>',methods=['GET'])
@login_required
def ProductSale(product):
    productsale=OrderItems.query.filter_by(product_name=product).all()
    return render_template('productsales.html',productsale=productsale,product=product)


# -----------------------------------------------------------------------------------------------
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
    print(table)
    product_list=[]
    date=[]
    quantityarray=[]
    reoderlevelarray=[]
    price=[]
    total_amount=[]   
    
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
                elif i=="reorder_level":
                    reoderlevelarray.append(data[i])
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
    print(product_list)
    print(date)
    print(quantityarray)
    print(reoderlevelarray)
    print(total_amount)
    for (prod,expiry,qty,reodlv,price,total) in zip(product_list,date,quantityarray,reoderlevelarray,price,total_amount):
        
        expiry_date = expiry
        expirydate_object = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        product_name=Product.query.filter_by(product_name=prod).one()
        seling_price=product_name.sell_price

        itemlines=PurchaseItems(product_name=prod,invoice_no=invoiceNo,reorder_level=reodlv,\
        expiry_date=expirydate_object,quantity=qty,in_quantity=qty,buying_price=price,\
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
    PurchaseToDelete =Purchase.query.filter_by(id = purchase_id).one()

    supplierId=PurchaseToDelete.supplier_id
    balance=PurchaseToDelete.due_balance
    debt_pay=PurchaseToDelete.paydue_amount
        
    # Get the supplier for this purchase
    suppliert_obj=Supplier.query.filter_by(id=supplierId).one()
    suppliert_obj.openbalance -=int(balance)
    suppliert_obj.openbalance +=int(debt_pay)
   
        
    purchaseitems=PurchaseItems.query.filter_by(purchase_id=purchase_id).all()
    for item in purchaseitems:
        db.session.delete(item)
        db.session.commit()
            
    db.session.add(suppliert_obj)
    db.session.commit()

    db.session.delete(PurchaseToDelete)
    db.session.commit()

    flash(f'Puchase  successfully Deleted!','danger')
    return redirect(url_for('AllPurchase'))


# -----------------------------------------------------------------------------------------------

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


# delete a tracked expense
@app.route('/trackedexpense/<int:Expense_id>/delete/', methods = ['POST'])
@login_required
def deleteTrackedExpense(Expense_id):
        expenseToDelete = TrackExpense.query.filter_by(id = Expense_id).one()
        db.session.delete(expenseToDelete)
        db.session.commit()
        flash(f'Expense successfully Deleted!','danger')
        return redirect(url_for('AllTrackedExpenses'))


# ----------------------------------------------------------------------------
# REPORTS
# All stock
@app.route('/stockreport/',methods=['GET','POST'])
@login_required
def StockReport():
    stock=PurchaseItems.query.all()
    return render_template("stockreport.html",stock=stock)


# Product purchase sales report
@app.route('/productsalepurchasereport/',methods=['GET','POST'])
@login_required
def ProductDetailsReport():
    return render_template("productReport.html")


# sales report (cummulative)
@app.route('/medicationsalesreport/',methods=['GET','POST'])
@login_required
def MedicationSalesReport():
    try:
        sales=OrderItems.query.with_entities(OrderItems.product_name,OrderItems.buying_price,\
        func.sum(OrderItems.quantity).label('total_quantity') ,func.sum(OrderItems.total_amount).\
        label('total_amount')).group_by(OrderItems.product_name).filter_by(product_type='Medication').all()
        return render_template("medsalesreport.html",sales=sales)
    except:
        flash(f'No sales found! click on stock report')
        return render_template("medsalesreport.html",sales=sales)


# stock report (cumulative)
@app.route('/medicationstockreport/',methods=['GET','POST'])
@login_required
def MedicationStockReport():
    stock=PurchaseItems.query.with_entities(PurchaseItems.product_name,func.sum(PurchaseItems.in_quantity).label('In_Quantity') ,func.sum(PurchaseItems.quantity).label('Current_Quantity') ,func.sum(PurchaseItems.total_amount).label('Cost_of_Goods')).group_by(PurchaseItems.product_name).all()
    return render_template("totalstock.html",stock=stock)


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
