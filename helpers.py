import numpy as np
import pandas as pd
from looker_sdk import sdk
import streamlit as st

def get_dashboards_by_id(sdk, dash_id: int):
    dashboards = sdk.search_dashboards(id=dash_id)
    if not dashboards:
        print(f'Dashboard "{dash_id}" not found')
        return None
    return dashboards[0]

def get_titles(items, indices):
    """
    Get the titles of items at the specified indices.
    """
    return [item.title for idx, item in enumerate(items) if idx in indices]

def process_looks(look, targeted_strings):
    """
    Extract look information containing targeted strings.
    Each targeted string is checked and those found are noted.
    """
    look_str = str(look)
    found_strings = [ts for ts in targeted_strings if ts in look_str]
    if found_strings:  # Only proceed if there are any found strings
        look_info = {
            'ID': look.id,
            'title': look.title,
            'look_folder_name': look.folder.name,
            'look_folder_id': look.folder_id,
            'found_strings': found_strings  # Store the list of found strings
        }
        return look_info
    return None

def get_indices_by_folder(sdk, all_items, cur_folder_ids, cur_agency_folder_ids):
    """
    Get indices of items whose folder ID match any of the current folder IDs or agency folder IDs
    provided for one or more regions.
    
    Parameters:
        sdk (object): An instance of the SDK to interact with.
        all_items (list): List of all items to filter.
        cur_folder_ids (list): List of current folder IDs across selected regions.
        cur_agency_folder_ids (list): List of current agency folder IDs across selected regions.

    Returns:
        np.array: Unique indices of items that match the folder criteria.
    """
    target_folders = set(map(str, cur_folder_ids + cur_agency_folder_ids))
    indices = [
        idx for idx, item in enumerate(all_items)
        if str(item.folder.parent_id) in target_folders or str(item.folder.id) in target_folders
    ]
    return np.unique(indices)

def get_query_info(sdk, query_slug, targeted_strings):
    """Retrieve and process query information, checking for targeted strings."""
    try:
        query = sdk.query_for_slug(slug=query_slug)
        found_strings = [ts for ts in targeted_strings if ts in str(query)]
        if found_strings:
            qf_id = str(query).find(found_strings[0])
            return query.id, str(query)[(qf_id - 10):(qf_id + 50)], found_strings
    except Exception as e:
        print(f"Error processing query with slug {query_slug}: {e}")
    return None

def process_dashboards(sdk, dashboard, targeted_strings):
    """Process each dashboard to find relevant queries without duplicates in tiles and found strings,
    ensuring tiles also contain targeted strings and noting where strings are found."""
    dashboard_info = {
        'Dashboard ID': dashboard.id,
        'Dashboard Title': dashboard.title,
        'Folder Name': dashboard.folder.name,
        'Folder ID': dashboard.folder.id,
        'Model': None,
        'Merged?': 'No',  # Default assumption
        'Tiles': set(),  # Using set to avoid duplicates
        'Found Strings': set(),
        'Found In': set()  # To track where exactly strings are found
    }

    # Check if any targeted string is in the overall dashboard description
    dashboard_str = str(dashboard)
    found_in_dashboard = any(ts in dashboard_str for ts in targeted_strings)
    if found_in_dashboard:
        dashboard_info['Found In'].add("Dashboard Description")

    # Process for merged queries if available and each tile
    found_in_tiles = False
    for d_elem in dashboard.dashboard_elements:
        element_str = str(d_elem)
        found_in_element = any(ts in element_str for ts in targeted_strings)
        if found_in_element:
            dashboard_info['Found In'].add("Tile: " + d_elem.title)

        if hasattr(d_elem, 'result_maker') and d_elem.result_maker and d_elem.result_maker.id:
            dashboard_info['Model'] = d_elem.result_maker.filterables[0].model
            if d_elem.merge_result_id:
                dashboard_info['Merged?'] = 'Yes'
                cur_mq = sdk.merge_query(merge_query_id=d_elem.merge_result_id)
                for cur_sq in cur_mq.source_queries:
                    query_info = get_query_info(sdk, cur_sq.query_slug, targeted_strings)
                    if query_info and found_in_element:
                        dashboard_info['Tiles'].add(d_elem.title)
                        dashboard_info['Found Strings'].update(query_info[2])
                        found_in_tiles = True
                break  # Stop further checks if merged query processed

    # Process non-merged tiles
    if dashboard_info['Merged?'] == 'No':
        for tile in dashboard.dashboard_elements:
            tile_str = str(tile)
            found = [s for s in targeted_strings if s in tile_str]
            if found:
                dashboard_info['Tiles'].add(tile.title)
                dashboard_info['Found Strings'].update(found)
                dashboard_info['Found In'].add("Tile: " + tile.title)
                found_in_tiles = True

    # Only include dashboard info if relevant strings were found in dashboard description or any tile
    if not (found_in_dashboard or found_in_tiles):
        return None

    # Finalize data: convert sets to lists for output consistency
    dashboard_info['Found Strings'] = list(dashboard_info['Found Strings'])
    dashboard_info['Tiles'] = list(dashboard_info['Tiles'])
    dashboard_info['Found In'] = list(dashboard_info['Found In'])
    return dashboard_info

# Example usage of this function would remain similar to previous examples.
