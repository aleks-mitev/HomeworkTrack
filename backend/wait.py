import time
import os
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from __init__ import create_app, db

def wait_for_db():
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@database:5432/mydb')
    engine = create_engine(DATABASE_URL)
    print("Waiting for PostgreSQL to be available...")
    while True:
        try:
            with engine.connect() as connection:
                print("PostgreSQL is available!")
                break
        except OperationalError:
            print("PostgreSQL is unavailable - sleeping for 1 second")
            time.sleep(1)

if __name__ == "__main__":
    wait_for_db()
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
