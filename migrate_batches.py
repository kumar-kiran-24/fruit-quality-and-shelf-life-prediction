from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text, inspect

load_dotenv()
url = os.getenv('DATABASE_URL')
engine = create_engine(url)

insp = inspect(engine)
existing = [c['name'] for c in insp.get_columns('batches')]
print('Existing batches columns:', existing)

with engine.connect() as conn:
    if 'user_id' not in existing:
        print('Adding user_id column...')
        conn.execute(text('ALTER TABLE batches ADD COLUMN user_id VARCHAR(100)'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS ix_batches_user_id ON batches (user_id)'))
    else:
        print('user_id already exists')
    if 'number_of_images' not in existing:
        print('Adding number_of_images column...')
        conn.execute(text('ALTER TABLE batches ADD COLUMN number_of_images INTEGER'))
    else:
        print('number_of_images already exists')
    if 'total_apples_detected' not in existing:
        print('Adding total_apples_detected column...')
        conn.execute(text('ALTER TABLE batches ADD COLUMN total_apples_detected INTEGER'))
    else:
        print('total_apples_detected already exists')
    conn.commit()

insp2 = inspect(engine)
new_cols = [c['name'] for c in insp2.get_columns('batches')]
print('New batches columns:', new_cols)
