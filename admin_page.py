import datetime
import sys
import warnings
import streamlit as st
import os
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
import sqlite3
from sqlite_module import setup_database, insert_data_to_db, display_data_from_db  # Ensure these are implemented
import re
import base64
import shutil

def log_re_function(func, pattern, *args, **kwargs):
    """
    Logs the usage of an `re` function and executes it.
    
    Parameters:
        func (callable): The `re` function to use (e.g., re.search, re.match).
        pattern (str): The regex pattern to apply.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the `re` function call.
    """
    print(f"Using '{func.__name__}' with pattern: {pattern}")
    return func(pattern, *args, **kwargs)



# def display():
#     st.header("Admin Page")
#     st.write("This is the admin-specific page.")

def extract_table_data(page):
    # Attempt to extract data from the third table
    tables = page.extract_tables()
    
    if len(tables) >= 3:
        # Extract first column from the third table
        third_table = tables[2]
        columns = list(zip(*third_table))
        first_column = [cell.strip() for cell in columns[0] if cell and cell.strip()]
        combined_text = ' '.join(first_column)
        
        # Extract data between "EQUIPMENT I.D.NO" and "Technique Particle"
        pattern = r'I\.D\.NO(.*?)Technique'
        match = re.search(pattern, combined_text, re.DOTALL)
        if match:
            extracted_data = match.group(1).strip()
            # Remove newline characters
            cleaned_data = extracted_data.replace('\n', ' ')
            return cleaned_data

    # If the first approach didn't return data, try the fourth table
    if len(tables) >= 4:
        # Extract fourth table
        fourth_table = tables[3]
        columns = list(zip(*fourth_table))
        first_column = [cell.strip() for cell in columns[0] if cell and cell.strip()]
        combined_text = ' '.join(first_column)
        
        # Extract data between "I.D NO." and "Technique"
        pattern = r'I\.D\s?NO\. *([^.]*)Technique'
        match = re.search(pattern, combined_text, re.DOTALL)
        if match:
            extracted_data = match.group(1).strip()
            # Remove newline characters
            cleaned_data = extracted_data.replace('\n', ' ')
            return cleaned_data
    
    # If the above approaches didn't return data, try the first table
    if len(tables) >= 1:
        # Extract first table
        first_table = tables[0]
        columns = list(zip(*first_table))
        first_column = [cell.strip() for cell in columns[0] if cell and cell.strip()]
        combined_text = ' '.join(first_column)
        
        # Extract data between "I.D NO." and "Technique"
        pattern = r'I\.D NO\.(.*?)Technique'
        match = re.search(pattern, combined_text, re.DOTALL)
        if match:
            extracted_data = match.group(1).strip()
            # Remove newline characters
            cleaned_data = extracted_data.replace('\n', ' ')
            return cleaned_data
    
    return 'No table data extracted.'
        

# Regular expressions for extracting data   
def extract_magnetic_particle_data(text):
    return {
        'Work Order No': re.search(r'W\.O\. No\.\s*(\d+)', text).group(1) if re.search(r'W\.O\. No\.\s*(\d+)', text) else 'N/A',
        'File Name': extract_last_line_above_customer(text),
        'Type/Description': re.search(r'Material / Item Type and Description\s*([^\n]*)', text).group(1).strip() if re.search(r'Material / Item Type and Description\s*([^\n]*)', text) else 'N/A',
        'Location': re.search(r"Location\.?\s*(.*?)\s*Cert\. No", text).group(1).strip() if re.search(r"Location\.?\s*(.*?)\s*Cert\. No", text) else 'N/A',        'Certificate No': re.search(r'Cert\. No\.\s*(\S+)', text).group(1) if re.search(r'Cert\. No\.\s*(\S+)', text) else 'N/A',
        'Certificate No': re.search(r"Cert\. No[:.]?\s*(.+)", text).group(1) if re.search(r"Cert\. No[:.]?\s*(.+)", text) else 'N/A',
        'Part No' : re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', text).group(1).strip() if re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', text) else 'N/A',
        'Serial No.': re.search(r'(?:Material \/ Item serial No\.\s*)?(\S.*?)(?:\s+(?:Part No|Project|PROJECT)|\s*$)', text).group(1) if re.search(r'(?:Material \/ Item serial No\.\s*)?(\S.*?)(?:\s+(?:Part No|Project|PROJECT)|\s*$)', text) else 'N/A',
        'Inspection Date': re.search(r'Date of Inspection\.\s*([\d\-]+)', text).group(1).strip() if re.search(r'Date of Inspection\.\s*([\d\-]+)', text) else 'N/A',
        'Expire Date': re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", text).group(1).strip() if re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text) else 'N/A',
        'Remarks': re.search(r'Area of inspection:\s*(.*?)\s*Results', text).group(1).strip() if re.search(r'Area of inspection:\s*(.*?)\s*Results', text) else 'N/A',
        'Customer': re.search(r"(?:Customer|CUSTOMER\s*:)\s*(.*?)\s*Date of Work", text).group(1).strip() if re.search(r"(?:Customer|CUSTOMER\s*:)\s*(.*?)\s*Date of Work", text) else 'N/A',
    }
    pass

def extract_ultrasonic_wall_thickness_data(text):
    return {
        "Work Order No": re.search(r"Work Order No:\s*(\d+)", text).group(1).strip() if re.search(r"Work Order No:\s*(\d+)", text) else None,
        "File Name": re.search(r'^(.*\bSHEET\b.*)$', text, re.MULTILINE).group(1).strip() if re.search(r'^(.*\bSHEET\b.*)$', text, re.MULTILINE) else None,  
        "Type/Description": re.search(r"(?:Material /Item type & Description:|Matrial /Item type & Description:)\s*(.*)", text).group(1).strip() if re.search(r"(?:Material /Item type & Description:|Matrial /Item type & Description:)\s*(.*)", text) else None,
        "Location": re.search(r"Location:\s*(.*?)\s*(?:Sub Location:)", text).group(1).strip() if re.search(r"Location:\s*(.*?)\s*(?:Sub Location:)", text) else None,
        "Certificate No": re.search(r"(?:Cert\s*\.?\s*No)\s*(.*)", text).group(1).strip() if re.search(r"(?:Cert\s*\.?\s*No)\s*(.*)", text) else None,
        "Serial No.": re.search(r"(?:Matrial /Item Type serial No:|Material /Item Type serial No:)\s*(.*?)\s*(?:Item Location:)", text).group(1) if re.search(r"(?:Matrial /Item Type serial No:|Material /Item Type serial No:)\s*(.*?)\s*(?:Item Location:)", text) else None,
        "Part No": re.search (r"Item Location:\s*(.*)", text).group(1).strip() if re.search(r"Item Location:\s*(.*)",text) else None,
        "Inspection Date": find_inspection_date(text),
        "Expire Date": extract_due_date(text),
        "Remarks": re.search(r"Recommendation\s*/\s*Comments\s*:\s*(.*)", text).group(1).strip() if re.search(r"Recommendation\s*/\s*Comments\s*:\s*(.*)", text) else None,
        "Customer": re.search(r"Customer\s*:\s*(.*?)(?=\s+Rig\s*/\s*Well\s+No)", text).group(1).strip() if re.search(r"Customer\s*:\s*(.*?)(?=\s+Rig\s*/\s*Well\s+No)", text) else None,
        "Fit For Use": re.search(r'Fit For Use:(.+?)(?=Work Order No)', text).group(1).strip() if re.search(r'Fit For Use:(.+?)(?=Work Order No)', text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:(.+?)(?=Fit For Use)', text).group(1).strip() if re.search(r'Fit/Rejected:(.+?)(?=Fit For Use)', text) else None,

    }
    pass


def extract_lifting_gear_data(text,page):
    return {
        "Work Order No": re.search(r'W\.?O\.?NO:\s*(\S+)', text).group(1) if re.search(r'W\.?O\.?NO:\s*(\S+)', text) else None,
        "File Name": re.search(r'(.*?)\s*/ LIFTING APPLIANCES', text).group(1).strip() if re.search(r'(.*?)\s*/ LIFTING APPLIANCES', text) else None,
        "Type/Description": re.search(r'(.*?)\s*Customer:', text).group(1).strip() if re.search(r'(.*?)\s*Customer:', text) else None,
        "Location": re.search(r"Location:\s*(.*?)\s*(?=Rig & Well Number|W.O.NO:)", text).group(1) if re.search(r"Location:\s*(.*?)\s*(?=Rig & Well Number|W.O.NO:)", text) else None,
        "Certificate No": re.search(r'Certificate No\s*:\s*(.*)', text).group(1) if re.search(r'Certificate No\s*:\s*(.*)', text) else None,
        "Serial No." : extract_table_data(page=page),
        # "Serial No.": re.search(r'"(.*?)"', text).group(1).strip() if re.search(r'"(.*?)"', text) else None,
        "Part No": re.search (r"Location Of Item:?\s*(.*)", text).group(1).strip() if re.search(r"Location Of Item:?\s*(.*)",text) else None,
        "Inspection Date": re.search(r"(\d{2}-\d{2}-\d{4})\s+Due Date:", text).group(1) if re.search(r"(\d{2}-\d{2}-\d{4})\s+Due Date:", text) else None,
        "Expire Date": re.search(r'Due Date:\s*(\S+)', text).group(1).strip() if re.search(r'Due Date:\s*(\S+)', text) else None,
        "Fit For Use": re.search(r'FIT FOR USE:\s*(\S+)', text).group(1).strip() if re.search(r'FIT FOR USE:\s*(\S+)', text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:\s*(\S+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*(\S+)', text) else None,
        "Remarks": re.search(r'Results\s*:(.*?)\n(?:Recommendation|Comments|\n\n)', text).group(1).strip() if re.search(r'Results\s*:(.*?)\n(?:Recommendation|Comments|\n\n)', text) else None,
        "Customer": re.search(r'Customer:\s*(.*?)\s*Location Of Item', text).group(1) if re.search(r'Customer:\s*(.*?)\s*Location Of Item', text) else None
    }    

def extract_drill_collar_data(text):
    return {
        
        'Work Order No': re.search(r"WORK ORDER NUM\s+(\d+)", text).group(1) if re.search(r"WORK ORDER NUM\s+(\d+)", text) else 'N/A',
        'File Name': re.search(r'(.*?)\s*(?:Document Number|Customer)', text).group(1).strip() if re.search(r'(.*?)\s*(?:Document Number|Customer)', text) else 'N/A',
        'Type/Description': re.search(r"TYPE OF INSPECTION (.+?) TYPE", text).group(1).strip() if re.search(r"TYPE OF INSPECTION (.+?) TYPE", text) else 'N/A',
        'Location': re.search(r"LOCATION\s+([\w\s\/-]+)\s*(?=CONSUMABLE TRACEABILITY|$)", text).group(1).strip() if re.search(r"LOCATION\s+([\w\s\/-]+)\s*(?=CONSUMABLE TRACEABILITY|$)", text) else 'N/A',        'Certificate No': re.search(r'Cert\. No\.\s*(\S+)', text).group(1) if re.search(r'Cert\. No\.\s*(\S+)', text) else 'N/A',
        "Certificate No": re.search(r"Certificate No:\s*(.*)", text).group(1) if re.search(r"Certificate No:\s*(.*)", text) else None,
        'Serial No.' : dc_extracted_serial(text),
        # 'Serial No.': re.search(r'(.*?)\s*Part No\.', text).group(1) if re.search(r'(.*?)\s*Part No\.', text) else 'N/A',
        'Inspection Date': re.search(r'DATE OF WORK\s*(.*?)\s*(?:ISNPECTION|INSPECTION NUMBER)', text).group(1).strip() if re.search(r'DATE OF WORK\s*(.*?)\s*(?:ISNPECTION|INSPECTION NUMBER)', text) else 'N/A',
        'Expire Date': re.search(r"\b\d{2}-\d{2}-\d{4}\b", text).group(0).strip() if re.search(r"\b\d{2}-\d{2}-\d{4}\b", text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text) else 'N/A',
        'Remarks': re.search(r'Area of inspection:\s*(.*?)\s*Results', text).group(1).strip() if re.search(r'Area of inspection:\s*(.*?)\s*Results', text) else 'N/A',
        'Customer': re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', text) else 'N/A'
    }    

def extract_load_test_data(text):

    return {
        'Work Order No': re.search(r'W\.?O\.?NO:\s*(\S+)', text).group(1) if re.search(r'W\.?O\.?NO:\s*(\S+)', text) else 'N/A',
        'File Name': re.search(r'(?:CERTIFICATE OF LOAD/ PROOF|CERTIFICATE OF LOAD TEST/ PROOF)(.*)& THOROUGH EXAMINATION(.*)', text).group(1).strip() if re.search(r'(?:CERTIFICATE OF LOAD/ PROOF|CERTIFICATE OF LOAD TEST/ PROOF)(.*)& THOROUGH EXAMINATION(.*)', text) else 'N/A',
        'Type/Description': re.search(r"(.*?)(?=\s*Customer)", text).group(1).strip() if re.search(r"(.*?)(?=\s*Customer)", text) else 'N/A',
        'Location': re.search(r"Location:\s*(.*?)\s*Rig & Well", text).group(1).strip() if re.search(r"Location:\s*(.*?)\s*Rig & Well", text) else 'N/A',
        'Certificate No' : re.search(r"Certificate No\s*:\s*(\S+)", text).group(1).strip() if re.search(r"Certificate No\s*:\s*(\S+)", text) else 'N/A',
        "Part No": re.search (r"Item Location:\s*(.*)", text).group(1).strip() if re.search(r"Item Location:\s*(.*)",text) else None,
        'Serial No.':(
            re.search(r"\bSPK\S*\b", text).group(0).strip() 
            if re.search(r"\bSPK\S*\b", text) 
            else (
                re.search(r'ITEMS \(Ton\) \(Ton\) \(mm\) \(mm\)\s*\n(\S+)', text).group(1).strip() 
                if re.search(r'ITEMS \(Ton\) \(Ton\) \(mm\) \(mm\)\s*\n(\S+)', text) 
                else None
           )
         ),
        'Inspection Date': re.search(r"(?:Inspection Date|Inspected Date)\s*(?:\:)?\s*(\d{2}-\d{2}-\d{4})\s*Due Date", text).group(1).strip() if re.search(r"(?:Inspection Date|Inspected Date)\s*(?:\:)?\s*(\d{2}-\d{2}-\d{4})\s*Due Date", text) else 'N/A',
        'Expire Date': re.search(r"Due Date:\s*(.*)", text).group(1).strip() if re.search(r"Due Date:\s*(.*)", text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text) else 'N/A',
        'Remarks': re.search(r"REMARKS\s*:\s*(.*)", text).group(1).strip() if re.search(r"REMARKS\s*:\s*(.*)", text) else 'N/A',
        "Customer": re.search(r'Customer:\s*(.*?)\s*Location', text).group(1).strip() if re.search(r'Customer:\s*(.*?)\s*Location', text) else None

    }

def extract_wall_thickness_MPI(text):
    
    return {
        "Work Order No": re.search(r'W\.?O\.?NO:\s*(\S+)', text).group(1) if re.search(r'W\.?O\.?NO:\s*(\S+)', text) else None,
        "File Name": re.search(r'Certificate No:\s*.*\n(.*)', text).group(1).strip() if re.search(r'Certificate No:\s*.*\n(.*)', text) else None,
        "Type/Description": re.search(r"(.*?)(?=\s*Customer)", text).group(1).strip() if re.search(r"(.*?)(?=\s*Customer)", text) else None,
        "Location": re.search(r'Location\s*:\s*(.*?)\s*W\.O\.NO:', text).group(1) if re.search(r'Location\s*:\s*(.*?)\s*W\.O\.NO:', text) else None,
        "Certificate No": re.search(r"Certificate No\s*:\s*(\S+)", text).group(1) if re.search(r"Certificate No\s*:\s*(\S+)", text) else None,
        "Serial No.": re.search(r"\bSPK\S*\b", text).group(0).strip() if re.search(r"\bSPK\S*\b", text) else None,
        # "Part no": re.search(r"(?<=INSPECTED ITEMS THICKNESS \(INCHES\)\n)((?:.+(?:\n| )?)+?)(?=EQUIPMENT TRACEABILITY)", text).group(0).strip() if re.search(r"(?<=INSPECTED ITEMS THICKNESS \(INCHES\)\n)((?:.+(?:\n| )?)+?)(?=EQUIPMENT TRACEABILITY)", text) else None,
        "Part No" : re.search(r"PROJECT\s+(.*)", text).group(1).strip() if re.search(r"PROJECT\s+(.*)", text) else None,
        "Inspection Date": re.search(r"(?:Inspection Date|Inspected Date)\s*(?:\:)?\s*(\d{2}-\d{2}-\d{4})\s*Due Date", text).group(1) if re.search(r"(?:Inspection Date|Inspected Date)\s*(?:\:)?\s*(\d{2}-\d{2}-\d{4})\s*Due Date", text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', text).group(1) if re.search(r'Due Date\s*(.*)', text) else None,
        "Fit for use": re.search(r'FIT FOR USE:\s*(\S+)', text).group(1) if re.search(r'FIT FOR USE:\s*(\S+)', text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:\s*(\S+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*(\S+)', text) else None,
        "Remarks": re.search(r"RESULT\s+(.*)", text).group(1).strip() if re.search(r"RESULT\s+(.*)", text) else None,
        "Customer": re.search(r"Customer\s*:\s*(.*?)\s*(?:DEPART|PROJECT)", text).group(1).strip() if re.search(r"Customer\s*:\s*(.*?)\s*(?:DEPART|PROJECT)", text) else None
    }

def heavy_weight_drill_pipe_data(text):
    
    return {
        "Work Order No": re.search(r'WORK ORDER NUM\s+(\d+)', text).group(1) if re.search(r'WORK ORDER NUM\s+(\d+)', text) else None,
        "File Name": re.search(r'(.*?)\s+Document Number', text).group(1).strip() if re.search(r'(.*?)\s+Document Number', text) else None,
        "Type/Description": re.search(r"(.*?)(?=\s*Customer)", text).group(1).strip() if re.search(r"(.*?)(?=\s*Customer)", text) else None,
        "Location": re.search(r'LOCATION\s+(.*?)\s+CONSUMABLE', text).group(1) if re.search(r'LOCATION\s+(.*?)\s+CONSUMABLE', text) else None,
        # "Certificate No": re.search(r"(.*?)\sCONTROLLED", text).group(1) if re.search(r"(.*?)\sCONTROLLED", text) else None,
        "Certificate No": hw_extracted_serial(text)[2:6],
        "Serial No.": hw_extracted_serial(text),
        # "Part no": re.search(r"(?<=INSPECTED ITEMS THICKNESS \(INCHES\)\n)((?:.+(?:\n| )?)+?)(?=EQUIPMENT TRACEABILITY)", text).group(0).strip() if re.search(r"(?<=INSPECTED ITEMS THICKNESS \(INCHES\)\n)((?:.+(?:\n| )?)+?)(?=EQUIPMENT TRACEABILITY)", text) else None,
        # "Part No" : re.search(r"PROJECT\s+(.*)", text).group(1).strip() if re.search(r"PROJECT\s+(.*)", text) else None,
        "Inspection Date": re.search(r'DATE OF WORK\s+(.*?)\s+JOB NUMBER', text).group(1) if re.search(r'DATE OF WORK\s+(.*?)\s+JOB NUMBER', text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', text).group(1) if re.search(r'Due Date\s*(.*)', text) else None,
        "Fit for use": re.search(r'FIT FOR USE:\s*(\S+)', text).group(1) if re.search(r'FIT FOR USE:\s*(\S+)', text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:\s*(\S+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*(\S+)', text) else None,
        "Remarks": re.search(r"RESULT\s+(.*)", text).group(1).strip() if re.search(r"RESULT\s+(.*)", text) else None,
        "Customer": re.search(r'CUSTOMER\s(.*?)\sLOCATION', text).group(1).strip() if re.search(r'CUSTOMER\s(.*?)\sLOCATION', text) else None
    }

def extract_drill_pipe_data(text):
    
    return {
        "Work Order No": re.search(r'WORK ORDER NUM\s+(\d+)', text).group(1) if re.search(r'WORK ORDER NUM\s+(\d+)', text) else None,
        "File Name": re.search(r'(.*?)\s*(?:Document Number|Customer)', text).group(1).strip() if re.search(r'(.*?)\s*(?:Document Number|Customer)', text) else None,
        "Type/Description": re.search(r"TYPE OF INSPECTION:\s+(.*?)\s+MAGNETIC", text).group(1).strip() if re.search(r"TYPE OF INSPECTION:\s+(.*?)\s+MAGNETIC", text) else None,
        "Location": re.search(r"LOCATION\s+(.*?)\s+GRADE", text).group(1) if re.search(r"LOCATION\s+(.*?)\s+GRADE", text) else None,
        # "Certificate No": re.search(r"(.*?)\sCONTROLLED", text).group(1) if re.search(r"(.*?)\sCONTROLLED", text) else None,
        "Certificate No": extract_drill_pipe_combined_remarks(text)[1:9] if extract_drill_pipe_combined_remarks(text) else None,
        "Serial No.": extract_drill_pipe_combined_remarks(text),
        # "Part no": re.search(r"(?<=INSPECTED ITEMS THICKNESS \(INCHES\)\n)((?:.+(?:\n| )?)+?)(?=EQUIPMENT TRACEABILITY)", text).group(0).strip() if re.search(r"(?<=INSPECTED ITEMS THICKNESS \(INCHES\)\n)((?:.+(?:\n| )?)+?)(?=EQUIPMENT TRACEABILITY)", text) else None,
        # "Part No" : re.search(r"PROJECT\s+(.*)", text).group(1).strip() if re.search(r"PROJECT\s+(.*)", text) else None,
        "Inspection Date": re.search(r'DATE OF WORK\s*(.*?)\s*(?:ISNPECTION|INSPECTION NUMBER)', text).group(1) if re.search(r'DATE OF WORK\s*(.*?)\s*(?:ISNPECTION|INSPECTION NUMBER)', text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', text).group(1) if re.search(r'Due Date\s*(.*)', text) else None,
        "Fit for use": re.search(r'FIT FOR USE:\s*(\S+)', text).group(1) if re.search(r'FIT FOR USE:\s*(\S+)', text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:\s*(\S+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*(\S+)', text) else None,
        "Remarks": re.search(r"RESULT\s+(.*)", text).group(1).strip() if re.search(r"RESULT\s+(.*)", text) else None,
        "Customer": re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', text) else None
    }

def extract_drilling_tool_pxp(text):

    file_name_match = re.search(r"DRILLINGTOOLS\s*\(PxP\)\s*INSPECTION\s*REPORT", text)
    if file_name_match:
        # Extract the match and apply formatting
        extracted_data = file_name_match.group(0)
        # Add spaces between 'DRILLING' and 'TOOLS', as well as around '(PxP)'
        formatted_file_name = extracted_data.replace("DRILLINGTOOLS", "DRILLING TOOLS").replace("(PxP)", "( P x P )")
    else:
        formatted_file_name = None
    
    return {
        "Work Order No": re.search(r'WORK ORDER NUM\s+(\d+)', text).group(1) if re.search(r'WORK ORDER NUM\s+(\d+)', text) else None,
        "File Name": formatted_file_name,
        # "File Name": re.search(r"(?<=Tel #).*?([A-Za-z\s\(\)]+DRILLINGTOOLS.*)", text).group(1).strip() if re.search(r"(?<=Tel #).*?([A-Za-z\s\(\)]+DRILLINGTOOLS.*)", text) else None,
        "Type/Description": re.search(r"(?<=T INY SP PE E O CF T ION)(.*?)(?=INSPECTION TYPE OF CONNECTION)", text).group(1).strip() if re.search(r"(?<=T INY SP PE E O CF T ION)(.*?)(?=INSPECTION TYPE OF CONNECTION)", text) else None,
        "Location": re.search(r"(?<=LOCATION/USED AT)(.*?)(?=INSPECTION TECHNIQUES)", text).group(1) if re.search(r"(?<=LOCATION/USED AT)(.*?)(?=INSPECTION TECHNIQUES)", text) else None,
        # "Certificate No": re.search(r"(?<=STANDARD USED)(.*?)(?=MAGNETIC)", text).group(1) if re.search(r"(?<=STANDARD USED)(.*?)(?=MAGNETIC)", text) else None,
        "Certificate No": drilling_tool_extracted_serial(text)[1:9],
        "Serial No.": drilling_tool_extracted_serial(text),  
        # "Part no": re.search(r"(?<=INSPECTED ITEMS THICKNESS \(INCHES\)\n)((?:.+(?:\n| )?)+?)(?=EQUIPMENT TRACEABILITY)", text).group(0).strip() if re.search(r"(?<=INSPECTED ITEMS THICKNESS \(INCHES\)\n)((?:.+(?:\n| )?)+?)(?=EQUIPMENT TRACEABILITY)", text) else None,
        "Inspection Date": re.search(r"(?<=DATE OF WORK)(.*?)(?=JOB NUMBER)", text).group(1) if re.search(r"(?<=DATE OF WORK)(.*?)(?=JOB NUMBER)", text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', text).group(1) if re.search(r'Due Date\s*(.*)', text) else None,
        "Fit for use": re.search(r'FIT FOR USE:\s*(\S+)', text).group(1) if re.search(r'FIT FOR USE:\s*(\S+)', text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:\s*(\S+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*(\S+)', text) else None,
        "Remarks": re.search(r"RESULT\s+(.*)", text).group(1).strip() if re.search(r"RESULT\s+(.*)", text) else None,
        "Customer": re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', text) else None
    }




def extract_drill_pipe_bxb(pdf_text):
    return {
        'Work Order No': re.search(r'WORK ORDER NUM\s+(.*)', pdf_text).group(1) if re.search(r'WORK ORDER NUM\s+(.*)', pdf_text) else 'N/A',
        'File Name': extract_bxb_file_name(pdf_text),
        'Type/Description': re.search(r"Type Of Inspection\s+(.*?)\s+TYPE OF CONNECTION", pdf_text).group(1).strip() if re.search(r"Type Of Inspection\s+(.*?)\s+TYPE OF CONNECTION", pdf_text) else 'N/A',
        'Location': re.search(r"Location\s+(.*?)\s+CONSUMABLE", pdf_text).group(1).strip() if re.search(r"Location\s+(.*?)\s+CONSUMABLE", pdf_text) else 'N/A',        
        # 'Certificate No': re.search(r'Cert\. No\.\s*(\S+)', pdf_text).group(1) if re.search(r'Cert\. No\.\s*(\S+)', pdf_text) else 'N/A',
        'Certificate No': re.search(r'Certificate No:\s*([A-Za-z0-9\(\)\-]+)', pdf_text).group(1) if re.search(r'Certificate No:\s*([A-Za-z0-9\(\)\-]+)', pdf_text) else 'N/A',
        'Part No' : re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', pdf_text).group(1).strip() if re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', pdf_text) else 'N/A',
        'Serial No.': extract_pxb_serial_no(pdf_text),
        'Inspection Date': re.search(r'DATE OF WORK\s+(.*?)\s+JOB NUMBER', pdf_text).group(1).strip() if re.search(r'DATE OF WORK\s+(.*?)\s+JOB NUMBER', pdf_text) else 'N/A',
        'Expire Date': re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", pdf_text).group(1).strip() if re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", pdf_text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', pdf_text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', pdf_text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text) else 'N/A',
        'Remarks': re.search(r'Area of inspection:\s*(.*?)\s*Results', pdf_text).group(1).strip() if re.search(r'Area of inspection:\s*(.*?)\s*Results', pdf_text) else 'N/A',
        'Customer': re.search(r'Customer\s+(.*?)\s+Location', pdf_text).group(1).strip() if re.search(r'Customer\s+(.*?)\s+Location', pdf_text) else 'N/A',
    }


def extract_bxb_file_name(text):
    # Search for the pattern before "Customer"
    file_name_match = re.search(r"(.*?)\s*(?:Customer)", text)
    
    if file_name_match:
        # Extract the match
        extracted_data = file_name_match.group(1)
        # Add spaces between 'DRILLING' and 'TOOLS', as well as around '(PXB)'
        formatted_file_name = extracted_data.replace("(BXB)", "( B x B )")
    else:
        # If no match is found, return None
        formatted_file_name = None
    
    # Return the formatted file name or None
    return formatted_file_name

def extract_bxb_serial_no(text):
    extracted_info = []

    # Split the PDF text by lines
    for text in text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second word if available
                second_word = words[1] if len(words) > 1 else ''
            
                # Extract the last two words
                last_two_words = " ".join(words[-2:]) if len(words) >= 2 else ''

                # Append formatted string
                extracted_info.append(f"[{second_word}, ({last_two_words})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    # Use the extracted serial information as needed
    return ', '.join(extracted_info) if extracted_info else None









def extract_miscellaneous_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[1] if len(words) > 1 else ''
                third_word = " ".join(words[2:5]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word}, {third_word}({last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        "Work Order No": re.search(r"W\.O NO\.\s*(.*)", pdf_text).group(1) if re.search(r"W\.O NO\.\s*(.*)", pdf_text) else None,
        "File Name": re.search(r"(.*?)\s*CUSTOMER:", pdf_text).group(1).strip() if re.search(r"(.*?)\s*CUSTOMER:", pdf_text) else None,
        "Type/Description": re.search(r"TYPE OF INSPECTION\s*(.*?)\s*STANDARD:", pdf_text).group(1).strip() if re.search(r"TYPE OF INSPECTION\s*(.*?)\s*STANDARD:", pdf_text) else None,
        "Location": re.search(r"LOCATION:\s*(.*?)\s*DATE OF WORK:", pdf_text).group(1) if re.search(r"LOCATION:\s*(.*?)\s*DATE OF WORK:", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": serial_info[1:12],

        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE OF WORK:\s*(.*)", pdf_text).group(1) if re.search(r"DATE OF WORK:\s*(.*)", pdf_text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', pdf_text).group(1) if re.search(r'Due Date\s*(.*)', pdf_text) else None,
        "Fit for use": re.search(r'FIT FOR USE:\s*(\S+)', pdf_text).group(1) if re.search(r'FIT FOR USE:\s*(\S+)', pdf_text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:\s*(\S+)', pdf_text).group(1).strip() if re.search(r'Fit/Rejected:\s*(\S+)', pdf_text) else None,
        "Remarks": re.search(r"RESULT\s+(.*)", pdf_text).group(1).strip() if re.search(r"RESULT\s+(.*)", pdf_text) else None,
        "Customer": re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text) else None
    }



def extract_miscellaneous_tools_inspection_ds_1(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[1] if len(words) > 1 else ''
                third_word = " ".join(words[2:5]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word}, {third_word}({last_word})]")
                

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    # Use the extracted serial information as needed
    serial_info_2 = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        "Work Order No": re.search(r"W\.O\.No\.\s*(.*)", pdf_text).group(1) if re.search(r"W\.O\.No\.\s*(.*)", pdf_text) else None,
        "File Name": re.search(r"(.*?)\s*CUSTOMER:", pdf_text).group(1).strip() if re.search(r"(.*?)\s*CUSTOMER:", pdf_text) else None,
        "Type/Description": re.search(r"TYPE OF INSPECTION\s*(.*?)\s*STANDARD:", pdf_text).group(1).strip() if re.search(r"TYPE OF INSPECTION\s*(.*?)\s*STANDARD:", pdf_text) else None,
        "Location": re.search(r"LOCATION:\s*(.*?)\s*DS-1/DC", pdf_text).group(1) if re.search(r"LOCATION:\s*(.*?)\s*DS-1/DC", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": serial_info_2[1:12],
        "Serial No.": serial_info_2,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE OF WORK:\s*(.*)", pdf_text).group(1) if re.search(r"DATE OF WORK:\s*(.*)", pdf_text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', pdf_text).group(1) if re.search(r'Due Date\s*(.*)', pdf_text) else None,
        "Fit for use": re.search(r'FIT FOR USE:\s*(\S+)', pdf_text).group(1) if re.search(r'FIT FOR USE:\s*(\S+)', pdf_text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:\s*(\S+)', pdf_text).group(1).strip() if re.search(r'Fit/Rejected:\s*(\S+)', pdf_text) else None,
        "Remarks": re.search(r"RESULT\s+(.*)", pdf_text).group(1).strip() if re.search(r"RESULT\s+(.*)", pdf_text) else None,
        "Customer": re.search(r"CUSTOMER:\s*(.*?)\s*LOCATION:", pdf_text).group(1).strip() if re.search(r"CUSTOMER:\s*(.*?)\s*LOCATION:", pdf_text) else None
    }


def extract_pressure_witness_test(text):


    pressure_pattern = r"PRESSURE\n\(P\.S\.I\)\n([^\s]+)"
    time_pattern = r"TIME\n[^\n]*\n([^\s]*)"

    # Logic for "Serial No." based on PRESSURE or TIME patterns
    serial_no = re.search(pressure_pattern, text).group(1) if re.search(pressure_pattern, text) else \
                re.search(time_pattern, text).group(1) if re.search(time_pattern, text) else None
    
    return {
        "Work Order No": re.search(r"W\.O(?:\.?\s*No\.|\.NO:)\s*(\d+)", text).group(1) if re.search(r"W\.O(?:\.?\s*No\.|\.NO:)\s*(\d+)", text) else None,
        "File Name": re.search(r"Certificate No:.*?\n(.*)", text).group(1).strip() if re.search(r"Certificate No:.*?\n(.*)", text) else None,
        "Type/Description": re.search(r"(.*?)\s*Customer", text).group(1).strip() if re.search(r"(.*?)\s*Customer", text) else None,
        "Location": re.search(r"Location(?:\:|\s)(.*?)(?=\s*W\.O\.?\s*(?:No\.|NO:))", text).group(1) if re.search(r"Location(?:\:|\s)(.*?)(?=\s*W\.O\.?\s*(?:No\.|NO:))", text) else None,
        "Certificate No": re.search(r"Certificate No:\s*(.*)", text).group(1) if re.search(r"Certificate No:\s*(.*)", text) else None,
       "Serial No." : serial_no,
        # "Serial No.": re.search(r"TIME\n[^\n]*\n([^\s]*)", text).group(1) if re.search(r"TIME\n[^\n]*\n([^\s]*)", text) else None,
        "Inspection Date": re.search(r"Inspection Date:? ([\d\-]+)(?=\s*Due Date:?|\s*Due Date)", text).group(1) if re.search(r"Inspection Date:? ([\d\-]+)(?=\s*Due Date:?|\s*Due Date)", text) else None,
        "Expire Date": re.search(r"Due Date:? ([\d\/\-]+)", text).group(1) if re.search(r"Due Date:? ([\d\/\-]+)", text) else None,
        "Fit for use": re.search(r'FIT FOR USE:\s*(\S+)', text).group(1) if re.search(r'FIT FOR USE:\s*(\S+)', text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:\s*(\S+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*(\S+)', text) else None,
        "Remarks": re.search(r'PRESSURE\s*\(P\.S\.I\)\s*(.*)', text).group(1).strip() if re.search(r'PRESSURE\s*\(P\.S\.I\)\s*(.*)', text) else None,
        "Customer": re.search(r"Customer(?:\:|\s)(.*?)(?=\s*Project)", text).group(1).strip() if re.search(r"Customer(?:\:|\s)(.*?)(?=\s*Project)", text) else None
    }


def extract_boroscopic_data(pdf_text):
    return {
        'Work Order No': re.search(r'W\.O\. No\.\s*(\d+)', pdf_text).group(1) if re.search(r'W\.O\. No\.\s*(\d+)', pdf_text) else 'N/A',
        'File Name': re.search(r'(.*)\nCustomer', pdf_text).group(1) if re.search(r'(.*)\nCustomer', pdf_text) else 'N/A',
        'Type/Description': re.search(r'Material / Item Type and Description\s*([^\n]*)', pdf_text).group(1).strip() if re.search(r'Material / Item Type and Description\s*([^\n]*)', pdf_text) else 'N/A',
        'Location': re.search(r'Location\s*(.*?)\s*Cert\. No\.', pdf_text).group(1).strip() if re.search(r'Location\s*(.*?)\s*Cert\. No\.', pdf_text) else 'N/A',        'Certificate No': re.search(r'Cert\. No\.\s*(\S+)', pdf_text).group(1) if re.search(r'Cert\. No\.\s*(\S+)', pdf_text) else 'N/A',
        'Certificate No': re.search(r'Cert\. No\.\s*(.*?)\s*Material / Item Type and Description', pdf_text).group(1) if re.search(r'Cert\. No\.\s*(.*?)\s*Material / Item Type and Description', pdf_text) else 'N/A',
        'Part No' : re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', pdf_text).group(1).strip() if re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', pdf_text) else 'N/A',
        'Serial No.': re.search(r'(?:Material \/ Item serial No\.\s*)?(\S.*?)(?:\s+(?:Part No|Project|PROJECT)|\s*$)', pdf_text).group(1) if re.search(r'(?:Material \/ Item serial No\.\s*)?(\S.*?)(?:\s+(?:Part No|Project|PROJECT)|\s*$)', pdf_text) else 'N/A',
        'Inspection Date': re.search(r'Date of Inspection\.\s*([\d\-]+)', pdf_text).group(1).strip() if re.search(r'Date of Inspection\.\s*([\d\-]+)', pdf_text) else 'N/A',
        'Expire Date': re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", pdf_text).group(1).strip() if re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", pdf_text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', pdf_text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', pdf_text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text) else 'N/A',
        'Remarks': re.search(r'Area of inspection:\s*(.*?)\s*Results', pdf_text).group(1).strip() if re.search(r'Area of inspection:\s*(.*?)\s*Results', pdf_text) else 'N/A',
        'Customer': re.search(r"(?:Customer|CUSTOMER\s*:)\s*(.*?)\s*Date of Work", pdf_text).group(1).strip() if re.search(r"(?:Customer|CUSTOMER\s*:)\s*(.*?)\s*Date of Work", pdf_text) else 'N/A',
    }


def extract_boroscopic_mpi_data(pdf_text):
    return {
        'Work Order No': re.search(r'W\.O\. No\.\s*(\d+)', pdf_text).group(1) if re.search(r'W\.O\. No\.\s*(\d+)', pdf_text) else 'N/A',
        'File Name': re.search(r'(.*)\nCustomer', pdf_text).group(1) if re.search(r'(.*)\nCustomer', pdf_text) else 'N/A',
        'Type/Description': re.search(r'Material / Item Type and Description\s*([^\n]*)', pdf_text).group(1).strip() if re.search(r'Material / Item Type and Description\s*([^\n]*)', pdf_text) else 'N/A',
        'Location': re.search(r'Location\s*(.*?)\s*Cert\. No\.', pdf_text).group(1).strip() if re.search(r'Location\s*(.*?)\s*Cert\. No\.', pdf_text) else 'N/A', 
        'Certificate No': re.search(r'Cert\. No\.\s*(.*?)\s*Material / Item Type and Description', pdf_text).group(1) if re.search(r'Cert\. No\.\s*(.*?)\s*Material / Item Type and Description', pdf_text) else 'N/A',
        'Part No' : re.search(r'Material\s*/\s*Item\s*serial\s*No\.\s*(.*?)\s*Type\s*of\s*Inspection', pdf_text).group(1).strip() if re.search(r'Material\s*/\s*Item\s*serial\s*No\.\s*(.*?)\s*Type\s*of\s*Inspection', pdf_text) else 'N/A',
        'Serial No.': re.search(r'Material\s*/\s*Item\s*serial\s*No\.\s*(.*)', pdf_text).group(1) if re.search(r'Material\s*/\s*Item\s*serial\s*No\.\s*(.*)', pdf_text) else 'N/A',
        'Inspection Date': re.search(r'Date of Inspection\.\s*([\d\-]+)', pdf_text).group(1).strip() if re.search(r'Date of Inspection\.\s*([\d\-]+)', pdf_text) else 'N/A',
        'Expire Date': re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", pdf_text).group(1).strip() if re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", pdf_text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', pdf_text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', pdf_text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text) else 'N/A',
        'Remarks': re.search(r'Area of inspection:\s*(.*?)\s*Results', pdf_text).group(1).strip() if re.search(r'Area of inspection:\s*(.*?)\s*Results', pdf_text) else 'N/A',
        'Customer': re.search(r"(?:Customer|CUSTOMER\s*:)\s*(.*?)\s*Date of Work", pdf_text).group(1).strip() if re.search(r"(?:Customer|CUSTOMER\s*:)\s*(.*?)\s*Date of Work", pdf_text) else 'N/A',
    }


def extract_liquid_penetrant_data(pdf_text):
    return {
        'Work Order No': re.search(r'W\.O\. No\.\s*(\d+)', pdf_text).group(1) if re.search(r'W\.O\. No\.\s*(\d+)', pdf_text) else 'N/A',
        'File Name': re.search(r"(.*?)\s*(?:CUSTOMER :|Customer)", pdf_text).group(1) if re.search(r"(.*?)\s*(?:CUSTOMER :|Customer)", pdf_text) else 'N/A',
        'Type/Description': re.search(r'Material / Item Type and Description\s*([^\n]*)', pdf_text).group(1).strip() if re.search(r'Material / Item Type and Description\s*([^\n]*)', pdf_text) else 'N/A',
        'Location': re.search(r'Location\s*(.*?)\s*Cert\. No\.', pdf_text).group(1).strip() if re.search(r'Location\s*(.*?)\s*Cert\. No\.', pdf_text) else 'N/A',        'Certificate No': re.search(r'Cert\. No\.\s*(\S+)', pdf_text).group(1) if re.search(r'Cert\. No\.\s*(\S+)', pdf_text) else 'N/A',
        'Certificate No': re.search(r'Cert\. No\.\s*(.*?)\s*Material / Item Type and Description', pdf_text).group(1) if re.search(r'Cert\. No\.\s*(.*?)\s*Material / Item Type and Description', pdf_text) else 'N/A',
        'Part No' : re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', pdf_text).group(1).strip() if re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', pdf_text) else 'N/A',
        'Serial No.': re.search(r'(?:Material \/ Item serial No\.\s*)?(\S.*?)(?:\s+(?:Part No|Project|PROJECT)|\s*$)', pdf_text).group(1) if re.search(r'(?:Material \/ Item serial No\.\s*)?(\S.*?)(?:\s+(?:Part No|Project|PROJECT)|\s*$)', pdf_text) else 'N/A',
        'Inspection Date': re.search(r'Date of Inspection\.\s*([\d\-]+)', pdf_text).group(1).strip() if re.search(r'Date of Inspection\.\s*([\d\-]+)', pdf_text) else 'N/A',
        'Expire Date': re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", pdf_text).group(1).strip() if re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", pdf_text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', pdf_text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', pdf_text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text) else 'N/A',
        'Remarks': re.search(r'Area of inspection:\s*(.*?)\s*Results', pdf_text).group(1).strip() if re.search(r'Area of inspection:\s*(.*?)\s*Results', pdf_text) else 'N/A',
        'Customer': re.search(r"(?:Customer|CUSTOMER\s*:)\s*(.*?)\s*Date of Work", pdf_text).group(1).strip() if re.search(r"(?:Customer|CUSTOMER\s*:)\s*(.*?)\s*Date of Work", pdf_text) else 'N/A',
    }

def extract_drill_pipe_pxb(pdf_text):
    return {
        'Work Order No': re.search(r'WORK ORDER NUM\s+(.*)', pdf_text).group(1) if re.search(r'WORK ORDER NUM\s+(.*)', pdf_text) else 'N/A',
        'File Name': extract_pxb_file_name(pdf_text),
        'Type/Description': re.search(r"Type Of Inspection\s+(.*?)\s+TYPE OF CONNECTION", pdf_text).group(1).strip() if re.search(r"Type Of Inspection\s+(.*?)\s+TYPE OF CONNECTION", pdf_text) else 'N/A',
        'Location': re.search(r"Location\s+(.*?)\s+CONSUMABLE", pdf_text).group(1).strip() if re.search(r"Location\s+(.*?)\s+CONSUMABLE", pdf_text) else 'N/A',        
        # 'Certificate No': re.search(r'Cert\. No\.\s*(\S+)', pdf_text).group(1) if re.search(r'Cert\. No\.\s*(\S+)', pdf_text) else 'N/A',
        'Certificate No': re.search(r'Certificate No:\s*([A-Za-z0-9\(\)\-]+)', pdf_text).group(1) if re.search(r'Certificate No:\s*([A-Za-z0-9\(\)\-]+)', pdf_text) else 'N/A',
        'Part No' : re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', pdf_text).group(1).strip() if re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', pdf_text) else 'N/A',
        'Serial No.': extract_pxb_serial_no(pdf_text),
        'Inspection Date': re.search(r'DATE OF WORK\s+(.*?)\s+JOB NUMBER', pdf_text).group(1).strip() if re.search(r'DATE OF WORK\s+(.*?)\s+JOB NUMBER', pdf_text) else 'N/A',
        'Expire Date': re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", pdf_text).group(1).strip() if re.search(r"Validity of Inspection:\s*(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}[-/]\d{2}[-/]\d{4})", pdf_text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', pdf_text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', pdf_text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text) else 'N/A',
        'Remarks': re.search(r'Area of inspection:\s*(.*?)\s*Results', pdf_text).group(1).strip() if re.search(r'Area of inspection:\s*(.*?)\s*Results', pdf_text) else 'N/A',
        'Customer': re.search(r'Customer\s+(.*?)\s+Location', pdf_text).group(1).strip() if re.search(r'Customer\s+(.*?)\s+Location', pdf_text) else 'N/A',
    }


def extract_string_stabilizer_data(text):
    return {
        'Work Order No': re.search(r'Certificate No: SS-(.*?)-', text).group(1) if re.search(r'Certificate No: SS-(.*?)-', text) else 'N/A',
        'File Name': re.search(r'(.*)\s+Customer', text).group(1) if re.search(r'(.*)\s+Customer', text) else 'N/A',
        'Type/Description': re.search(r"FIELD DIRECTION\s*-?\s*\n.*\n(.*)", text).group(1).strip() if re.search(r"FIELD DIRECTION\s*-?\s*\n.*\n(.*)", text) else 'N/A',
        'Location': re.search(r'Location/Used at:\s*(.*)', text).group(1).strip() if re.search(r'Location/Used at:\s*(.*)', text) else 'N/A',       
        #   'Certificate No': re.search(r'Cert\. No\.\s*(\S+)', pdf_text).group(1) if re.search(r'Cert\. No\.\s*(\S+)', pdf_text) else 'N/A',
        'Certificate No': re.search(r'Certificate No:\s*([A-Za-z0-9\(\)\-]+)', text).group(1) if re.search(r'Certificate No:\s*([A-Za-z0-9\(\)\-]+)', text) else 'N/A',
        'Part No' : re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', text).group(1).strip() if re.search(r'(?:Part No\.?|PROJECT|Project:)\s*(.*?)(?=\n|$)', text) else 'N/A',
        'Serial No.': re.search(r'FIELD DIRECTION(?:\s*-?\n)+.*?\n.*?(\d+)', text).group(1) if re.search(r'FIELD DIRECTION(?:\s*-?\n)+.*?\n.*?(\d+)', text) else 'N/A',
        'Inspection Date': re.search(r'Tools Pictures\s*(.*)', text).group(1).strip() if re.search(r'Tools Pictures\s*(.*)', text) else 'N/A',
        'Expire Date': re.search(r'Due Date\s*(.*)', text).group(1).strip() if re.search(r'Due Date\s*(.*)', text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text) else 'N/A',
        'Remarks': re.search(r'Tools Pictures\s+(.*?)\n(.*?)\n(.*?)\n', text).group(1).strip() if re.search(r'Tools Pictures\s+(.*?)\n(.*?)\n(.*?)\n', text) else 'N/A',
        'Customer': re.search(r'Customer\s+(.*?)\s+Location', text).group(1).strip() if re.search(r'Customer\s+(.*?)\s+Location', text) else 'N/A'
    }

def extract_dye_penetrant_data(pdf_text):
    return {
        'Work Order No': re.search(r'W\.?[O0]\.?\s*No\.?\s*(\S+)', pdf_text).group(1) if re.search(r'W\.?[O0]\.?\s*No\.?\s*(\S+)', pdf_text) else 'N/A',
        'File Name': re.search(r'(.*)\n.*Customer', pdf_text).group(1).strip() if re.search(r'(.*)\n.*Customer', pdf_text) else 'N/A',
        'Type/Description': re.search(r'Material / Item Type and Description\s*([^\n]*)', pdf_text).group(1).strip() if re.search(r'Material / Item Type and Description\s*([^\n]*)', pdf_text) else 'N/A',
        'Part no': re.search(r'Model \.\s*(.*)', pdf_text).group(1).strip() if re.search(r'Model \.\s*(.*)', pdf_text) else 'N/A',
        'Location': re.search(r'Location\.\s*([\w\s\-]+)', pdf_text).group(1).strip() if re.search(r'Location\.\s*([\w\s\-]+)', pdf_text) else 'N/A',
        'Certificate No': re.search(r'Cert\. No\.\s*(\S+)', pdf_text).group(1) if re.search(r'Cert\. No\.\s*(\S+)', pdf_text) else 'N/A',
        'Serial No.': re.search(r'Material / Item serial No\.\s*(.*?)\s*Model \.', pdf_text).group(1).strip() if re.search(r'Material / Item serial No\.\s*(.*?)\s*Model \.', pdf_text) else 'N/A',
        'Inspection date': re.search(r'Date of Work\s*(.*?)(?:\s+Rig|$)', pdf_text).group(1) if re.search(r'Date of Work\s*(.*?)(?:\s+Rig|$)', pdf_text) else 'N/A',
        'Expire date': re.search(r'Validity of Inspection:\s*([\d\-]+)', pdf_text).group(1) if re.search(r'Validity of Inspection:\s*([\d\-]+)', pdf_text) else 'N/A',
        'Fit for use': re.search(r'Fit for use:\s*([A-Za-z\s]+)', pdf_text).group(1).strip() if re.search(r'Fit for use:\s*([A-Za-z\s]+)', pdf_text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', pdf_text) else 'N/A',
        'Detailed Remarks': re.search(r'Recommendation/ Comments:\s*(.+)', pdf_text).group(1).strip() if re.search(r'Recommendation/ Comments:\s*(.+)', pdf_text) else 'N/A',
        'Customer': re.search(r'Customer\s*(.*?)\s*Date of Work', pdf_text).group(1).strip() if re.search(r'Customer\s*(.*?)\s*Date of Work', pdf_text) else 'N/A',
    }


def extract_ultrasonic_thickness_measurment(text):
    return {
        'Work Order No': re.search(r"Work Order No:\s*(\d+)", text).group(1) if re.search(r"Work Order No:\s*(\d+)", text) else 'N/A',
        'File Name': re.search(r'^(.*\bSHEET\b.*)$', text, re.MULTILINE).group(1).strip() if re.search(r'^(.*\bSHEET\b.*)$', text, re.MULTILINE) else None,
        'Type/Description': re.search(r"Matrial /Item type & Description\s*(.+)", text).group(1).strip() if re.search(r"Matrial /Item type & Description\s*(.+)", text) else 'N/A',
        'Location': re.search(r"Location:\s*(.*?)\s*(?=Work Order No:|Sub Location)", text).group(1).strip() if re.search(r"Location:\s*(.*?)\s*(?=Work Order No:|Sub Location)", text) else 'N/A',       
        'Certificate No': re.search(r"(?:Certificate No|Cert\. No:)\s*([^\s]+)", text).group(1) if re.search(r"(?:Certificate No|Cert\. No:)\s*([^\s]+)", text) else 'N/A',
        'Part No' : re.search(r"Sub Location\s*(.+)", text).group(1).strip() if re.search(r"Sub Location\s*(.+)", text) else 'N/A',
        'Serial No.': re.search(r"Matrial /Item Type serial NO\s*(.+)", text).group(1) if re.search(r"Matrial /Item Type serial NO\s*(.+)", text) else 'N/A',
        'Inspection Date': re.search(r'Inspection Date:\s*([\w-]+)', text).group(1).strip() if re.search(r'Inspection Date:\s*([\w-]+)', text) else 'N/A',
        'Expire Date': re.search(r'Due Date[:;]\s*([\w-]+)', text).group(1).strip() if re.search(r'Due Date[:;]\s*([\w-]+)', text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text) else 'N/A',
        'Remarks': re.search(r"RESULT:\s*(.+)", text).group(1).strip() if re.search(r"RESULT:\s*(.+)", text) else 'N/A',
        'Customer': re.search(r"Customer:\s*(.+?)\s*(?=Cert\. No:|Certificate No)", text).group(1).strip() if re.search(r"Customer:\s*(.+?)\s*(?=Cert\. No:|Certificate No)", text) else 'N/A'
    }

def extract_ultrasonic_thickness_measurment_mpi(text):
    return {
        'Work Order No': re.search(r"Work Order No:\s*(\d+)", text).group(1) if re.search(r"Work Order No:\s*(\d+)", text) else 'N/A',
        'File Name': re.search(r'^(.*\bSHEET\b.*)$', text, re.MULTILINE).group(1) if re.search(r'^(.*\bSHEET\b.*)$', text, re.MULTILINE) else 'N/A',
        'Type/Description': re.search(r"Matrial /Item type & Description\s*(.+)", text).group(1).strip() if re.search(r"Matrial /Item type & Description\s*(.+)", text) else 'N/A',
        'Location': re.search(r"Location:\s*(.*?)\s*Sub Location", text).group(1).strip() if re.search(r"Location:\s*(.*?)\s*Sub Location", text) else 'N/A',       
        'Certificate No': re.search(r"Cert\s*\.\s*No\s*(.*)", text).group(1) if re.search(r"Cert\s*\.\s*No\s*(.*)", text) else 'N/A',
        'Part No' : re.search(r"Sub Location\s*(.+)", text).group(1).strip() if re.search(r"Sub Location\s*(.+)", text) else 'N/A',
        'Serial No.': re.search(r'(?:Matrial /Item Type serial No|Matrial /Item Type serial NO)[:\s]+(.+?)(?:\s|$)', text).group(1) if re.search(r'(?:Matrial /Item Type serial No|Matrial /Item Type serial NO)[:\s]+(.+?)(?:\s|$)', text) else 'N/A',
        'Inspection Date': re.search(r'Inspection Date:\s*([\w-]+)', text).group(1).strip() if re.search(r'Inspection Date:\s*([\w-]+)', text) else 'N/A',
        'Expire Date': re.search(r'Due Date[:;]\s*([\w-]+)', text).group(1).strip() if re.search(r'Due Date[:;]\s*([\w-]+)', text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text) else 'N/A',
        'Remarks': re.search(r"RESULT:\s*(.+)", text).group(1).strip() if re.search(r"RESULT:\s*(.+)", text) else 'N/A',
        'Customer': re.search(r"Customer\s*:\s*(.*?)(?=\s+Rig\s*/\s*Well\s+No)", text).group(1).strip() if re.search(r"Customer\s*:\s*(.*?)(?=\s+Rig\s*/\s*Well\s+No)", text) else 'N/A'
    }



def extract_drilling_tool(text):
    return {
        'Work Order No': re.search(r"W\.O NO\.\s*(.+)", text).group(1) if re.search(r"W\.O NO\.\s*(.+)", text) else 'N/A',
        'File Name': re.search(r'^.*', text).group(0) if re.search(r'^.*', text) else 'N/A',
        'Type/Description': re.search(r"TYPE OF INSPECTION\s+(.*?)\s+STANDARD:", text).group(1).strip() if re.search(r"TYPE OF INSPECTION\s+(.*?)\s+STANDARD:", text) else 'N/A',
        'Location': re.search(r"LOCATION:\s+(.*?)\s+DATE OF WORK", text).group(1).strip() if re.search(r"LOCATION:\s+(.*?)\s+DATE OF WORK", text) else 'N/A',       
        'Certificate No': dt_extracted_serial(text)[0:10] if dt_extracted_serial(text) else None,
        'Part No' : re.search(r"DEPARTMENT\s+(.*?)\s+PTIS W\.O NO", text).group(1).strip() if re.search(r"DEPARTMENT\s+(.*?)\s+PTIS W\.O NO", text) else 'N/A',
        'Serial No.': dt_extracted_serial(text),
        'Inspection Date': re.search(r"DATE OF WORK:\s+(.*)", text).group(1).strip() if re.search(r"DATE OF WORK:\s+(.*)", text) else 'N/A',
        'Expire Date': re.search(r"Due Date;\s*(.+)", text).group(1).strip() if re.search(r"Due Date;\s*(.+)", text) else 'N/A',
        'Fit for use': re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text).group(1).strip() if re.search(r'Results\s*:\s*(.*?)\s*Recommendation', text) else 'N/A',
        'Fit/Rejected': re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text).group(1).strip() if re.search(r'Fit/Rejected:\s*([A-Za-z\s]+)', text) else 'N/A',
        'Remarks': re.search(r"RESULT:\s*(.+)", text).group(1).strip() if re.search(r"RESULT:\s*(.+)", text) else 'N/A',
        'Customer': re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', text) else 'N/A'
    }


def extract_casing_tubing_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[0] if len(words) > 1 else ''
                third_word = " ".join(words[-2]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({third_word}{last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        "Work Order No": re.search(r"W\.O NO:\s*(.+)", pdf_text).group(1) if re.search(r"W\.O NO:\s*(.+)", pdf_text) else None,
        "File Name": (
        re.search(r"Fax #.*\n(.+)", pdf_text).group(1).strip() 
        if re.search(r"Fax #.*\n(.+)", pdf_text) 
        else re.search(r'^.*', pdf_text).group(0).strip() 
        if re.search(r'^.*', pdf_text) 
        else None),
        "Type/Description": re.search(r"SIZE\s*:(.*)", pdf_text).group(0).strip() if re.search(r"SIZE\s*:(.*)", pdf_text) else None,
        "Location": re.search(r"LOCATION:\s*(.*?)\s*W\.O NO:", pdf_text).group(1) if re.search(r"LOCATION:\s*(.*?)\s*W\.O NO:", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": 
        (serial_info[:3] + ""if serial_info else"") + # Add first two characters of serial_info
        "-" +
        ( serial_info[-13]+  ""if serial_info else "") +
        ( serial_info[-12]+  "" if serial_info else "") +
        ( serial_info[-14]+  "" if serial_info else "") +
        "-" +
        (re.search(r"W\.O NO:\s*(.+)", pdf_text).group(1) if re.search(r"W\.O NO:\s*(.+)", pdf_text) else ""),
        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE:\s*(.+)", pdf_text).group(1) if re.search(r"DATE:\s*(.+)", pdf_text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', pdf_text).group(1) if re.search(r'Due Date\s*(.*)', pdf_text) else None,
        "Fit for use": re.search(r'FIT FOR USE:\s*(\S+)', pdf_text).group(1) if re.search(r'FIT FOR USE:\s*(\S+)', pdf_text) else None,
        "Fit/Rejected": re.search(r'Fit/Rejected:\s*(\S+)', pdf_text).group(1).strip() if re.search(r'Fit/Rejected:\s*(\S+)', pdf_text) else None,
        "Remarks": re.search(r".*TOTAL TALLY LENGTH MEASURED.*", pdf_text).group(0).strip() if re.search(r".*TOTAL TALLY LENGTH MEASURED.*", pdf_text) else None,
        "Customer": re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text) else None
    }


def extract_tubing_ppf_pup_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[0] if len(words) > 1 else ''
                # third_word = " ".join(words[-2]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        "Work Order No": re.search(r"W\.O#\s*(.*)", pdf_text).group(1) if re.search(r"W\.O#\s*(.*)", pdf_text) else None,
        "File Name": re.search(r"Fax #.*\n(.+)", pdf_text).group(1).strip() if re.search(r"Fax #.*\n(.+)", pdf_text) else None,
        "Type/Description": re.search(r"TYPE OF INSPECTION\s(.*?)\sDRIFT SIZE OD", pdf_text).group(1).strip() if re.search(r"TYPE OF INSPECTION\s(.*?)\sDRIFT SIZE OD", pdf_text) else None,
        "Location": re.search(r"LOCATION\s(.*?)\sNOMINAL O\.D", pdf_text).group(1) if re.search(r"LOCATION\s(.*?)\sNOMINAL O\.D", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": 
        (serial_info[:3] + ""if serial_info else"") + # Add first two characters of serial_info
        "-" +
        ( serial_info[-29]+  ""if serial_info else "") +
        ( serial_info[-12]+  "" if serial_info else "") +
        ( serial_info[-14]+  "" if serial_info else "") +
        "-" +
        (re.search(r"W\.O#\s*(.*)", pdf_text).group(1) if re.search(r"W\.O#\s*(.*)", pdf_text) else ""),
        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE:\s*(.+)", pdf_text).group(1) if re.search(r"DATE:\s*(.+)", pdf_text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', pdf_text).group(1) if re.search(r'Due Date\s*(.*)', pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Customer": re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text) else None
    }


def extract_od_pupjoint_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[0] if len(words) > 1 else ''
                # third_word = " ".join(words[-2]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        "Work Order No": re.search(r"W\.O#\s*(.*)", pdf_text).group(1) if re.search(r"W\.O#\s*(.*)", pdf_text) else None,
        "File Name": re.search(r"Fax #.*\n(.*)\nCUSTOMER", pdf_text).group(1).strip() if re.search(r"Fax #.*\n(.*)\nCUSTOMER", pdf_text) else None,
        "Type/Description": re.search(r"TYPE OF INSPECTION(.*?)DRIFT OD", pdf_text).group(1).strip() if re.search(r"TYPE OF INSPECTION(.*?)DRIFT OD", pdf_text) else None,
        "Location": re.search(r"LOCATION\s(.*?)\sNOMINAL O\.D", pdf_text).group(1) if re.search(r"LOCATION\s(.*?)\sNOMINAL O\.D", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": 
        (serial_info[:3] + ""if serial_info else"") + # Add first two characters of serial_info
        "-" +
        ( serial_info[-29]+  ""if serial_info else "") +
        ( serial_info[-12]+  "" if serial_info else "") +
        ( serial_info[-14]+  "" if serial_info else "") +
        "-" +
        (re.search(r"W\.O#\s*(.*)", pdf_text).group(1) if re.search(r"W\.O#\s*(.*)", pdf_text) else ""),
        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE:\s*(.+)", pdf_text).group(1) if re.search(r"DATE:\s*(.+)", pdf_text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', pdf_text).group(1) if re.search(r'Due Date\s*(.*)', pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Customer": re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text) else None
    }


def extract_od_tubing_tally_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[0] if len(words) > 1 else ''
                # third_word = " ".join(words[-2]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        "Work Order No": re.search(r"W\.O#\s*(.*)", pdf_text).group(1) if re.search(r"W\.O#\s*(.*)", pdf_text) else None,
        "File Name": re.search(r"Fax #.*\n(.*)\nCUSTOMER", pdf_text).group(1).strip() if re.search(r"Fax #.*\n(.*)\nCUSTOMER", pdf_text) else None,
        "Type/Description": re.search(r"TYPE OF INSPECTION(.*?)DRIFT OD", pdf_text).group(1).strip() if re.search(r"TYPE OF INSPECTION(.*?)DRIFT OD", pdf_text) else None,
        "Location": re.search(r"LOCATION\s(.*?)\sNOMINAL O\.D", pdf_text).group(1) if re.search(r"LOCATION\s(.*?)\sNOMINAL O\.D", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": 
        (serial_info[:3] + ""if serial_info else"") + # Add first two characters of serial_info
        "-" +
        ( serial_info[-29]+  ""if serial_info else "") +
        ( serial_info[-12]+  "" if serial_info else "") +
        ( serial_info[-14]+  "" if serial_info else "") +
        "-" +
        (re.search(r"W\.O#\s*(.*)", pdf_text).group(1) if re.search(r"W\.O#\s*(.*)", pdf_text) else ""),
        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE:\s*(.+)", pdf_text).group(1) if re.search(r"DATE:\s*(.+)", pdf_text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', pdf_text).group(1) if re.search(r'Due Date\s*(.*)', pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Customer": re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text) else None
    }



def dt_extracted_serial(pdf_text):
    extracted_info = []

    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok','OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[1] if len(words) > 1 else ''
                second_last_word = words[-2] if len(words) > 1 else ''
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"{second_word} ({second_last_word} {last_word})")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    return ''.join(extracted_info)





def extract_pxb_file_name(text):
    # Search for the pattern before "Customer"
    file_name_match = re.search(r"(.*?)\s*(?:Customer)", text)
    
    if file_name_match:
        # Extract the match
        extracted_data = file_name_match.group(1)
        # Add spaces between 'DRILLING' and 'TOOLS', as well as around '(PXB)'
        formatted_file_name = extracted_data.replace("(PXB)", "( P x B )")
    else:
        # If no match is found, return None
        formatted_file_name = None
    
    # Return the formatted file name or None
    return formatted_file_name

def extract_pxb_serial_no(text):
    extracted_info = []

    # Split the PDF text by lines
    for text in text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second word if available
                second_word = words[1] if len(words) > 1 else ''
            
                # Extract the last two words
                last_two_words = " ".join(words[-2:]) if len(words) >= 2 else ''

                # Append formatted string
                extracted_info.append(f"[{second_word}, ({last_two_words})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    # Use the extracted serial information as needed
    return ', '.join(extracted_info) if extracted_info else None


def extract_drill_pipe_remarks_section_2(text):
    # Step 1: Extract text between "REMARKS" and "ABBREVIATIONS"
    match = re.search(r'REM ARKS\s(.*?)\sABBREVIATIONS', text, re.DOTALL)

    if match:
        remarks_section = match.group(1).strip()

        # Step 2: Extract first and last words from each line
        lines = remarks_section.split('\n')
        results = []

        for line in lines:
            words = line.split()
            if len(words) > 2:
                first_word = words[0]  # First word after space
                second_last = words[-2]
                last_word = words[-1]  # Last word
                # Combine first and last words into a string
                results.append(f"[{first_word} ({second_last} {last_word})] ")

        # Join the results into a single string with newlines between entries
        return ''.join(results)
    
    return None


def extract_drill_pipe_combined_remarks(text):
    result = extract_drill_pipe_remarks_section_1(text)
    
    if result is None:
        result = extract_drill_pipe_remarks_section_2(text)
    
    if result is None:
        print("None")
    
    return result



def extract_drill_pipe_remarks_section_1(text):
    # Step 1: Extract text between "REMARKS" and "ABBREVIATIONS"
    match = re.search(r'REMA RKS\s(.*?)\sABBREVIATIONS', text, re.DOTALL)

    if match:
        remarks_section = match.group(1).strip()

        # Step 2: Extract first and last words from each line
        lines = remarks_section.split('\n')
        results = []

        for line in lines:
            words = line.split()
            if len(words) > 2:
                first_word = words[1]  # First word after space
                last_word = words[-1]  # Last word
                # Combine first and last words into a string
                results.append(f"[{first_word} ({last_word})] ")

        # Join the results into a single string with newlines between entries
        return ''.join(results)
    
    return None



def drilling_tool_extracted_serial(text):
    extracted_info = []

    for text in text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok','OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[1] if len(words) > 1 else ''
                second_last_word = words[-2] if len(words) > 1 else ''
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({second_last_word} {last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    return ''.join(extracted_info)





def extract_last_line_above_customer(text):
    lines = text.split('\n')
    for i in range(len(lines)):
        if 'Customer' in lines[i] or 'CUSTOMER :' in lines[i]:
            # Return the last line before the current one
            return lines[i-1].strip() if i > 0 else 'N/A'
    return 'N/A'


def hw_extracted_serial(text):
    extracted_info = []

    for text in text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok','OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[1] if len(words) > 1 else ''
                second_last_word = words[-2] if len(words) > 1 else ''
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({second_last_word} {last_word})]--")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    return ''.join(extracted_info)


def dc_extracted_serial(extracted_data):
    extracted_info = []

    for text in extracted_data.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[1] if len(words) > 1 else ''
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"{second_word}  [{last_word}]--")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    return ''.join(extracted_info)


def find_inspection_date(text):
    # Try the first pattern
    match = re.search(r"Work Order No:\s*\d+\s*(?:\n.*?\s*(\d{2}-\d{2}-\d{4})|(?:Inspection Date:\s*(\d{2}-\d{2}-\d{4})))", text, re.DOTALL)
    if match:
        return match.group(1) if match.group(1) else match.group(2)
    
    # If no match, try the second pattern
    match = re.search(r"Inspection Date:\s*(\d{2}-\d{2}-\d{4})", text)
    return match.group(1) if match else None

def extract_due_date(text):
    # Print text for debugging purposes
    # print("Text for due date extraction:", text)

    # First pattern: tries to find a date before "Inspection Date"
    pattern1 = r"(\d{2}-\d{2}-\d{4})(?=\s*Inspection Date)"
    match1 = re.search(pattern1, text)
    
    if match1:
        # print(f"Found due date before 'Inspection Date': {match1.group(1)}")
        return match1.group(1)
    
    # Second pattern: tries to find a date after "Due Date:"
    pattern2 = r"Due Date:\s*(\d{2}-\d{2}-\d{4})"
    match2 = re.search(pattern2, text)
    
    if match2:
        # print(f"Found due date after 'Due Date:': {match2.group(1)}")
        return match2.group(1)
    
    # If neither pattern matches, return None
    print("No due date found.")
    return None

def extract_casing_talling_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[0] if len(words) > 1 else ''
                # third_word = " ".join(words[-2]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        "Work Order No": re.search(r"W\.O#\s*(.*)", pdf_text).group(1) if re.search(r"W\.O#\s*(.*)", pdf_text) else None,
        "File Name": re.search(r"Fax #.*\n(.+)", pdf_text).group(1).strip() if re.search(r"Fax #.*\n(.+)", pdf_text) else None,
        "Type/Description": re.search(r"TYPE OF INSPECTION\s(.*?)\sDRIFT SIZE OD", pdf_text).group(1).strip() if re.search(r"TYPE OF INSPECTION\s(.*?)\sDRIFT SIZE OD", pdf_text) else None,
        "Location": re.search(r"LOCATION\s(.*?)\sNOMINAL O\.D", pdf_text).group(1) if re.search(r"LOCATION\s(.*?)\sNOMINAL O\.D", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": 
        (serial_info[:3] + ""if serial_info else"") + # Add first two characters of serial_info
        "-" +
        ( serial_info[-9]+  ""if serial_info else "") +
        ( serial_info[-8]+  "" if serial_info else "") +
        ( serial_info[-7]+  "" if serial_info else "") +
        "-" +
        (re.search(r"W\.O#\s*(.*)", pdf_text).group(1) if re.search(r"W\.O#\s*(.*)", pdf_text) else "") +
        "]" ,
        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE:\s*(.+)", pdf_text).group(1) if re.search(r"DATE:\s*(.+)", pdf_text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', pdf_text).group(1) if re.search(r'Due Date\s*(.*)', pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Customer": re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text) else None
    }


def extract_pup_joint_tally_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[0] if len(words) > 1 else ''
                # third_word = " ".join(words[-2]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        "Work Order No": re.search(r"W\.O#\s*(.*)", pdf_text).group(1) if re.search(r"W\.O#\s*(.*)", pdf_text) else None,
        "File Name": re.search(r"Fax #.*\n(.+)", pdf_text).group(1).strip() if re.search(r"Fax #.*\n(.+)", pdf_text) else None,
        "Type/Description": re.search(r"TYPE OF INSPECTION\s(.*?)\sDRIFT SIZE OD", pdf_text).group(1).strip() if re.search(r"TYPE OF INSPECTION\s(.*?)\sDRIFT SIZE OD", pdf_text) else None,
        "Location": re.search(r"LOCATION\s(.*?)\sNOMINAL O\.D", pdf_text).group(1) if re.search(r"LOCATION\s(.*?)\sNOMINAL O\.D", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": 
        (serial_info[:3] + ""if serial_info else"") + # Add first two characters of serial_info
        "-" +
        ( serial_info[-9]+  ""if serial_info else "") +
        ( serial_info[-8]+  "" if serial_info else "") +
        ( serial_info[-7]+  "" if serial_info else "") +
        "-" +
        (re.search(r"W\.O#\s*(.*)", pdf_text).group(1) if re.search(r"W\.O#\s*(.*)", pdf_text) else "") +
        "]" ,
        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE:\s*(.+)", pdf_text).group(1) if re.search(r"DATE:\s*(.+)", pdf_text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', pdf_text).group(1) if re.search(r'Due Date\s*(.*)', pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Customer": re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text) else None
    }


def extract_x_over_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[0] if len(words) > 1 else ''
                # third_word = " ".join(words[-2]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        "Work Order No": re.search(r"W\.ORDER :\s*(\d+)", pdf_text).group(1) if re.search(r"W\.ORDER :\s*(\d+)", pdf_text) else None,
        "File Name": re.search(r"Fax #.*\n(.+)", pdf_text).group(1).strip() if re.search(r"Fax #.*\n(.+)", pdf_text) else None,
        "Type/Description": re.search(r"TYPE OF INSPECTION:\s*(.*)", pdf_text).group(1).strip() if re.search(r"TYPE OF INSPECTION:\s*(.*)", pdf_text) else None,
        "Location": re.search(r"LOCATION:\s*(.*?)\s*RIG NO:", pdf_text).group(1) if re.search(r"LOCATION:\s*(.*?)\s*RIG NO:", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": 
        (serial_info[:3] + ""if serial_info else"") + # Add first two characters of serial_info
        "-" +
        ( serial_info[-9]+  ""if serial_info else "") +
        ( serial_info[-8]+  "" if serial_info else "") +
        ( serial_info[-7]+  "" if serial_info else "") +
        "-" +
        (re.search(r"W\.ORDER :\s*(\d+)", pdf_text).group(1) if re.search(r"W\.ORDER :\s*(\d+)", pdf_text) else "") +
        "]" ,
        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE:\s*(.+)", pdf_text).group(1) if re.search(r"DATE:\s*(.+)", pdf_text) else None,
        "Expire Date": re.search(r'Due Date\s*(.*)', pdf_text).group(1) if re.search(r'Due Date\s*(.*)', pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Customer": re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text).group(1).strip() if re.search(r'(?:Customer\s*|CUSTOMER\s*|CUSTOMER:\s*)(.*?)(?:\s*LOCATION|\s*Location|\s*DATE:)', pdf_text) else None
    }


def extract_crimping_tool_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[0] if len(words) > 1 else ''
                # third_word = " ".join(words[-2]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        'Work Order No': log_re_function(re.search,r"WO/PO\s+(.*?)\s+CERT", pdf_text).group(1) if log_re_function(re.search,r"WO/PO\s+(.*?)\s+CERT", pdf_text) else None,
        "File Name": re.search(r"(.*)\nCustomer", pdf_text).group(1).strip() if re.search(r"(.*)\nCustomer", pdf_text) else None,
        "Type/Description": re.search(r"DESCRIPTION\s+(.*?)(?=\s+SERIAL\s)", pdf_text).group(1).strip() if re.search(r"DESCRIPTION\s+(.*?)(?=\s+SERIAL\s)", pdf_text) else None,
        "Location": re.search(r"Location\s+(.*?)\s+WO/PO", pdf_text).group(1) if re.search(r"Location\s+(.*?)\s+WO/PO", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": re.search(r"CERT\.#\s+(.*)", pdf_text).group(1) if re.search(r"CERT\.#\s+(.*)", pdf_text) else None,
        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE:\s*(.+)", pdf_text).group(1) if re.search(r"DATE:\s*(.+)", pdf_text) else None,
        
        "Expire Date": re.search(r"([^\s]+)\s+Calibrated By:", pdf_text).group(1) if re.search(r"([^\s]+)\s+Calibrated By:", pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Customer": re.search(r"Customer Name\s+(.*?)\s+ISSUE DATE:", pdf_text).group(1).strip() if re.search(r"Customer Name\s+(.*?)\s+ISSUE DATE:", pdf_text) else None
    }


def extract_cis_crimping_tool_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[0] if len(words) > 1 else ''
                # third_word = " ".join(words[-2]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        'Work Order No': log_re_function(re.search,r"WO / PO\s*:\s*(.*?)\s*Cert\. No", pdf_text).group(1) if log_re_function(re.search,r"WO / PO\s*:\s*(.*?)\s*Cert\. No", pdf_text) else None,
        "File Name": (re.search(r"(.*)\nCustomer", pdf_text).group(1).strip() if re.search(r"(.*)\nCustomer", pdf_text) else "")
        + " "
        + (re.search(r"EQUIP\. NAME (.*?) MODEL", pdf_text).group(1).strip() if re.search(r"EQUIP\. NAME (.*?) MODEL", pdf_text) else ""),
        "Type/Description": re.search(r"EQUIP\. NAME (.*?) MODEL", pdf_text).group(1).strip() if re.search(r"EQUIP\. NAME (.*?) MODEL", pdf_text) else None,
        "Location": re.search(r"Location\s*:\s*(.*?)\s*WO / PO", pdf_text).group(1) if re.search(r"Location\s*:\s*(.*?)\s*WO / PO", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": re.search(r"Cert\. No\s*:\s*(.*?)\s*Issue Date", pdf_text).group(1) if re.search(r"Cert\. No\s*:\s*(.*?)\s*Issue Date", pdf_text) else None,
        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE:\s*(.+)", pdf_text).group(1) if re.search(r"DATE:\s*(.+)", pdf_text) else None,
        "Expire Date": re.search(r"(\S+)\s+Calibrated By", pdf_text).group(1) if re.search(r"(\S+)\s+Calibrated By", pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Customer": re.search(r"Customer\s*:\s*(.*)", pdf_text).group(1).strip() if re.search(r"Customer\s*:\s*(.*)", pdf_text) else None
    }




def extract_cis_psv_inspection(pdf_text):
    # Extract other key information using regex
    return {
        'Work Order No': log_re_function(re.search,r"WO / PO : (.*?) Cert.#", pdf_text).group(1) if log_re_function(re.search,r"WO / PO : (.*?) Cert.#", pdf_text) else None,
        "File Name": (re.search(r"(.*)\nCustomer", pdf_text).group(1).strip() if re.search(r"(.*)\nCustomer", pdf_text) else "")
        + " "
        + (re.search(r"Equipment Name (.*?) MODEL", pdf_text).group(1).strip() if re.search(r"Equipment Name (.*?) MODEL", pdf_text) else ""),
        "Type/Description": re.search(r"Equipment Name (.+)", pdf_text).group(1).strip() if re.search(r"Equipment Name (.+)", pdf_text) else None,
        "Location": re.search(r"Location\s*:\s*(.*?)\s*WO / PO", pdf_text).group(1) if re.search(r"Location\s*:\s*(.*?)\s*WO / PO", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": re.search(r"Cert\.# (.*?) Issue Date:", pdf_text).group(1) if re.search(r"Cert\.# (.*?) Issue Date:", pdf_text) else None,
        # "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DUE DATE\s+([^\s]+ [^\s]+)", pdf_text).group(1) if re.search(r"DUE DATE\s+([^\s]+ [^\s]+)", pdf_text) else None,
        "Expire Date": re.search(r"(\S+)\s+Calibrated By", pdf_text).group(1) if re.search(r"(\S+)\s+Calibrated By", pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"DISCLAIMER\s*(.+)", pdf_text).group(1).strip() if re.search(r"DISCLAIMER\s*(.+)", pdf_text) else None,
        "Customer": re.search(r"Customer Name : (.+)", pdf_text).group(1).strip() if re.search(r"Customer Name : (.+)", pdf_text) else None
    }





def extract_cis_decade_box_inspection(pdf_text):
    extracted_info = []

    # Split the PDF text by lines
    for text in pdf_text.split('\n'):
        text = text.strip()

        if not text:  # Skip empty lines
            continue

        try:
            # Ensure the first character is an integer for serial info extraction
            a = int(text[0])

            # Check for specific keywords
            if any(keyword in text for keyword in ('USEABLE', 'ok', 'OK','SATISFACTORY')):
                words = text.split()  # Split the line into words

                # Extract the second and last words if they exist
                second_word = words[0] if len(words) > 1 else ''
                # third_word = " ".join(words[-2]) if len(words) > 1 else ""
                last_word = words[-1] if words else ''

                # Append formatted string
                extracted_info.append(f"[{second_word} ({last_word})]")

        except ValueError:
            # Handle cases where text[0] is not an integer
            pass

    

    # Use the extracted serial information as needed
    serial_info = ', '.join(extracted_info) if extracted_info else None

    # Extract other key information using regex
    return {
        'Work Order No': log_re_function(re.search,r"WO / PO\s+(.*?)\s+CERT.#", pdf_text).group(1) if log_re_function(re.search,r"WO / PO\s+(.*?)\s+CERT.#", pdf_text) else None,
        "File Name": (re.search(r"(.*)\nCUSTOMER NAME :", pdf_text).group(1).strip() if re.search(r"(.*)\nCUSTOMER NAME :", pdf_text) else "")
        + " "
        + (re.search(r"EQUIPMENT NAME\s+(.*?)\s+MODEL #", pdf_text).group(1).strip() if re.search(r"EQUIPMENT NAME\s+(.*?)\s+MODEL #", pdf_text) else ""),
        "Type/Description": re.search(r"EQUIPMENT NAME\s+(.+)", pdf_text).group(1).strip() if re.search(r"EQUIPMENT NAME\s+(.+)", pdf_text) else None,
        "Location": re.search(r"LOCATION\s+(.*?)\s+WO / PO", pdf_text).group(1) if re.search(r"LOCATION\s+(.*?)\s+WO / PO", pdf_text) else None,
        # "Certificate NO": re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){1}\s(\S+)', pdf_text).group(1) if re.search(r'(?:REMA\sRKS|REM\sARKS)(?:\s\S+){3}\s(\S+)', pdf_text) else None,
        "Certificate No": re.search(r"CERT.#\s+(.*?)\s+Issue Date:", pdf_text).group(1) if re.search(r"CERT.#\s+(.*?)\s+Issue Date:", pdf_text) else None,
        "Serial No.": serial_info,  # This now includes the extracted serial info
        "Inspection Date": re.search(r"DATE:\s*(.+)", pdf_text).group(1) if re.search(r"DATE:\s*(.+)", pdf_text) else None,
        "Expire Date": re.search(r"(\S+)\s+Calibrated By", pdf_text).group(1) if re.search(r"(\S+)\s+Calibrated By", pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"DISCLAIMER\s+(.*?)\s+CALIBRATION STATUS", pdf_text, re.DOTALL).group(1).strip() if re.search(r"DISCLAIMER\s+(.*?)\s+CALIBRATION STATUS", pdf_text, re.DOTALL) else None,
        "Customer": re.search(r"CUSTOMER NAME\s*:\s*(.+)", pdf_text).group(1).strip() if re.search(r"CUSTOMER NAME\s*:\s*(.+)", pdf_text) else None
    }

def extract_calibrtion_vernier_caliper(pdf_text):
    customer_match = re.search(r"Customer Name\s+(.*?)\s+ISSUE DATE:", pdf_text)
    customer = customer_match.group(1).strip() if customer_match else None
    if not customer:
        print("Customer data not found in the text.")
    
    return {
        "Work Order No": re.search(r"WO/PO\s+(.*?)\s+CERT\.\#", pdf_text).group(1) if re.search(r"WO/PO\s+(.*?)\s+CERT\.\#", pdf_text) else None,
        "File Name": re.search(r"(.*)\n.*Customer Name", pdf_text).group(1).strip() if re.search(r"(.*)\n.*Customer Name", pdf_text) else None,
        "Type/Description": re.search(r"Equipment Name\s+([^\n]+)", pdf_text).group(1).strip() if re.search(r"Equipment Name\s+([^\n]+)", pdf_text) else None,
        "Location": re.search(r"Location\s+(.*?)\s+WO/PO", pdf_text).group(1) if re.search(r"Location\s+(.*?)\s+WO/PO", pdf_text) else None,
        "Certificate No": re.search(r"CERT\.\#\s*(.*)", pdf_text).group(1) if re.search(r"CERT\.\#\s*(.*)", pdf_text) else None,
        "Serial No.": re.search(r"SERIAL \#\s+(.*?)\s+RANGE", pdf_text).group(1) if re.search(r"SERIAL \#\s+(.*?)\s+RANGE", pdf_text) else None,
        "Inspection Date": re.search(r"DUE DATE.*?(\d{2}-\d{2}-\d{4})", pdf_text).group(1) if re.search(r"DUE DATE.*?(\d{2}-\d{2}-\d{4})", pdf_text) else None,
        "Expire Date": re.search(r"([\S]+)\s+Performed By", pdf_text).group(1) if re.search(r"([\S]+)\s+Performed By", pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"CALIBRATION STATUS\s+(.*?)\s+RECEIVED DATE", pdf_text, re.DOTALL).group(1).strip() if re.search(r"CALIBRATION STATUS\s+(.*?)\s+RECEIVED DATE", pdf_text, re.DOTALL) else None,
        "Customer": customer
    }


def extract__psv_tool(pdf_text):
    # Extract other key information using regex
    return {
        'Work Order No': log_re_function(re.search,r"WO/PO\s(.*?)\sCert.#", pdf_text).group(1) if log_re_function(re.search,r"WO/PO\s(.*?)\sCert.#", pdf_text) else None,
        "File Name": (re.search(r"(.*)\nCustomer", pdf_text).group(1).strip() if re.search(r"(.*)\nCustomer", pdf_text) else "")
        + " "
        + (re.search(r"Equipment Name (.*?) MODEL", pdf_text).group(1).strip() if re.search(r"Equipment Name (.*?) MODEL", pdf_text) else ""),
        "Type/Description": re.search(r"Equipment Name[:\s]+(.*)", pdf_text).group(1).strip() if re.search(r"Equipment Name[:\s]+(.*)", pdf_text) else None,
        "Location": re.search(r"Location\s*:\s*(.*?)\s*WO / PO", pdf_text).group(1) if re.search(r"Location\s*:\s*(.*?)\s*WO / PO", pdf_text) else None,
        "Certificate No": re.search(r"Cert.#\s(.*)", pdf_text).group(1) if re.search(r"Cert.#\s(.*)", pdf_text) else None,
        "Inspection Date": re.search(r"DUE DATE\s*\n(\S+\s\S+)", pdf_text).group(1) if re.search(r"DUE DATE\s*\n(\S+\s\S+)", pdf_text) else None,
        "Expire Date": re.search(r"([^\s]+)\s+Calibrated By:", pdf_text).group(1) if re.search(r"([^\s]+)\s+Calibrated By:", pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"(?<=PSV DE ACTIVATED\n)(.*?)(?=\nPHYSICAL CONDITION OF INSTRUMENT CALIBRATED)", pdf_text,re.S).group(1).strip() if re.search(r"(?<=PSV DE ACTIVATED\n)(.*?)(?=\nPHYSICAL CONDITION OF INSTRUMENT CALIBRATED)", pdf_text,re.S) else None,
        "Customer": re.search(r"Customer Name[:\s]+(.*)", pdf_text).group(1).strip() if re.search(r"Customer Name[:\s]+(.*)", pdf_text) else None
    }

def extract_decade_box_tool(pdf_text):
    # Extract other key information using regex
    return {
        'Work Order No': log_re_function(re.search,r"W/O\s+(.*?)\s+CERT\.#", pdf_text).group(1) if log_re_function(re.search,r"W/O\s+(.*?)\s+CERT\.#", pdf_text) else None,
        "File Name": re.search(r"(.*)\nCustomer", pdf_text).group(1).strip() if re.search(r"(.*)\nCustomer", pdf_text) else None,
        "Type/Description": re.search(r"Equipment Name\s+(.*)", pdf_text).group(1).strip() if re.search(r"Equipment Name\s+(.*)", pdf_text) else None,
        "Location": re.search(r"Location\s+(.*?)\s+Tag #", pdf_text).group(1) if re.search(r"Location\s+(.*?)\s+Tag #", pdf_text) else None,
        "Certificate No": re.search(r"CERT\.#\s+(.*)", pdf_text).group(1) if re.search(r"CERT\.#\s+(.*)", pdf_text) else None,
        "Inspection Date": re.search(r"DUE DATE\s*\n(\S+\s\S+)", pdf_text).group(1) if re.search(r"DUE DATE\s*\n(\S+\s\S+)", pdf_text) else None,
        "Expire Date": re.search(r"([^\s]+)\s+Calibrated By:", pdf_text).group(1) if re.search(r"([^\s]+)\s+Calibrated By:", pdf_text) else None,
        "Fit for use": re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text).group(1) if re.search(r"(.*)\n.*\n.*INSPECTED BY", pdf_text) else None,
        "Fit/Rejected": re.search(r"(.*)\n.*INSPECTED BY", pdf_text).group(1).strip() if re.search(r"(.*)\n.*INSPECTED BY", pdf_text) else None,
        "Remarks": re.search(r"CALIBRATION STATUS\s*(.*?)\s*RECEIVED DATE", pdf_text,re.S).group(1).strip() if re.search(r"CALIBRATION STATUS\s*(.*?)\s*RECEIVED DATE", pdf_text,re.S) else None,
        "Customer": re.search(r"Customer Name\s+(.*)", pdf_text).group(1).strip() if re.search(r"Customer Name\s+(.*)", pdf_text) else None
    }







def identify_and_extract_data(pdf_path):
    inspection_results = []
    none_type_folder = os.path.join(os.path.dirname(pdf_path), "NoneType")
    
    if not os.path.exists(none_type_folder):
        os.makedirs(none_type_folder)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            text = page.extract_text()
            
            if text and len([char for char in text if char.isalpha()]) > 300:
                data = None
                
                # Identify report type and extract data
                if "MAGNETIC PARTICLE INSPECTION REPORT" in text:
                    data = extract_magnetic_particle_data(text)
                elif "ULTRASONIC WALL THICKNESS MEASURMENT RECORD SHEET" in text:
                    data = extract_ultrasonic_wall_thickness_data(text)
                elif "LIFTING GEAR / LIFTING APPLIANCES / LIFTING EQUIPMENT" in text:
                    data = extract_lifting_gear_data(text, page)
                elif "DRILL COLLAR INSPECTION REPORT" in text:
                    data = extract_drill_collar_data(text)
                elif "LOAD TEST" in text:
                    data = extract_load_test_data(text)
                elif "WALL THICKNESS / M.P.I BY AC YOKE INSPECTION REPORT" in text:
                    data = extract_wall_thickness_MPI(text)
                elif "HEAVY-WEIGHT DRILL PIPE INSPECTION REPORT" in text:
                    data = heavy_weight_drill_pipe_data(text)
                elif "DRILL PIPE / PTISCOPE TALLY INSPECTION REPORT" in text:
                    data = extract_drill_pipe_data(text)
                elif "DRILLINGTOOLS (PxP)INSPECTION REPORT" in text:
                    data = extract_drilling_tool_pxp(text)
                elif "MISCELLANEOUS INSPECTION REPORT" in text:
                    data = extract_miscellaneous_inspection(text)
                elif "MISCELLANEOUS TOOLS INSPECTION IN ACCORDANCE WITH DS-1" in text:
                    data = extract_miscellaneous_tools_inspection_ds_1(text)
                elif "CERTIFICATE OF PRESSURE WITNESS TEST" in text:
                    data = extract_pressure_witness_test(text)
                elif "BOROSCOPIC INSPECTION REPORT" in text:
                    data = extract_boroscopic_data(text)
                elif "BOROSCOPIC/ MAGNETIC PARTICLE INSPECTION REPORT" in text:
                    data = extract_boroscopic_mpi_data(text)
                elif "LIQUID PENETRANT INSPECTION REPORT" in text:
                    data = extract_liquid_penetrant_data(text)
                elif "DRILLING TOOLS (PXB) INSPECTION REPORT" in text:
                    data = extract_drill_pipe_pxb(text)
                elif "DRILLING TOOLS (BXB) INSPECTION REPORT" in text:
                    data = extract_drill_pipe_bxb(text)
                elif "String Stabilizer Inspection Report (IR)" in text:
                    data = extract_string_stabilizer_data(text)
                elif "ULTRASONIC THICKNESS MEASUREMENT RECORD SHEET" in text:
                    data = extract_ultrasonic_thickness_measurment(text)
                elif "ULTRASONIC THICKNESS MEASURMENT RECORD SHEET" in text:
                    data = extract_ultrasonic_thickness_measurment(text)
                elif "ULTRASONIC WALL THICKNESS MEASURMENT/MPI RECORD SHEET" in text:
                    data = extract_ultrasonic_thickness_measurment_mpi(text)
                elif "DRILLINGTOOLS INSPECTION REPORT" in text:
                    data = extract_drilling_tool(text)
                elif "CASING/ TUBING INSPECTION TALLY REPORT" in text:
                    data = extract_casing_tubing_inspection(text)
                elif "TUBING PUP JOINT" in text:
                    data = extract_tubing_ppf_pup_inspection(text)
                elif "OD PUPJOINTS TALLY REPORTS" in text:
                    data = extract_od_pupjoint_inspection(text)
                elif "OD TUBING TALLY REPORTS" in text:
                    data = extract_od_tubing_tally_inspection(text)
                elif "CASING TALLY REPORTS" in text:
                    data = extract_casing_talling_inspection(text) 
                elif "PUP JOINT TALLY REPORTS" in text:
                    data = extract_pup_joint_tally_inspection(text)
                elif "X-OVER REPORT" in text:
                    data = extract_x_over_inspection(text)
                elif "CALIBRATION CERTIFICATE OF CRIMPING TOOL" in text:
                    data = extract_crimping_tool_inspection(text)
                elif "EQUIP. NAME Crimping Tool" in text:
                    data = extract_cis_crimping_tool_inspection(text)
                elif "EQUIP. NAME CRIMPING TOOL"in text:
                    data = extract_cis_crimping_tool_inspection(text)
                elif "Equipment Name Pressure Safety Valve"in text:
                    data = extract_cis_psv_inspection(text)
                elif "EQUIPMENT NAME DECADE BOX"in text:
                    data = extract_cis_decade_box_inspection(text)
                elif "Equipment Name Digital Vernier Caliper" in text:
                    data = extract_calibrtion_vernier_caliper(text)
                elif "CALIBRATION CERTIFICATE OF PRESSURE SAFETY VALVE" in text:
                    data = extract__psv_tool(text)
                elif "CALIBRATION CERTIFICATE OF DECADE RESISTANCE BOX" in text:
                    data = extract_decade_box_tool(text)


                if data:
                    try:
                        # Ensure 'File Name' field is not None before processing
                        if data.get('File Name') is not None:
                            data['File Name'] = ''.join([word[0].upper() for word in data['File Name'].split()])
                        
                        # Check if 'Customer' field exists and is not None
                        if data.get('Customer') is not None:
                            data['Customer'] = ''.join([word[0].upper() for word in data['Customer'].split()])
                        else:
                            # Move the file to 'NoneType' folder if 'Customer' is None
                            none_type_path = os.path.join(none_type_folder, os.path.basename(pdf_path))
                            shutil.copy(pdf_path, none_type_path)
                            print(f"File '{pdf_path}' moved to 'NoneType' folder due to missing 'Customer' data.")
                            break  # Exit the loop for this file if 'Customer' is None
                        
                        data['Page Index'] = page_index  # Add page index for later matching
                        inspection_results.append(data)

                    except AttributeError:
                        # If any other AttributeError occurs, handle it here
                        print(f"An unexpected error occurred in file '{pdf_path}' on page {page_index}.")
                        continue  # Skip to the next page

            else:
                print(f"Skipped page {page_index} due to insufficient text content.")
                
    return inspection_results



























# def identify_and_extract_data(pdf_path):
#     inspection_results = []

#     with pdfplumber.open(pdf_path) as pdf:
#         for page_index, page in enumerate(pdf.pages):  # Track page index
#             text = page.extract_text()
            
#             if text:
#                 # Check if the extracted text contains more than 300 letters
#                 if len([char for char in text if char.isalpha()]) > 300:
#                     data = None  # Default to None before identifying the report type
#                     if "MAGNETIC PARTICLE INSPECTION REPORT" in text:
#                         data = extract_magnetic_particle_data(text)
#                     elif "ULTRASONIC WALL THICKNESS MEASURMENT RECORD SHEET" in text:
#                         data = extract_ultrasonic_wall_thickness_data(text)
#                     elif "LIFTING GEAR / LIFTING APPLIANCES / LIFTING EQUIPMENT" in text:
#                         data = extract_lifting_gear_data(text, page)
#                     elif "DRILL COLLAR INSPECTION REPORT" in text:
#                         data = extract_drill_collar_data(text)
#                     elif "LOAD TEST" in text:
#                         data = extract_load_test_data(text)
#                     elif "WALL THICKNESS / M.P.I BY AC YOKE INSPECTION REPORT" in text:
#                         data = extract_wall_thickness_MPI(text)
#                     elif "HEAVY-WEIGHT DRILL PIPE INSPECTION REPORT" in text:
#                         data = heavy_weight_drill_pipe_data(text)
#                     elif "DRILL PIPE / PTISCOPE TALLY INSPECTION REPORT" in text:
#                         data = extract_drill_pipe_data(text)
#                     elif "DRILLINGTOOLS (PxP)INSPECTION REPORT" in text:
#                         data = extract_drilling_tool_pxp(text)
#                     elif "DRILLING TOOLS (BXB) INSPECTION REPORT" in text:
#                         data = extract_drill_pipe_bxb(text)
#                     elif "MISCELLANEOUS INSPECTION REPORT" in text:
#                         data = extract_miscellaneous_inspection(text)
#                     elif "MISCELLANEOUS TOOLS INSPECTION IN ACCORDANCE WITH DS-1" in text:
#                         data = extract_miscellaneous_tools_inspection_ds_1(text)
#                     elif "CERTIFICATE OF PRESSURE WITNESS TEST" in text:
#                         data = extract_pressure_witness_test(text)
#                     elif "BOROSCOPIC INSPECTION REPORT" in text:
#                         data = extract_boroscopic_data(text)
#                     elif "BOROSCOPIC/ MAGNETIC PARTICLE INSPECTION REPORT" in text:
#                         data = extract_boroscopic_mpi_data(text)
#                     elif "LIQUID PENETRANT INSPECTION REPORT" in text:
#                         data = extract_liquid_penetrant_data(text)
#                     elif "DRILLING TOOLS (PXB) INSPECTION REPORT" in text:
#                         data = extract_drill_pipe_pxb(text)
#                     elif "String Stabilizer Inspection Report (IR)" in text:
#                         data = extract_string_stabilizer_data(text)
#                     elif "DYE PENETRANT (DPT)INSPECTION REPORT" in text:
#                         data = extract_dye_penetrant_data(text)
#                     elif "ULTRASONIC THICKNESS MEASURMENT RECORD SHEET" in text:
#                         data = extract_ultrasonic_thickness_measurment(text)
#                     elif "ULTRASONIC WALL THICKNESS MEASURMENT/MPI RECORD SHEET" in text:
#                         data = extract_ultrasonic_thickness_measurment_mpi(text)
#                     elif "DRILLINGTOOLS INSPECTION REPORT" in text:
#                         data = extract_drilling_tool(text)
#                     elif "CASING/ TUBING INSPECTION TALLY REPORT" in text:
#                         data = extract_casing_tubing_inspection(text)
#                     elif "TUBING PUP JOINT" in text:
#                         data = extract_tubing_ppf_pup_inspection(text)
#                     elif "OD PUPJOINTS TALLY REPORTS" in text:
#                         data = extract_od_pupjoint_inspection(text)
#                     elif "OD TUBING TALLY REPORTS" in text:
#                         data = extract_od_tubing_tally_inspection(text)
#                     elif "CASING TALLY REPORTS" in text:
#                         data = extract_casing_talling_inspection(text)
#                     elif "PUP JOINT TALLY REPORTS" in text:
#                         data = extract_pup_joint_tally_inspection(text)
#                     elif "X-OVER REPORT" in text:
#                         data = extract_x_over_inspection(text)
#                     elif "CALIBRATION CERTIFICATE OF CRIMPING TOOL" in text:
#                         data = extract_crimping_tool_inspection(text)


#                     if data:
#                         # Ensure 'File Name' is present
#                         if data.get('File Name') is not None:
#                             # Process and store the extracted data, with the page index included
#                             data['File Name'] = ''.join([word[0].upper() for word in data['File Name'].split()])
#                             data['Customer'] = ''.join([word[0].upper() for word in data['Customer'].split()])
#                             data['Page Index'] = page_index  # Add page index for later matching
#                             inspection_results.append(data)
#                 else:
#                     # Skip if the text contains fewer than 300 letters
#                     print(f"Skipped page with fewer than 300 letters.")
#             else:
#                 data = None

#     return inspection_results

# def save_pdf_pages(pdf_path, output_folder):
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)
#     inspection_results = identify_and_extract_data(pdf_path)  # Extract once

#     with open(pdf_path, 'rb') as file:
#         reader = PdfReader(file)
#         num_pages = len(reader.pages)

#         for i, result in enumerate(inspection_results):
#             if not all(key in result for key in ['Work Order No', 'File Name', 'Type/Description', 'Location', 'Certificate No', 'Customer']):
#                 continue
            
#             # Process Type/Description
#             type_description = result.get('Type/Description', 'N/A')
#             if type_description is not None and isinstance(type_description, str):
#                 type_description = type_description[:50] if len(type_description) > 50 else type_description
#             else:
#                 type_description = 'N/A'
            
#             # Process Customer
#             customer = result.get('Customer', 'N/A')
#             if customer is not None and isinstance(customer, str):
#                 customer_words = customer.split()
#                 customer = " ".join(customer_words[:5])  # Limit to the first three words
#             else:
#                 customer = 'N/A'

#             # Debugging output
#             # print(f"Original Type/Description: {result.get('Type/Description', 'N/A')}")
#             # print(f"Processed Type/Description: {type_description}")
#             # print(f"Original Customer: {result.get('Customer', 'N/A')}")
#             # print(f"Processed Customer: {customer}")

#             filename = f"{result['Work Order No']}_{result['File Name']}_{type_description}_{result['Location']}_{result['Certificate No']}_{result['Expire Date']}_{customer}.pdf"
#             cleaned_filename = clean_filename(filename)

#             writer = PdfWriter()
#             writer.add_page(reader.pages[i])

#             # Create customer folder
#             customer_folder = os.path.join(output_folder, clean_filename(customer))
#             if not os.path.exists(customer_folder):
#                 os.makedirs(customer_folder)

#             output_path = os.path.join(customer_folder, cleaned_filename)
#             with open(output_path, 'wb') as output_file:
#                 writer.write(output_file)

#             # Insert data to DB if not already present
#             insert_data_to_db(result, output_path)


def save_pdf_pages(pdf_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    inspection_results = identify_and_extract_data(pdf_path)  # Extract data along with page indices

    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)

        for result in inspection_results:
            # Verify required keys are in result data
            if not all(key in result for key in ['Work Order No', 'File Name', 'Type/Description', 'Location', 'Certificate No', 'Customer', 'Page Index']):
                continue

            # Use 'Page Index' to correctly retrieve the page from reader
            page_index = result['Page Index']
            writer = PdfWriter()
            writer.add_page(reader.pages[page_index])  # Correctly match page using 'Page Index'

            # Process Type/Description
            type_description = result.get('Type/Description', 'N/A')
            type_description = type_description[:50] if isinstance(type_description, str) and len(type_description) > 50 else type_description
            
            # Process Customer
            customer = result.get('Customer', 'N/A')
            customer = " ".join(customer.split()[:5]) if isinstance(customer, str) else 'N/A'

            # Generate a clean filename based on data fields
            filename = f"{result['Work Order No']}_{result['File Name']}_{type_description}_{result['Location']}_{result['Certificate No']}_{result.get('Expire Date', 'N/A')}_{customer}.pdf"
            cleaned_filename = clean_filename(filename)

            # Create customer-specific folder if it does not exist
            customer_folder = os.path.join(output_folder, clean_filename(customer))
            if not os.path.exists(customer_folder):
                os.makedirs(customer_folder)

            # Write PDF file to output path
            output_path = os.path.join(customer_folder, cleaned_filename)
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            # Insert data into the database if not already present
            insert_data_to_db(result, output_path)






def clean_filename(filename):
    # Clean the filename by removing invalid characters and limiting the length
    cleaned_filename = re.sub(r'[\\/:"*?<>|,]+', '', filename)
    cleaned_filename = cleaned_filename.replace('\n', ' ')
    max_length = 255  # Maximum filename length (common limit)
    if len(cleaned_filename) > max_length:
        cleaned_filename = cleaned_filename[:max_length]
    return cleaned_filename

def generate_pdf_link(pdf_blob, filename):
    if pdf_blob is None:
        return '<span>No PDF available</span>'
    pdf_base64 = base64.b64encode(pdf_blob).decode('utf-8')
    return f'<a href="data:application/pdf;base64,{pdf_base64}" download="{filename}">Download PDF</a>'

def fetch_data_from_db(search_by=None, search_value=None, after_date=None, show_all=False):
    conn = sqlite3.connect('inspections.db')
    if show_all:
        query = """
        SELECT * FROM inspections
        """
        params = ()
    elif search_by == 'expire_date' and after_date:
        query = f"""
        SELECT * FROM inspections
        WHERE {search_by} > ?
        """
        params = (after_date,)
    else:
        query = f"""
        SELECT * FROM inspections
        WHERE {search_by} LIKE ?
        """
        params = (f'%{search_value}%',)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def create_download_link(file_data, file_name):
    b64 = base64.b64encode(file_data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">Download PDF</a>'
    return href



def display():
    st.title("Inspection Report Portal")
    st.write("Search for data by various criteria or show all records.")

    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'page_num' not in st.session_state:
        st.session_state.page_num = 0

    search_options = ['work_order_no', 'file_name', 'part_no', 'certificate_no', 'serial_no','location', 'expire_date', 'Show All Data', 'customer']
    search_by = st.selectbox('Search by', search_options)
    
    show_all = False

    if search_by == 'expire_date':
        after_date = st.date_input("Select a date to find records expiring after", value=datetime.date.today())
        search_value = None
    elif search_by == 'Show All Data':
        after_date = None
        search_value = None
        show_all = True
    else:
        after_date = None
        search_value = st.text_input(f"Enter {search_by.replace('_', ' ').title()}")

    if st.button('Search'):
        with st.spinner('Fetching data...'):
            data = fetch_data_from_db(search_by, search_value, after_date, show_all=show_all)
            if not data.empty:
                data['Download'] = data.apply(
                    lambda row: create_download_link(
                        row['pdf_blob'],
                        f"{row['work_order_no']}_{row['file_name']}_{row['part_no']}_{row['certificate_no']}_{row['serial_no']}_{row['expire_date']}_{row['customer']}.pdf"
                    ),
                    axis=1
                )
                data.drop(columns=['pdf_blob'], inplace=True)
                st.session_state.data = data
                st.session_state.page_num = 0
            else:
                st.session_state.data = None
                st.warning("No matching records found.")

    if st.session_state.data is not None:
        data = st.session_state.data
        page_size = 100
        total_records = len(data)
        total_pages = (total_records - 1) // page_size + 1

        page_num = st.session_state.page_num
        if page_num < 0:
            page_num = 0
        elif page_num >= total_pages:
            page_num = total_pages - 1
        st.session_state.page_num = page_num

        start_idx = page_num * page_size
        end_idx = start_idx + page_size
        paginated_data = data.iloc[start_idx:end_idx]

        st.write(f"Showing records {start_idx + 1} to {min(end_idx, total_records)} of {total_records}")
        st.write(paginated_data.to_html(escape=False, index=False), unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button('Previous') and page_num > 0:
                st.session_state.page_num -= 1
        with col2:
            st.write(f"Page {page_num + 1} of {total_pages}")
        with col3:
            if st.button('Next') and page_num < total_pages - 1:
                st.session_state.page_num += 1



def main_admin():
    setup_database()

    st.sidebar.title("Options")
    
    # Include the display function here
    st.sidebar.header("Search Inspection Data")
    display()


    st.title("PDF Inspection Report Management")

    uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)  # Allow multiple files

    if uploaded_files:  # Check if any files are uploaded
        st.sidebar.header("Processing PDFs")
        output_folder = st.sidebar.text_input("Output Folder Name", "output_pages")

        for uploaded_file in uploaded_files:  # Process each uploaded file
            pdf_path = os.path.join(output_folder, uploaded_file.name)

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)  # Ensure the output folder exists

            with open(pdf_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())  # Save the uploaded file

            st.sidebar.success(f"PDF {uploaded_file.name} successfully uploaded and saved.")

            save_pdf_pages(pdf_path, output_folder)  # Process the PDF file

        if st.sidebar.button("Show Extracted Data"):
            df = display_data_from_db()

            if 'pdf_blob' in df.columns:
                df['PDF Link'] = df.apply(lambda row: generate_pdf_link(row['pdf_blob'], f"{row['work_order_no']}_{row['file_name']}.pdf"), axis=1)
                df = df.drop(columns=['pdf_blob'])

            df.head(200)
            st.write(df.to_html(escape=False), unsafe_allow_html=True)

if __name__ == "__main__":
    main_admin()