import pandas as pd
from app import app, db, Books

# Correct file path with raw string
file_path = r"C:\Projects\LIB_SYS_REV\books.csv"

def import_csv_to_db(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)

    with app.app_context():
        # Iterate over the DataFrame and insert each row into the Books table
        for index, row in df.iterrows():
            try:
                csv_entry = Books(Book_Name=row['Book_Name']) 
                print(csv_entry) 
                db.session.add(csv_entry)
            except Exception as e:
                print(f"Error adding entry {index}: {e}")
        db.session.commit()

# Call the function with the path to your CSV file
import_csv_to_db(file_path)
