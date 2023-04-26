import logging
import streamlit as st
from auth import show_login_page
from helpers import *
from looker_utils import sdk

# Set page configuration
st.set_page_config(page_title="Dashboard Search", page_icon=":mag_right:", layout="wide")

# Set logging configuration
logging.basicConfig(
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO)

MAX_RECENT_INPUTS = 5


# Function to create a download link
def create_download_link(data, filename, mime):
    b64 = base64.b64encode(data.encode()).decode()
    return f'<a href="data:{mime};base64,{b64}" download="{filename}">Download {filename}</a>'


# Functions to cache data
@st.cache_data(ttl=None)
def get_all_dashboards_cached():
    return sdk.all_dashboards()


@st.cache_data(ttl=None)
def get_all_looks_cached():
    return sdk.all_looks()


# Functions to manage session state
def get_session_state():
    session_state = st.session_state.get('recent_inputs', [])
    return session_state


def set_session_state(region_inputs):
    st.session_state['recent_inputs'] = region_inputs


# Main function
def main():
    # Sidebar content
    st.sidebar.markdown(
        """
        <div style="font-style: italic; color: #808080; text-align: left;">
        <a href="https://icalliances.org/" target="_blank"><img src="https://images.squarespace-cdn.com/content/v1/54ca7491e4b000c4d5583d9c/eb7da336-e61c-4e0b-bbb5-1a7b9d45bff6/Dash+Logo+2.png?format=750w" width="250"></a>
        </div>
        """,
        unsafe_allow_html=True)
    st.sidebar.title("Dashboards/Looks Search")

    # Radio button for selecting implementation
    tabs = ["New England", "Wisconsin"]
    region = st.sidebar.radio("Select Implementation", tabs)

    # Set folder IDs based on region
    if region == "New England":
        cur_folder_id = 11429
        cur_agency_folder_id = 11430
    elif region == "Wisconsin":
        cur_folder_id = 8519
        cur_agency_folder_id = 8520

    stop_button = st.sidebar.button("Stop")

    # Display recent inputs
    st.sidebar.subheader("Recent Inputs")
    recent_inputs = get_session_state()
    region_inputs = [input_string for input_string, input_region in recent_inputs if input_region == region]
    st.sidebar.write(", ".join(region_inputs))

    # Input field for search string
    input_string = st.text_input("Enter a string to search for:", "referrals.status")

    input_changed = False
    if input_string and st.button("Search"):
        input_changed = True
        recent_inputs.append((input_string, region))
        if len(recent_inputs) > MAX_RECENT_INPUTS:
            recent_inputs.pop(0)

        set_session_state(recent_inputs)
        st.sidebar.write(f"{input_string} ({region})")

        # Process search request
        with st.spinner("Processing..."):
            progress_bar = st.progress(0)
            total_tasks = 6
            completed_tasks = 0

            if not stop_button:
                # Get all dashboards
                all_dashboards = get_all_dashboards_cached()
                completed_tasks += 1
                progress_bar.progress(completed_tasks / total_tasks)

            if not stop_button:
                all_dash_ind = get_indices_by_folder(sdk, all_dashboards, cur_folder_id, cur_agency_folder_id)
                completed_tasks += 1
                progress_bar.progress(completed_tasks / total_tasks)
                all_dash_titles = get_titles(all_dashboards, all_dash_ind)

            # Loop through all possible Dashboards
            if not stop_button:
                found_dash_list = []
                for cur_dash in all_dash_ind:
                    try:
                        cur_dashboard = get_dashboards_by_id(sdk, all_dashboards[cur_dash].id)
                        dashboard_str = str(cur_dashboard)

                        if any(input_string in s for s in dashboard_str.split()):
                            dashboard_info = extract_dashboard_info(cur_dashboard, input_string)
                            found_dash_list.append(dashboard_info)
                    except Exception as e:
                        logging.error(f"Error processing dashboard {cur_dash}: {e}")
                        st.error(f"Error processing dashboard {cur_dash}: {e}")

                found_dash = pd.DataFrame(found_dash_list).reset_index(drop=True)
                completed_tasks += 1
                progress_bar.progress(completed_tasks / total_tasks)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.subheader('List of Dashboards without merged query')
                dashboards = found_dash.to_csv(index=False)
                st.markdown(create_download_link(dashboards, 'dashs.csv', 'text/csv'), unsafe_allow_html=True)
                st.dataframe(found_dash)

            # Loop through all possible Dashboards with merged query
            if not stop_button:
                found_dash_dict = ({})
                data = []
                for cur_dash in all_dash_ind:
                    try:
                        cur_dashboard = get_dashboards_by_id(sdk, all_dashboards[cur_dash].id)
                        dashboard_info = process_dashboard(sdk, cur_dashboard, input_string)
                        if dashboard_info:
                            found_dash_dict[str(cur_dashboard.id)] = dashboard_info
                            data.append(dashboard_info)
                    except Exception as e:
                        st.error(f"Error processing dashboard (merged) {cur_dash}: {e}")
                        logging.error(f"Error processing dashboard (merged) {cur_dash}: {e}")

                grouped_dash = (
                    pd.DataFrame([(k, v.get('title', ''), v.get('dashboard_folder_id', ''), v2.get('elem_title', ''))
                                  for k, v in found_dash_dict.items()
                                  for k2, v2 in v.items()
                                  if k2 not in ('title', 'dashboard_folder_id')
                                  for mq_key, mq_value in v2.get(list(v2.keys())[1], {}).items()],
                                 columns=['Dashboard ID', 'Title', 'Folder ID', 'Element Title'])
                    .groupby(['Dashboard ID', 'Title', 'Folder ID'])['Element Title']
                    .agg(', '.join)
                    .reset_index())
                completed_tasks += 1
                progress_bar.progress(completed_tasks / total_tasks)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.subheader('List of Dashboards with merged query')
                dashboards_merged = grouped_dash.to_csv(index=False)
                st.markdown(create_download_link(dashboards_merged, 'dashs-merged.csv', 'text/csv'),
                            unsafe_allow_html=True)
                st.dataframe(grouped_dash)

            if not stop_button:
                all_looks = get_all_looks_cached()
                all_look_ind = get_indices_by_folder(sdk, all_looks, cur_folder_id, cur_agency_folder_id)
                all_look_titles = get_titles(all_looks, all_look_ind)

                # Loop through all possible Dashboards
                if not stop_button:
                    found_look_list = []
                    for cur_look in all_look_ind:
                        try:
                            cur_look = sdk.look(look_id=all_looks[cur_look].id)
                            look_info = extract_look_info(cur_look, input_string)
                            if look_info:
                                found_look_list.append(look_info)
                        except Exception as e:
                            st.error(f"Error processing look {cur_look}: {e}")
                            logging.error(f"Error processing look {cur_look}: {e}")

                found_look = pd.DataFrame(found_look_list).reset_index(drop=True)
                completed_tasks += 1
                progress_bar.progress(completed_tasks / total_tasks)
                st.markdown("<hr>", unsafe_allow_html=True)
                st.subheader('List of Looks')
                looks = found_look.to_csv(index=False)
                st.markdown(create_download_link(looks, 'looks.csv', 'text/csv'), unsafe_allow_html=True)
                st.dataframe(found_look)

            @st.cache_data
            def get_dataframes():
                return {"found_dash": found_dash, "grouped_dash": grouped_dash, "found_look": found_look}

            if input_changed:
                get_dataframes()

            found_dash = get_dataframes()["found_dash"]
            grouped_dash = get_dataframes()["grouped_dash"]
            found_look = get_dataframes()["found_look"]
            completed_tasks += 1
            progress_bar.progress(completed_tasks / total_tasks)
            st.snow()

        st.markdown(
            """
           <div style="font-style: italic; color: #808080; text-align: center;"><a href="https://icalliances.org/" target="_blank"><img src="https://images.squarespace-cdn.com/content/v1/54ca7491e4b000c4d5583d9c/eb7da336-e61c-4e0b-bbb5-1a7b9d45bff6/Dash+Logo+2.png?format=750w" width="99"></a>DASH™ is a trademark of Institute for Community Alliances.</div>
            <div style="font-style: italic; color: #808080; text-align: center;"><a href="https://icalliances.org/" target="_blank"><img src="https://images.squarespace-cdn.com/content/v1/54ca7491e4b000c4d5583d9c/1475614371395-KFTYP42QLJN0VD5V9VB1/ICA+Official+Logo+PNG+%28transparent%29.png?format=1500w" width="99"></a>© 2023 Institute for Community Alliances (ICA). All rights reserved.</div>
            """,
            unsafe_allow_html=True
        )


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    show_login_page()
else:
    if __name__ == '__main__':
        main()
