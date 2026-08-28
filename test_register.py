from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session
from api.database.database import SessionLocal
from api.services.user_service import UserService

load_dotenv()
# Use existing DB session
db = SessionLocal()
service = UserService()
try:
    user = service.register_user(
        db=db,
        name='Migration Test',
        email='migration_test@example.com',
        password='test1234',
        address='MG Road',
        pincode='560001'
    )
    print('Created user:', user.user_id, user.email, user.city, user.country)
except Exception as e:
    print('Error:', e)
finally:
    db.close()
