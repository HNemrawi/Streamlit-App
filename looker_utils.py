import looker_sdk
from looker_sdk import api_settings
import streamlit as st


class MyApiSettings(api_settings.ApiSettings):
    def __init__(self, *args, **kw_args):
        self.my_var = kw_args.pop("my_var")
        super().__init__(*args, **kw_args)

    def read_config(self) -> api_settings.SettingsConfig:
        config = super().read_config()
        # Load the Looker SDK configuration from st.secrets
        config["base_url"] = st.secrets["Looker"]["base_url"]
        config["client_id"] = st.secrets["Looker"]["client_id"]
        config["client_secret"] = st.secrets["Looker"]["client_secret"]
        config["verify_ssl"] = st.secrets["Looker"]["verify_ssl"]
        return config


# Initialize the Looker SDK with the custom configuration
sdk = looker_sdk.init40(config_settings=MyApiSettings(my_var="foo"))
