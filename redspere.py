import os
from flask import Flask
from datetime import datetime, timedelta
import pandas as pd
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')

# Access email configuration from environment variables
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')


# Load the spreadsheet data
SPREADSHEET_PATH = 'loans_data.xlsx'

def load_spreadsheet():
    """Load the spreadsheet into a pandas DataFrame."""
    return pd.read_excel(SPREADSHEET_PATH)

def search_loans(option):
    """Search for loans in the spreadsheet based on the user's option."""
    data = load_spreadsheet()
    options_map = {
        '1': 'Salary Based Loans',
        '2': 'Pensions Loan',
        '3': 'Pay Day Loan',
        '4': 'School Loan',
        '5': 'Order Financing',
    }

    selected_keyword = options_map.get(option, None)
    if not selected_keyword:
        return "Invalid option. Please choose a valid option from 1 to 5."

    key_words = " ".join(selected_keyword.split()[:1])
    matching_rows = data[data['Product Name'].str.contains(key_words, case=False, na=False)]

    if matching_rows.empty:
        return f"No results found for items matching '{key_words}'."

    response = f"Results for items matching '{key_words}':\n\n"
    for idx, (_, row) in enumerate(matching_rows.iterrows(), start=1):
        response += f"{idx}. {row['Product Name']}\n"
        response += "\n".join([f"{col}: {row[col]}" for col in data.columns])
        response += "\n\n---\n"

    response += "\nTo apply, reply with the number of the loan you want to choose."
    return response.strip()


def apply_for_loan(option, loan_number):
    """Handle the process of applying for a loan based on the selected loan number."""
    data = load_spreadsheet()

    # Map options to corresponding keywords in the spreadsheet
    options_map = {
        '1': 'Salary Based Loans',
        '2': 'Pensions Loan',
        '3': 'Pay Day Loan',
        '4': 'School Loan',
        '5': 'Order Financing',
    }

    selected_keyword = options_map.get(option, None)
    if not selected_keyword:
        return "Invalid option. Please choose a valid option from 1 to 5."

    # Extract the first word from the selected keyword
    key_words = " ".join(selected_keyword.split()[:1])

    # Filter rows where 'Product Name' contains the key words
    matching_rows = data[data['Product Name'].str.contains(key_words, case=False, na=False)]

    if matching_rows.empty or loan_number < 1 or loan_number > len(matching_rows):
        return "Invalid loan number. Please choose a valid loan from the list."

    selected_loan = matching_rows.iloc[loan_number - 1]

    # Format the application response
    response = "You have chosen to apply for the following loan:\n\n"
    response += "\n".join([f"{col}: {selected_loan[col]}" for col in data.columns])
    response += "\n\nOur team will contact you shortly to proceed with the application process!"

    return response.strip()

import uuid
from datetime import datetime, timedelta

# Function to generate a unique customId
def generate_custom_id():
    return f"LOAN-{uuid.uuid4().hex[:8].upper()}"  # Generates LOAN-XXXXXXXX format

# Populating the loan application data dynamically
def prepare_loan_application(user_data, camunda_data):
    return {
        "customerEmail": user_data['email'],
        "loanTenure": camunda_data['tenure'],  # Loan tenure selected by the user
        "disbursementOption": "VISA_CARD",  # Static value as per example
        "loanAmount": camunda_data['amount'],  # Loan amount entered by the user
        "idNumber": user_data['id_number'],  # ID number from user data
        "loanPaymentDate": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S"),  # 30 days from now
        "approvalStatus": "PENDING",  # Default approval status
        "typeOfLoan": camunda_data['loan_product'],  # Selected loan product name
        "customId": generate_custom_id(),  # Autogenerated custom ID
        "loanProduct": {
            "id": camunda_data.get('loan_product_id', 1)  # Loan product ID if available, default to 1
        },
        "customer": {
            "id": user_data.get('customer_id', 1)  # Customer ID if available, default to 1
        }
    }