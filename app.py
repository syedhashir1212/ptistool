import logging
import warnings
import streamlit as st
from login import login




logging.getLogger('streamlit').setLevel(logging.ERROR)


def logout():
    # Clear session state and redirect to login
    st.session_state.clear()
    st.experimental_set_query_params(page="login")

def main():
    # st.title("PTIS")

    # Initialize session state if not set
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # Get the current page from query parameters
    query_params = st.experimental_get_query_params()
    page = query_params.get("page", ["login"])[0]

    if page == "login":
        if not st.session_state.logged_in:
            login()
        else:
            st.experimental_set_query_params(page="home")
    elif page == "home":
        if st.session_state.logged_in:
            st.sidebar.button("Logout", on_click=logout)  # Logout button in sidebar
            role = st.session_state.role
            if role == "client":
                import sprint_page
                sprint_page.display()
            elif role == "admin":
                import admin_page
                admin_page.main_admin()
            elif role == "client_2":
                import exalo_page
                exalo_page.display()
            elif role == "client_3":
                import uepl_page
                uepl_page.display()
            elif role == "client_4":
                import hilong_page
                hilong_page.display()
            elif role == "client_5":
                import anton_page
                anton_page.display()
            elif role == "client_6":
                import weatherford_page
                weatherford_page.display()
            elif role == "client_7":
                import ppl_page
                ppl_page.display()
            elif role == "client_8":
                import mcpl_page
                mcpl_page.display()
            elif role == "client_9":
                import ogdcl_page
                ogdcl_page.display()
            elif role == "client_10":
                import dowell_page
                dowell_page.display()
            elif role == "client_11":
                import slb_page
                slb_page.display()
            elif role == "client_12":
                import slb_seaco_page
                slb_seaco_page.display()
            elif role == "client_13":
                import slb_sealand
                slb_sealand.display()
            elif role == "client_14":
                import ps_page
                ps_page.display()
            elif role == "client_15":
                import zia_page
                zia_page.display()
            elif role == "client_16":
                import iws_page
                iws_page.display()
            else:
                st.write("Role not recognized")
        else:
            st.experimental_set_query_params(page="login")
    else:
        st.experimental_set_query_params(page="login")

if __name__ == "__main__":
    main()
