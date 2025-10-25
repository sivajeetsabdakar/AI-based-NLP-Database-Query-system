import csv
from faker import Faker
from random import choice, randint
import datetime
import sys

# Try to import FPDF
try:
    from fpdf import FPDF
except ImportError:
    print("\n--- ERROR ---")
    print("To create a PDF, you must install the 'fpdf2' library.")
    print("Please run this command in your terminal:")
    print("\npip install fpdf2\n")
    print("Then run this script again.")
    sys.exit()

# Initialize Faker to generate random data
fake = Faker()

# Define possible departments and their job titles
departments = ['Engineering', 'Marketing', 'Sales', 'Human Resources', 'Finance', 'Customer Support', 'IT']
job_titles_by_dept = {
    'Engineering': ['Software Engineer', 'Senior Software Engineer', 'Data Scientist', 'QA Tester', 'DevOps Engineer'],
    'Marketing': ['Marketing Manager', 'SEO Specialist', 'Content Creator', 'Social Media Manager'],
    'Sales': ['Sales Representative', 'Account Executive', 'Sales Manager'],
    'Human Resources': ['HR Specialist', 'Recruiter', 'HR Manager'],
    'Finance': ['Accountant', 'Financial Analyst', 'Controller'],
    'Customer Support': ['Customer Support Rep', 'Support Specialist', 'Support Manager'],
    'IT': ['IT Support', 'Network Administrator', 'Systems Analyst']
}

# --- Settings ---
NUM_EMPLOYEES = 200
FILE_NAME = 'random_employees.pdf' # Changed to .pdf
# --- End Settings ---

# Generate data
employee_data = []
header = ['EmployeeID', 'FirstName', 'LastName', 'Email', 'Department', 'JobTitle', 'StartDate', 'Salary']
employee_data.append(header)

start_id = 1001

for i in range(NUM_EMPLOYEES):
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}.{last_name.lower()}@fakecorp.com"
    
    department = choice(departments)
    job_title = choice(job_titles_by_dept[department])
    
    # Generate a random start date within the last 10 years
    start_date = fake.date_between(start_date='-10y', end_date='today')
    
    # Generate a salary (e.g., between 45,000 and 150,000)
    salary = randint(45000, 150000)
    
    employee_id = start_id + i
    
    employee_data.append([
        employee_id, 
        first_name, 
        last_name, 
        email, 
        department, 
        job_title, 
        start_date, 
        salary
    ])

# --- Write to PDF file ---
try:
    pdf = FPDF(orientation='L', unit='mm', format='A4') # Landscape mode
    pdf.add_page()
    pdf.set_font("Arial", size=8)
    
    # Define column widths (total 277mm for A4 Landscape)
    col_widths = {
        'EmployeeID': 15,
        'FirstName': 30,
        'LastName': 30,
        'Email': 65,
        'Department': 35,
        'JobTitle': 47,
        'StartDate': 25,
        'Salary': 25
    }
    
    line_height = pdf.font_size * 2

    # Add Header
    pdf.set_font(style='B') # Bold
    for col_name in header:
        pdf.cell(col_widths[col_name], line_height, col_name, border=1, ln=0, align='C')
    pdf.ln(line_height) # New line
    pdf.set_font(style='') # Regular

    # Add Data Rows
    for row in employee_data[1:]: # Skip header row in data
        # Check if page break is needed
        if pdf.get_y() > 190: # 190mm is near bottom of A4-L (210mm)
            pdf.add_page()
            # Re-add header on new page
            pdf.set_font(style='B')
            for col_name in header:
                pdf.cell(col_widths[col_name], line_height, col_name, border=1, ln=0, align='C')
            pdf.ln(line_height)
            pdf.set_font(style='')

        # Add data cells
        for i, item in enumerate(row):
            col_name = header[i]
            pdf.cell(col_widths[col_name], line_height, str(item), border=1, ln=0, align='L')
        pdf.ln(line_height) # New line

    # Save the PDF
    pdf.output(FILE_NAME)
    
    print(f"Successfully generated '{FILE_NAME}' with {NUM_EMPLOYEES} random employee records.")

except Exception as e:
    print(f"An error occurred while generating the PDF: {e}")