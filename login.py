# import logging
# import os
# import sys
# import warnings
# import streamlit as st


# warnings.filterwarnings('ignore')
# logging.getLogger('streamlit').setLevel(logging.ERROR)


# # Dummy credentials
# USERS = {
#     "sp": {"password": "123", "role": "client"},
#     "admin": {"password": "123", "role": "admin"},
#     "exalo" : {"password": "123", "role": "client_2"},
#     "uepl" : {"password": "123", "role": "client_3"},
#     "hilong" : {"password": "123", "role": "client_4"},
#     "anton" : {"password": "123", "role": "client_5"},
#     "wot" : {"password": "123", "role": "client_6"},
#     "ppl" : {"password": "123", "role": "client_7"},
#     "mcpl" :{"password": "123", "role":"client_8"},
#     "ogdcl" :{"password": "123", "role":"client_9"},
#     "dowell" :{"password": "123", "role":"client_10"},
#     "slb" :{"password": "123", "role":"client_11"},
#     "slb_seaco" :{"password": "123", "role":"client_12"},
#     "slb_sealand" :{"password": "123", "role":"client_13"},
#     "ps" :{"password": "123", "role":"client_14"},
#     "zia" :{"password": "123", "role":"client_15"},
#     "iws" :{"password": "123", "role":"client_16"},
    

# }

# def login():
#     st.title("Login")
#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")

#     if st.button("Login"):
#         if username in USERS and USERS[username]["password"] == password:
#             st.session_state.user = username
#             st.session_state.role = USERS[username]["role"]
#             st.session_state.logged_in = True
#             st.experimental_set_query_params(page="home")
#         else:
#             st.error("Invalid username or password")

import logging
import warnings
import streamlit as st
from PIL import Image  # To handle image loading


# warnings.filterwarnings("ignore", message="Please replace st.experimental_get_query_params with st.query_params.st.experimental_get_query_params will be removed after 2024-04-11.Refer to our docs page for more information.")

# Ensure this is at the very top
# st.set_page_config(page_title="PTIS Portal Login", layout="centered")

# warnings.filterwarnings('ignore')
# logging.getLogger('streamlit').setLevel(logging.ERROR)

USERS = {
    "sp": {"password": "123", "role": "client"},
    "admin": {"password": "123", "role": "admin"},
    "exalo" : {"password": "123", "role": "client_2"},
    "uepl" : {"password": "123", "role": "client_3"},
    "hilong" : {"password": "123", "role": "client_4"},
    "anton" : {"password": "123", "role": "client_5"},
    "wot" : {"password": "123", "role": "client_6"},
    "ppl" : {"password": "123", "role": "client_7"},
    "mcpl" :{"password": "123", "role":"client_8"},
    "ogdcl" :{"password": "123", "role":"client_9"},
    "dowell" :{"password": "123", "role":"client_10"},
    "slb" :{"password": "123", "role":"client_11"},
    "slb_seaco" :{"password": "123", "role":"client_12"},
    "slb_sealand" :{"password": "123", "role":"client_13"},
    "ps" :{"password": "123", "role":"client_14"},
    "zia" :{"password": "123", "role":"client_15"},
    "iws" :{"password": "123", "role":"client_16"},
    

}

def login():
    # Create a layout with two columns
    col1, col2 = st.columns([2, 1])  # Left column (2x width) and right column (1x width)

    with col1:  # Left side: Login form
        st.markdown("## Welcome to Portal")
        st.markdown("### Please log in to continue")
        
        # Input fields with labels
        username = st.text_input("Username", placeholder="Enter your username", key="username")
        password = st.text_input("Password", placeholder="Enter your password", type="password", key="password")
        
        # Button for login
        if st.button("Login", key="login"):
            if not username or not password:
                st.error("Both username and password are required.")
            elif username in USERS and USERS[username]["password"] == password:
                st.session_state.user = username
                st.session_state.role = USERS[username]["role"]
                st.session_state.logged_in = True
                st.success(f"Welcome, {username}! Login successful.")
                st.experimental_set_query_params(page="home")
            else:
                st.error("Invalid username or password. Please try again.")
        
        st.markdown("---")
        st.caption("PTIS Portal © 2024")

    with col2:  # Right side: Logo
        logo_path = "PTIS Logo.jpg"  # Ensure the logo file is in the same directory
        logo = Image.open(logo_path)
        st.image(logo, caption="", use_container_width=True)

if __name__ == "__main__":
    login()