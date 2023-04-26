from typing import Sequence
import numpy as np
import pandas as pd
from looker_sdk import sdk
import base64


def get_indices_by_folder(sdk, all_items, cur_folder_id, cur_agency_folder_id):
    """
    Get the unique indices of items in target folders (cur_folder_id and cur_agency_folder_id).
    """
    target_folders = {str(cur_folder_id), str(cur_agency_folder_id)}
    indices = [
        idx for idx, item in enumerate(all_items)
        if item.folder.parent_id in target_folders or item.folder.id in target_folders
    ]
    return np.unique(indices)


def get_titles(items, indices):
    """
    Get the titles of items at the specified indices.
    """
    return [item.title for idx, item in enumerate(items) if idx in indices]


def get_dashboards_by_id(sdk, dash_id: int):
    """Get dashboards with matching id"""
    dashboards = sdk.search_dashboards(id=dash_id)
    if not dashboards:
        return None
    return dashboards[0]


def extract_dashboard_info(dashboard, targeted_strings):
    """
    Extract dashboard information and tiles containing targeted strings.
    """
    dashboard_info = {
        'ID': dashboard.id,
        'Title': dashboard.title,
        'Folder Name': dashboard.folder.name,
        'Tiles': [tile.title for tile in dashboard.dashboard_elements if targeted_strings in str(tile)]
    }
    return dashboard_info


def get_query_info(sdk, query_id, targeted_strings):
    """
    Get query information containing targeted strings.
    """
    try:
        query = sdk.query(query_id=query_id)
        qf_id = str(query).find(targeted_strings)
        if qf_id > 0:
            return query.id, str(query)[(qf_id - 10):(qf_id + 50)]
    except Exception as e:
        print(f"Error processing query {query_id}: {e}")
    return None


def process_dashboard(sdk, dashboard, targeted_strings):
    """
    Process dashboard elements containing merge queries with targeted strings.
    """
    dashboard_info = {}
    mf_id = str(dashboard).find("merge_result_id='")
    if mf_id >= 0:
        for d_elems in dashboard.dashboard_elements:
            if d_elems.merge_result_id is not None:
                cur_mq = sdk.merge_query(merge_query_id=d_elems.merge_result_id)
                cur_mq_list = {}
                for cur_sq in cur_mq.source_queries:
                    query_info = get_query_info(sdk, cur_sq.query_id, targeted_strings)
                    if query_info:
                        cur_mq_list[query_info[0]] = query_info[1]
                if cur_mq_list:
                    cur_list = {'elem_title': d_elems.title, d_elems.merge_result_id: cur_mq_list}
                    if cur_list:
                        dashboard_info.update({'title': dashboard.title, 'dashboard_folder_id': dashboard.folder_id,
                                               d_elems.id: cur_list})
    return dashboard_info


def extract_look_info(look, targeted_strings):
    """
    Extract look information containing targeted strings.
    """
    f_id = str(look).find(targeted_strings)
    if f_id >= 0:
        look_info = {
            'ID': look.id,
            'title': look.title,
            'look_folder_name': look.folder.name,
            'look_folder_id': look.folder_id,
        }
        return look_info
    return None


def create_download_link(data, filename, mime):
    b64 = base64.b64encode(data.encode()).decode()  # some strings <-> bytes conversions necessary here
    return f'<a href="data:{mime};base64,{b64}" download="{filename}">Download {filename}</a>'


def process_input_string(input_string, sdk, cur_folder_id, cur_agency_folder_id, all_dashboards, all_looks):
    # Perform data processing and return the processed data
    pass


def display_dataframes(found_dash, grouped_dash, found_look):
    # Display the dataframes and download links
    pass
