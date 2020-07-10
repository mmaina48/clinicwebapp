from app import *
from models import *




pid=db.session.query(db.func.max(Customer.id)).one()

def patientid(setids):
    import datetime
    id=['0' if v is None else v for v in setids]
    year=str(datetime.date.today().year) + '/100'
    patient_id=year+ str(id[0])
    return patient_id
opd=patientid(pid)

# add patients 
patient1 = Customer(name = "Michael Maina", patient_id = opd,age =25, gender = "Male",\
    patient_phone='078938473',National_id='3025698',nhif_no='25487236',debt=0)

db.session.add(patient1)
db.session.commit()

patient2 = Customer(name = "Jane Maina", patient_id = opd,age =22, gender = "FeMale",\
    patient_phone='071238473',National_id='3125588',nhif_no='2542566',debt=0)

db.session.add(patient2)
db.session.commit()

# add products and Service
# product1 = Product(product_name = "Amoxly 100mg pack", product_type = "Medication", sell_price = 100, reoder_level = "500")

# db.session.add(product1)
# db.session.commit()


# product2 = Product(product_name = "Brufen 100mg Tablet", product_type = "Medication", sell_price = 5, reoder_level = "500")

# db.session.add(product2)
# db.session.commit()

# product3 = Product(product_name = "Consultation", product_type = "Service", sell_price = 300, reoder_level = "0")

# db.session.add(product3)
# db.session.commit()
