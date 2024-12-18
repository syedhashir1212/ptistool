import warnings
import streamlit as st
import sqlite3
import pandas as pd
import base64
import datetime

warnings.filterwarnings('ignore')

def fetch_data_from_db(search_by=None, search_value=None, after_date=None, show_all=False):
    conn = sqlite3.connect('inspections.db')
    
    if show_all:
        query = """
        SELECT * FROM inspections
        WHERE Customer IN ('ED&PB', 'EDSE3', 'EDSPB')
        """
        params = ()
    elif search_by == 'expire_date' and after_date:
        query = f"""
        SELECT * FROM inspections
        WHERE {search_by} > ?
        AND Customer IN ('ED&PB', 'EDSE3', 'EDSPB')
        
        """
        params = (after_date,)
    else:
        query = f"""
        SELECT * FROM inspections
        WHERE {search_by} LIKE ?
        AND Customer IN ('ED&PB', 'EDSE3', 'EDSPB')
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
    st.title("EXALO PORTAL")
    st.write("Search for data by various criteria or show all records.")

    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'page_num' not in st.session_state:
        st.session_state.page_num = 0

    search_options = ['work_order_no', 'file_name', 'part_no', 'certificate_no', 'serial_no','location', 'expire_date', 'Show All Data']
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


if __name__ == "__main__":
    display()
