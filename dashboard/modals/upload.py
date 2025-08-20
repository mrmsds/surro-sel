"""Modal containing new data upload functionality.

This module contains definitions for a modal allowing users to upload a new
data set from a CSV file and store both original data and calculated
ionization efficiency descriptors as parquet files.
"""

import re

import pandas as pd
from shiny import module, reactive, req, ui

from calculation.ionization_efficiency import calculate_ionization_efficiency
from dashboard.files import save_data
from dashboard.notifications import (
    load_success_notification, error_notification, ValidationErrors)

# Regular expression for dataset name character validation
NAME_PATTERN = re.compile('[A-Za-z0-9_\\- ]{2,32}')

@module.ui
def upload_modal(): # pylint: disable=C0116 # Silence missing docstring error
    return ui.modal(
        ui.tooltip(
            ui.input_text('name', 'Name'),
            'Name must be unique, at least two chars, no more than 32 chars, '
            'and contain only alphanumerics, underscores, dashes, and spaces.'
        ),
        ui.input_file(
            'file', 'Choose CSV File', accept=['.csv'], multiple=False),
        ui.input_selectize(
            'id_col', 'Select Primary ID Column', choices=[]),
        ui.input_selectize(
            'qrs_col', 'Select QSAR-Ready SMILES Column', choices=[]),
        ui.input_selectize(
            'ignore_cols', 'Ignore Columns', choices=[], multiple=True),
        title='Upload New Data',
        easy_close=False, # No easy close to ensure data is always cleared
        footer=[
            ui.input_task_button('upload', 'Upload'),
            ui.input_action_button('close', 'Close')
        ]
    )

@module.server
# pylint: disable-next=C0116,W0622,W0613 # Silence server syntax errors
def upload_modal_server(input, output, session, datasets, _set_data):

    # Reactive value to hold temporary data loaded from the file input,
    # used to populate selectors before processing & persisting the data
    temp = reactive.value(pd.DataFrame())

    @reactive.effect
    def upload_temp():
        """Read the uploaded file into the temp reactive when input changes."""
        temp.set(
            pd.DataFrame()
            if (file := input.file()) is None
            else pd.read_csv(file[0]['datapath'])
        )

    @reactive.effect()
    def update_select():
        """Update select inputs with columns from temp when it changes."""
        req(not temp().empty)

        # List columns from the temp data frame
        choices = list(temp().columns)

        # Update select inputs with available columns
        ui.update_selectize('id_col', choices=choices)
        ui.update_selectize('qrs_col', choices=choices)
        ui.update_selectize('ignore_cols', choices=choices)

    def clear_and_close():
        """Clear entered data and close the modal."""
        temp.set(pd.DataFrame())
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.upload)
    def upload():
        """Perform data validation and final upload on button click."""

        errors = []
        # Check dataset name
        if not input.name():
            # Check dataset name provided
            errors.append(ValidationErrors.NO_NAME)
        elif input.name().lower() in [x.lower() for x in datasets()]:
            # Check dataset name not duplicated (case insensitive)
            errors.append(ValidationErrors.NAME_DUP)
        elif not re.fullmatch(NAME_PATTERN, input.name()):
            # Check dataset for valid length and characters
            errors.append(ValidationErrors.NAME_INVALID)

        # Check data and column inputs
        if temp().empty:
            # Check data was provided and read
            errors.append(ValidationErrors.NO_FILE)
        elif input.qrs_col() == input.id_col():
            # Check column selections not duplicated
            errors.append(ValidationErrors.COLS_DUP)

        # Short-circuit with notification(s) if needed
        if len(errors) > 0:
            # Display all error messages
            for err in errors:
                error_notification(err)
            return # Stop processing, but do not close the modal

        # Set index, drop user ignored columns, and propagate a copy of temp
        # data to final
        cols_to_drop = [
            col for col in input.ignore_cols() if not col == input.qrs_col()]
        data = temp().copy(deep=True).set_index(input.id_col())\
            .drop(columns=cols_to_drop)

        # Calculate ionization efficiency descriptors and TSNE
        desc = calculate_ionization_efficiency(
            data[input.qrs_col()], data.index, with_tsne=True)

        # Save data frames as parquet files
        save_data(input.name(), data, desc)

        # Use callback to update global app data
        _set_data(data, desc)

        # Show success notification
        load_success_notification(data.shape[0], desc.shape[0])

        # Clear temp data and close modal
        clear_and_close()

    @reactive.effect
    @reactive.event(input.close)
    def close():
        """Clear temp data and close the modal on button click."""
        clear_and_close()
