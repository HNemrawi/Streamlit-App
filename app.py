import streamlit as st
from auth import show_login_page
from helpers import *
from looker_utils import sdk

# Set page configuration
st.set_page_config(page_title="Dashboard Search", page_icon=":mag_right:", layout="wide")

# Functions to cache data
@st.cache_data
def get_all_dashboards_cached():
    return sdk.all_dashboards()


@st.cache_data
def get_all_looks_cached():
    return sdk.all_looks()


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

    region_options = {
        "New England": (11429, 11430),
        "GreatLakes": (8519, 8520)
    }

    selected_regions = st.sidebar.multiselect("Select Implementations", list(region_options.keys()), default=list(region_options.keys()))

    # Aggregating folder IDs from selected regions
    cur_folder_id = []
    cur_agency_folder_id = []
    for region in selected_regions:
        cur_folder_id.append(region_options[region][0])
        cur_agency_folder_id.append(region_options[region][1])

    stop_button = st.sidebar.button("Stop")

    input_string = st.text_input("Enter string(s) to search for (separate multiple with commas):", "chronic_5, education_child_school, education_child_type, education_degree, education_enrolled, education_level, employment_hours, employment_tenure, employment_status, health_mental_documented, health_mental_services, health_substance_abuse_services, housing_status, rhy_family_reunification, soar_staff, zipcode_quality")
    targeted_strings = [s.strip() for s in input_string.split(',')]
    st.sidebar.write ('List of Strings:')
    st.sidebar.write (targeted_strings)
    if targeted_strings and st.button("Search"):

        # Process search request
        with st.spinner("Processing..."):
            progress_bar = st.progress(0)
            total_tasks = 6
            completed_tasks = 0

            if not stop_button:
                # Get all dashboards
                all_dashboards = get_all_dashboards_cached()


            if not stop_button:
                all_dash_ind = get_indices_by_folder(sdk, all_dashboards, cur_folder_id, cur_agency_folder_id)
                completed_tasks += 2
                progress_bar.progress(completed_tasks / total_tasks)

            # Loop through all possible Dashboards
            if not stop_button:
                found_dash_dict = {}
                processed_dashboards = set()  # To prevent duplicate dashboard processing
                for cur_dash in all_dash_ind:
                    try:
                        cur_dashboard = get_dashboards_by_id(sdk, all_dashboards[cur_dash].id)
                        dashboard_str = str(cur_dashboard)
                        if cur_dashboard.id not in processed_dashboards and any(ts in dashboard_str for ts in targeted_strings):
                            dashboard_info = process_dashboards(sdk,cur_dashboard, targeted_strings)
                            found_dash_dict[str(cur_dashboard.id)] = dashboard_info
                            processed_dashboards.add(cur_dashboard.id)

                        if cur_dashboard.id not in processed_dashboards and any(ts in dashboard_str for ts in targeted_strings):
                            dashboard_info = process_dashboards(sdk,cur_dashboard, targeted_strings)
                    except Exception as e:
                        st.error(f"Error processing dashboard {cur_dash}: {e}")

                found_dash = pd.DataFrame(found_dash_dict).T.reset_index(drop=True)
                found_dash.dropna(inplace=True)
                completed_tasks += 1
                progress_bar.progress(completed_tasks / total_tasks)
                st.title('Dashboards')
                st.dataframe(found_dash)

            if not stop_button:
                all_looks = get_all_looks_cached()
                all_look_ind = get_indices_by_folder(sdk, all_looks, cur_folder_id, cur_agency_folder_id)
                completed_tasks += 1
                progress_bar.progress(completed_tasks / total_tasks)

                # Loop through all possible looks
                if not stop_button:
                    found_look_dict = {}
                    for cur_look_index in all_look_ind:
                        try:
                            cur_look = sdk.look(look_id=all_looks[cur_look_index].id)
                            look_info = process_looks(cur_look, targeted_strings)
                            if look_info:
                                found_look_dict[str(cur_look.id)] = look_info
                        except Exception as e:
                            st.error(f"Error processing look {cur_look}: {e}")

                found_look = pd.DataFrame(found_look_dict).T.reset_index(drop=True)
                completed_tasks += 1
                progress_bar.progress(completed_tasks / total_tasks)
                st.title('Looks')
                st.dataframe(found_look)

            @st.cache_data
            def get_dataframes():
                # Always retrieve and cache the latest data frames
                return {"found_dash": found_dash, "grouped_dash": grouped_dash, "found_look": found_look}

            # Get the updated data frames from the function
            found_dash = get_dataframes()["found_dash"]
            grouped_dash = get_dataframes()["grouped_dash"]
            found_look = get_dataframes()["found_look"]

            # Update the completion and progress
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