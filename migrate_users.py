from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text, inspect

load_dotenv()
url = os.getenv('DATABASE_URL')
engine = create_engine(url)

insp = inspect(engine)
existing = [c['name'] for c in insp.get_columns('users')]
print('Existing columns:', existing)

with engine.connect() as conn:
    if 'country' not in existing:
        print('Adding country column...')
        conn.execute(text('ALTER TABLE users ADD COLUMN country VARCHAR(100)'))
    else:
        print('country already exists')
    if 'phone_number' not in existing:
        print('Adding phone_number column...')
        conn.execute(text('ALTER TABLE users ADD COLUMN phone_number VARCHAR(50)'))
    else:
        print('phone_number already exists')
    conn.commit()

insp2 = inspect(engine)
new_cols = [c['name'] for c in insp2.get_columns('users')]
print('New columns:', new_cols)
