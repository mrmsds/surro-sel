"""Modal containing new data upload functionality.

This module contains definitions for a modal allowing users to upload a new
data set from a CSV file and store both original data and calculated
ionization efficiency descriptors as parquet files.
"""

import re

import pandas as pd
from shiny import module, reactive, req, ui

from calculation.ionization_efficiency import calculate_ionization_efficiency
from dashboard.utils.files import save_data
from dashboard.utils.notifications import (
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

    def validate_name(name):
        """Validate user input dataset name.

        Based on the current name conditions, no more than one error will
        ever be returned for the dataset name, but this function is extensible
        to multiple error conditions.
        
        Args:
            name: user input dataset name
        Returns:
            list of error message keys from ValidationErrors, or empty list
        """

        errors = []
        if not name:
            # Validate name was provided
            errors.append(ValidationErrors.NO_NAME)
        elif name.lower() in [x.lower() for x in datasets()]:
            # Validate name not duplicate of existing (case insensitive)
            errors.append(ValidationErrors.NAME_DUP)
        elif not re.fullmatch(NAME_PATTERN, name):
            # Validate name permissible
            errors.append(ValidationErrors.NAME_INVALID)

        return errors

    def validate_data(data, id_col, qrs_col):
        """Validate user input data and column selections.

        Based on the current conditions, no more than one error will
        ever be returned for the data or column selections, but this function
        is extensible to multiple error conditions.

        Args:
            data: user input df
            id_col: user selected ID col from data
            qrs_col: user selected QSAR-ready SMILES col from data
        Returns:
            list of error message keys from ValidationErrors, or empty list
        """

        errors = []
        if data.empty:
            # Validate data provided
            errors.append(ValidationErrors.NO_FILE)
        elif id_col == qrs_col:
            # Validate columns not duplicated
            errors.append(ValidationErrors.COLS_DUP)

        return errors

    def clear_and_close():
        """Clear entered data and close the modal.

        This is reused for user close on button click and to finish processing
        and close modal after data upload.
        """
        temp.set(pd.DataFrame())
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.close)
    def close():
        """Clear temp data and close the modal on close button click."""
        clear_and_close()

    @reactive.effect
    @reactive.event(input.upload)
    def upload():
        """Perform data validation and final upload on upload button click."""

        # Check for dataset name validation errors
        errors = validate_name(input.name())
        # Check for data and column selection validation errors
        errors.extend(validate_data(temp(), input.id_col(), input.qrs_col()))

        # Short-circuit with notification(s) if needed
        if len(errors) > 0:
            # Display all error messages
            for err in errors:
                error_notification(err)
            return # Stop processing, but do not close the modal

        # Set index, drop user ignored columns, and propagate a copy of data
        cdrop = [c for c in input.ignore_cols() if not c == input.qrs_col()]
        data = temp().copy(deep=True)\
            .set_index(input.id_col()).drop(columns=cdrop)

        # Calculate ionization efficiency descriptors and TSNE
        desc = calculate_ionization_efficiency(
            data[input.qrs_col()], data.index, with_tsne=True)

        # Use callback to update global app data
        _set_data(data, desc)

        # Save data frames as parquet files
        save_data(input.name(), data, desc)

        # Show success notification, clear temp data, and close modal
        load_success_notification(data.shape[0], desc.shape[0])
        clear_and_close()
