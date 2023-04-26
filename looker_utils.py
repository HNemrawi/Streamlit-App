import looker_sdk
from looker_sdk import models, error
from looker_sdk.rtl import transport
import streamlit as st
# Load the Looker SDK configuration from st.secrets

base_url = st.secrets["Looker"]["base_url"]
client_id = st.secrets["Looker"]["client_id"]
client_secret = st.secrets["Looker"]["client_secret"]
verify_ssl = st.secrets["Looker"]["verify_ssl"]

# Initialize the Looker SDK with the configuration
sdk = looker_sdk.init40()



