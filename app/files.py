"""Define config and utility functions for file system interactions."""

import os
from datetime import datetime

import pandas as pd

# Constants for data file names
DATA_FILENAME = 'data.parquet'
DESC_FILENAME = 'desc.parquet'

# Locate data persistence folder and last updated log file
DATA_FOLDER = './data'
LAST_UPDATED = os.path.join(DATA_FOLDER, 'last_updated.txt')

def update_log():
    """Update last updated log file with current timestamp."""

     # Ensure data folder exists
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER, exist_ok=True)

    # Write the current timestamp to the last updated file
    with open(LAST_UPDATED, 'w') as last_updated_file:
        last_updated_file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def get_datasets():
    """List available dataset names from data folder."""
    return [x for x in os.listdir(DATA_FOLDER) if not '.' in x]

def load_data(name):
    """Read data and descriptor files from a specified data directory.
    
    Args:
        name: name of the dataset directory to read from
    Returns:
        tuple of dfs containing original data and calculated descriptors
    """

    read_from_folder = os.path.join(DATA_FOLDER, name)
    def read_parquet(fname):
        return pd.read_parquet(os.path.join(read_from_folder, fname))

    return read_parquet(DATA_FILENAME), read_parquet(DESC_FILENAME)

def save_data(path, data, desc):
    """Save data and descriptor files to a specified data directory.
    
    Args:
        path: path to directory where data should be saved
        data: original data df
        desc: calculated descriptor df
    """

    def save_parquet(data, fname):
        data.to_parquet(os.path.join(path, fname), index=True)

    save_parquet(data, DATA_FILENAME)
    save_parquet(desc, DESC_FILENAME)
    update_log() # Update the last updated log
