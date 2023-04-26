import looker_sdk
from looker_sdk import models, error
from looker_sdk.rtl import transport
import streamlit as st
# Load the Looker SDK configuration from st.secrets

base_url = "https://looker.clarityhs.com:19999"
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
verify_ssl = True

# Initialize the Looker SDK with the configuration
sdk = looker_sdk.init40()

