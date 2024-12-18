import sqlite3
import base64
import pandas as pd

DB_PATH = 'inspections.db'

def setup_database():
    """
    Set up the SQLite database and create the table if it doesn't exist.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY,
                work_order_no TEXT,
                file_name TEXT,
                type_description TEXT,
                location TEXT,
                part_no TEXT,
                certificate_no TEXT,
                serial_no TEXT,
                inspection_date TEXT,
                expire_date TEXT,
                fit_for_use TEXT,
                fit_rejected TEXT,
                remarks TEXT,
                customer TEXT,
                pdf_blob BLOB,
                UNIQUE(work_order_no, certificate_no)
            )
        ''')
        conn.commit()

def insert_data(cursor, data, pdf_blob):
    """
    Helper function to insert data into the database.
    """
    cursor.execute('''
        INSERT INTO inspections (
            work_order_no, file_name, type_description, location, part_no, certificate_no,
            serial_no, inspection_date, expire_date, fit_for_use, fit_rejected,
            remarks, customer, pdf_blob
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('Work Order No'),
        data.get('File Name'),
        data.get('Type/Description'),
        data.get('Location'),
        data.get('Part No'),
        data.get('Certificate No'),
        data.get('Serial No.'),
        data.get('Inspection Date'),
        data.get('Expire Date'),
        data.get('Fit for use'),
        data.get('Fit/Rejected'),
        data.get('Remarks'),
        data.get('Customer'),
        pdf_blob
    ))


def insert_data_to_db(data, pdf_path):
    """
    Insert data and the PDF file as a BLOB into the database.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        with open(pdf_path, 'rb') as file:
            pdf_blob = file.read()
            # Check if record already exists
            cursor.execute("SELECT COUNT(*) FROM inspections WHERE work_order_no = ? AND certificate_no = ?", 
                            (data['Work Order No'], data['Certificate No']))
            if cursor.fetchone()[0] > 0:
                print("Record already exists, skipping insert.")
                return
            insert_data(cursor, data, pdf_blob)
            conn.commit()

def display_data_from_db(db_path='inspections.db'):
    """
    Query and return all data from the SQLite database as a pandas DataFrame.
    """
    with sqlite3.connect(db_path) as conn:
        query = "SELECT * FROM inspections"
        df = pd.read_sql_query(query, conn)
    return df
