from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import pdfplumber
from sqlalchemy import create_engine, inspect,text, Table, Column, Integer, String, Float, MetaData, DateTime,UniqueConstraint
import hashlib
import re
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import sys,os




app = Flask(__name__)
print(sys.argv)
print(sys.executable)


if len(sys.argv) != 4:
    print("Usage: app.py <DB_HOST> <DB_PASSWORD>")
    sys.exit(1)

DB_HOST = sys.argv[2]
DB_PASSWORD = sys.argv[3]
DB_USERNAME = 'admin'
DB_PORT = '3306'
DB_NAME = 'mydatabase'
print(DB_HOST)
# DB_PASSWORD = 'Pu$hkar121'
# DB_HOST = 'localhost'
DATABASE_URI = f"mysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(DATABASE_URI)
TABLE_NAME = 'grndata'
HASH_TABLE_NAME = 'file_hashes'

# Create a connection to the database
engine = create_engine(DATABASE_URI)

# Function to retrieve data from tables
def get_data_from_db(engine, table_name, start_date, end_date):
    query = f"SELECT * FROM {table_name} where date between '{start_date}' and '{end_date}' ORDER BY date desc, item"
    return pd.read_sql(query, engine)

def get_recdata_from_db(engine, table_name, start_date, end_date):
    query = f"SELECT Item, SUM(total) Total, SUM(quantity) Quantity, AVG(price) Price, Date FROM ( SELECT *, ROW_NUMBER() OVER(PARTITION BY date,item,storename,quantity,price,total ORDER BY sr_no ASC) AS ronum FROM {table_name} )X where ronum=1 AND date between '{start_date}' and '{end_date}' GROUP BY date, item ORDER BY date desc, item"
    return pd.read_sql(query, engine)


@app.route('/data', methods=['GET'])
def data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
        
    # Retrieve daily spent and daily received data
    df_spent = get_data_from_db(engine, 'spent_data',start_date, end_date)
    df_received = get_recdata_from_db(engine, 'grndata', start_date, end_date)

    # Normalize column names to have consistent names for merging
    df_received = df_received.rename(columns={
        'Item': 'item',
        'Quantity': 'qty',
        'Price': 'price',
        'Total': 'total',
        'Date': 'date'
    })
    # print(df_received)
    # Standardize date formats
    df_spent['date'] = pd.to_datetime(df_spent['date'], dayfirst=False).dt.strftime('%Y-%m-%d')
    df_received['date'] = pd.to_datetime(df_received['date'], dayfirst=True).dt.strftime('%Y-%m-%d')
    df_received['qty'] = round(df_received['qty'],2)
    df_received['total'] = round(df_received['total'],2)
    df_received['price'] = round(df_received['price'],2)
    
    
    # Trim whitespace from item names
    df_spent['item'] = df_spent['item'].str.strip()
    df_received['item'] = df_received['item'].str.strip()
    
    # Separate 'OTHER COST' from df_spent
    df_other_costs = df_spent[df_spent['item'] == 'OTHER COST']
    df_spent = df_spent[df_spent['item'] != 'OTHER COST']
    
    # Merge the data on the date and item columns
    df_merged = pd.merge(df_spent, df_received, on=['date', 'item'], suffixes=('_spent', '_received'))

    # Calculate daily profit/loss for each item
    df_merged['daily_profit_loss'] = round(df_merged['total_received'] - df_merged['total_spent'],2)

    # Group by date to get the total spent, received, and daily profit/loss
    daily_summary = df_merged.groupby('date').agg({
        'total_spent': 'sum',
        'total_received': 'sum',
        'daily_profit_loss': 'sum'
    }).reset_index()
    
    # Include 'OTHER COST' in the daily summary
    if not df_other_costs.empty:
        other_costs_summary = df_other_costs.groupby('date').agg({'total': 'sum'}).reset_index()
        other_costs_summary = other_costs_summary.rename(columns={'total': 'other_costs'})
        daily_summary = pd.merge(daily_summary, other_costs_summary, on='date', how='left')
        daily_summary['other_costs'] = daily_summary['other_costs'].fillna(0)
    else:
        daily_summary['other_costs'] = 0

    # Adjust daily profit/loss to include 'OTHER COST'
    daily_summary['daily_profit_loss'] = round(daily_summary['daily_profit_loss'] - daily_summary['other_costs'], 2)

    #Rounding it off to 2 digits
    daily_summary['total_spent'] = round(daily_summary['total_spent'],2)
    daily_summary['total_received'] = round(daily_summary['total_received'],2)
    daily_summary['daily_profit_loss'] = round(daily_summary['daily_profit_loss'],2)
    daily_summary['other_costs'] = round(daily_summary['other_costs'], 2)


    daily_summary['items'] = daily_summary['date'].apply(
        lambda d: df_merged[df_merged['date'] == d].sort_values(by='item').to_dict(orient='records')
    )
    daily_summary = daily_summary.sort_values(by='date', ascending=False)
    response_data = daily_summary.to_dict(orient='records')
    return jsonify(response_data)




# Configuration for SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class SpentData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    item = db.Column(db.String(100), nullable=False)
    qty = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)

# Create the database
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("main.html")

@app.route("/submit", methods=["POST"])
def submit():
    date = request.form["date"]
    item = request.form["item"]
    qty = request.form["qty"]
    price = request.form["price"]
    total = request.form["total"]

    # Check if data with the same date and item already exists
    existing_data = SpentData.query.filter_by(date=date, item=item).first()
    if existing_data:
        # Update existing row with the same date and item
        existing_data.qty = qty
        existing_data.price = price
        existing_data.total = total
    else:
        # If data with the same date and item does not exist, create a new row
        new_data = SpentData(date=date, item=item, qty=qty, price=price, total=total)
        db.session.add(new_data)
    
    db.session.commit()
    return "Data submitted successfully!"

@app.route("/get_data")
def get_data():
    req_date = request.args.get("reqdate")
    
    data = SpentData.query.filter_by(date=req_date).order_by(SpentData.date.desc(), SpentData.item.asc()).all()
    if not data:
        return jsonify([])  # Return empty list if no data found for the given date

    result = []
    for row in data:
        row_data = {
            "date": row.date,
            "item": row.item,
            "qty": row.qty,
            "price": row.price,
            "total": row.total
        }
        result.append(row_data)

    return jsonify(result)

##File data backend


# Define table schema
metadata = MetaData()

data_table = Table(
    TABLE_NAME, metadata,
    Column('Sr_No', Integer, primary_key=True, autoincrement=True),
    Column('HSN_CODE', String(255)),
    Column('ITEM_CODE', Integer),
    Column('Item', String(255)),
    Column('Quantity', String(255)),
    Column('UOM', String(10)),
    Column('Price', Float),
    Column('Total', Float),
    Column('Date', DateTime),
    Column('StoreName', String(255))
)

hash_table = Table(
    HASH_TABLE_NAME, metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('file_hash', String(64), nullable=False),
    Column('store_name', String(255)),
    Column('file_date', DateTime),
    UniqueConstraint('file_hash', 'store_name', 'file_date', name='unique_file')
)

# Create tables if they don't exist
metadata.create_all(engine)

# Function to check if a table exists in the database
def table_exists(engine, table_name):
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def compute_file_hash(file_path):
    hash_func = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def is_duplicate_file(file_hash, store_name, file_date):
    with engine.connect() as connection:
        query = text(f"""
        SELECT COUNT(*) 
        FROM {HASH_TABLE_NAME} 
        WHERE file_hash = :file_hash 
        AND store_name = :store_name 
        AND file_date = :file_date
        """)
        params = {'file_hash': file_hash, 'store_name': store_name, 'file_date': file_date}
        result = connection.execute(query, params).scalar()
        return result > 0


def store_file_hash(file_hash, store_name, file_date):
    with engine.connect() as connection:
        metadata.create_all(engine)
        query = text(f"""
        INSERT INTO {HASH_TABLE_NAME} (file_hash, store_name, file_date) 
        VALUES ('{file_hash}', '{store_name}', '{file_date}')
        """)        
        try:
            connection.execute(query)
            connection.commit()  
            print("Data inserted into hash table successfully!")
        except SQLAlchemyError as e:
            print(f"Error inserting data into hash table: {e}")
        
    
# Function to store data to MySQL database
def store_to_db(df, engine, table):
    try:
        if not table_exists(engine, table.name):
            metadata.create_all(engine)
            df.to_sql(table.name, con=engine, if_exists='append', index=False)
            print(f"Table '{table.name}' created and data has been stored successfully!")
        else:
            df.to_sql(table.name, con=engine, if_exists='append', index=False)
            print(f"Data has been appended to the existing table '{table.name}' successfully!")
        
    except SQLAlchemyError as e:
        print(f"Error storing data to the database: {e}")

# Function to process a single PDF file
def process_pdf(input_file):
    file_size = os.path.getsize(input_file)
    file_hash = compute_file_hash(input_file)

    # Extract tables from PDF using pdfplumber
    with pdfplumber.open(input_file) as pdf:
        tables = []
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                tables.extend(table)

    # Convert tables to Pandas DataFrame
    df = pd.DataFrame(tables)

    # To get place name
    for index, row in df.iterrows():
        if 'Site Name' in row.values:
            # Get the index of 'Site Name' column
            site_name_index = row.index[row == 'Site Name'][0]

            # Get the place name from the next row in the same column
            place_name = df.iloc[index + 1, site_name_index].strip().replace(' ','_')

            break  # Exit loop after finding 'Site Name'
        
    #Extract Date
    date_str = re.search(r'(\d{2}\.\d{2}\.\d{4})', df.iloc[0, 2]).group(1)
    file_date = datetime.strptime(date_str, "%d.%m.%Y")
    df['Date'] = file_date

    if is_duplicate_file(file_hash, place_name, file_date):
        print(f"Duplicate file detected for {place_name} on {file_date}. Skipping processing.")
        return
    
    df=df[8:]


    # Find the index of the first occurrence of 'Sr.No'
    first_occurrence_index = df[0].tolist().index('Sr.No')

    # Filter out rows where the first column has 'Sr.No', except for the first occurrence
    df_filtered = pd.concat([df.iloc[first_occurrence_index:first_occurrence_index+1], df[df[0] != 'Sr.No']])

    # Reset the index of the DataFrame
    df_filtered.reset_index(drop=True, inplace=True)

    df=df_filtered

    # Find the index of the first occurrence of 'Grand Total of Qty'
    first_grand_total_index = df[df[0] == 'Grand Total of Qty'].index.tolist()

    if first_grand_total_index:
        # If 'Grand Total of Qty' exists in the DataFrame
        first_grand_total_index = first_grand_total_index[0]
        # Slice the DataFrame to include rows only up to the first occurrence of 'Grand Total of Qty'
        df_filtered = df.iloc[:first_grand_total_index ]
    else:
        # If 'Grand Total of Qty' does not exist in the DataFrame, keep the original DataFrame
        df_filtered = df.copy()

    df=df_filtered

    # df['Date']  = pd.to_datetime(df[3].str.extract(r'(\d{2}.\d{2}.\d{4})', expand=False),format="%d.%m.%Y")

    df['StoreName'] = place_name

    # Extract the date from the 'Date' column
    date_from_column = df.at[1, 'Date']
    datetime_obj=datetime.strptime(str(date_from_column), '%Y-%m-%d %H:%M:%S') 
    date_from_column = datetime_obj.strftime('%Y_%m_%d')

    # Remove date data from item name
    df[3] = df[3].str.replace(r'\n\d{2}.\d{2}.\d{4}\n\w{4}$', '', regex=True)

    # Remove columns 0, 6, 8 and 9
    df = df.drop(columns=[0, 6, 8, 9])

    #Remove the 1st row
    df = df.iloc[1:]
    
    # Add proper column names to the DataFrame
    df.columns = ['HSN_CODE', 'ITEM_CODE', 'Item',  'Quantity', 'UOM','Price','Total', 'Date', 'StoreName']

    # Function to clean the data
    def clean_data(value):
        return value.split('\n')[0]
    
    # Data Cleaning
    df['Total'] = df['Total'].str.replace(',','')
    df['Item'] = df['Item'].str.strip("._/\n")
    df['HSN_CODE'] = df['HSN_CODE'].str.replace('\n','')
    df['ITEM_CODE'] = df['ITEM_CODE'].apply(clean_data)


    # Change data types of the DataFrame columns
    df = df.astype({
        'Quantity': 'float',
        'Price': 'float',
        'Total': 'float'
    })
    df['Quantity'] = round(df['Quantity'], 2)
    df['Price'] = round(df['Price'], 2)
    df['Total'] = round(df['Total'], 2)

    store_to_db(df, engine, data_table)
    store_file_hash(file_hash, place_name, file_date)

@app.route('/FILEDATA', methods=['GET', 'POST'])
def file_data():
    if request.method == 'POST':
        # Check if files are present in the request
        if 'files' not in request.files:
            return jsonify(error="No file part in the request"), 400

        files = request.files.getlist('files')
        response_data = []

        # Process each file
        for file in files:
            if file.filename == '':
                response_data.append({"filename": file.filename, "success": False, "error": "No selected file"})
                continue
            if file:
                # Save the file temporarily
                temp_file_path = os.path.join('temp', file.filename)
                file.save(temp_file_path)

                try:
                    # Process the PDF file
                    process_pdf(temp_file_path)
                    response_data.append({"filename": file.filename, "success": True})
                except Exception as e:
                    response_data.append({"filename": file.filename, "success": False, "error": str(e)})

                # Remove the temporary file
                os.remove(temp_file_path)

        return jsonify(response_data)
    
    elif request.method=='GET':
        req_date = request.args.get("reqdate")
        with engine.connect() as connection:
            query = text(f"""
            SELECT * 
            FROM {TABLE_NAME} 
            WHERE Date = '{req_date}' 
            ORDER BY Date desc, item 
            """)
            grndata = connection.execute(query).fetchall()
                
        if not grndata:
            return jsonify([])  # Return empty list if no data found for the given date
        data = []
        for row in grndata:
            row_data = {
                "SR_NO": row.Sr_No,
                "ITEM": row.Item,
                "QUANTITY": row.Quantity,
                "PRICE": row.Price,
                "TOTAL": row.Total,
                "STORENAME":row.StoreName
            }
            data.append(row_data)

    return jsonify(data)


@app.route('/updateRow', methods=['POST'])
def update_row():
    data = request.json
    sr_no = data.get('SR_NO')
    updated_data = {
        "Quantity": data.get('QUANTITY'),
        "Price": data.get('PRICE'),
        "Total": data.get('TOTAL'),
    }

    with engine.connect() as connection:
        query = text(f"""
        UPDATE {TABLE_NAME}
        SET Quantity = :Quantity,
            Price = :Price,
            Total = :Total
        WHERE Sr_No = :SR_NO
        """)
        connection.execute(query, {
                    "Quantity": updated_data["Quantity"],
                    "Price": updated_data["Price"],
                    "Total": updated_data["Total"],
                    "SR_NO": sr_no
                })
        connection.commit() 

    return jsonify(success=True)

@app.route('/deleteRow', methods=['POST'])
def delete_row():
    data = request.json
    sr_no = data.get('SR_NO')

    with engine.connect() as connection:
        query = text(f"DELETE FROM {TABLE_NAME} WHERE Sr_No = :SR_NO")
        connection.execute(query, {'SR_NO': sr_no})
        connection.commit() 
    return jsonify(success=True)

if __name__ == "__main__":
    if not os.path.exists('temp'):
        os.makedirs('temp')
        
    app.run(debug=True)
