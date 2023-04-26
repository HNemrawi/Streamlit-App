import streamlit as st

def check_password(password):
    if password == st.secrets["password"]["auth_password"]:
        return True
    return False

def show_login_page():
    st.title("Authentication")
    st.write("Please enter the password to access the app:")

    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_password(password):
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Incorrect password. Please try again.")
