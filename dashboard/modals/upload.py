"""Modal containing new data upload functionality.

This module contains definitions for a modal allowing users to upload a new
data set from a CSV file and store both original data and calculated
ionization efficiency descriptors as parquet files.
"""

import re
from enum import StrEnum
from os.path import splitext

import pandas as pd
from shiny import module, reactive, ui

from calculation.ionization_efficiency import calculate_ionization_efficiency
from dashboard.utils.files import save_data
from dashboard.utils.notifications import (
    load_success_notification, error_notification, ValidationErrors)

# Regular expression for dataset name character validation
NAME_PATTERN = re.compile('[A-Za-z0-9_\\- ]{2,32}')


class FileExtensions(StrEnum):
    """Enum of acceptable file extensions for parsing."""
    CSV = '.csv'
    XLS = '.xls'
    XLSX = '.xlsx'
    TSV = '.tsv'
    TXT = '.txt'


@module.ui
def upload_modal(): # pylint: disable=C0116 # Silence missing docstring error
    return ui.modal(
        ui.tooltip(
            ui.input_text('name', 'Name'),
            'Name must be unique, at least two chars, no more than 32 chars, '
            'and contain only alphanumerics, underscores, dashes, and spaces.'
        ),
        ui.input_file(
            'file',
            'Choose Data File',
            accept=[ext.value for ext in FileExtensions],
            multiple=False
        ),
        ui.input_select(
            'id_col', 'Select Primary ID Column', choices=[]),
        ui.input_select(
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
# pylint: disable-next=C0116,W0622,W0613,R0915 # Silence server syntax errors
def upload_modal_server(input, output, session, datasets, _set_data):

    # Reactive value to hold temporary data loaded from the file input,
    # used to populate selectors before processing & persisting the data
    temp = reactive.value(pd.DataFrame())

    def _clear_temp():
        """Reset temp reactive to an empty data frame."""
        temp.set(pd.DataFrame())

    def _read_file(file):
        """Read a pandas df from a variety of tabular data formats.
        
        Args:
            file: shiny ui.input_file upload content
        Returns:
            df of parsed file data
        """

        _, ext = splitext(file['name'])
        content = file['datapath']

        df = pd.DataFrame()
        match ext:
            case FileExtensions.CSV:
                df = pd.read_csv(content)
            case FileExtensions.XLS | FileExtensions.XLSX:
                df = pd.read_excel(content)
            case FileExtensions.TSV:
                df = pd.read_table(content, sep='\t')
            case FileExtensions.TXT:
                # Infer delimiter from unspecified tabular text file
                df = pd.read_table(content, sep=None, engine='python')

        return df
    
    def _validate_name(name):
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

    def _validate_data(data, id_col, qrs_col):
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

    def _process_data(data, id_col, qrs_col, ignore_cols):
        """Process user uploaded data according to column selections.
        
        Args:
            data: df of user uploaded data
            id_col: user selected ID col from data
            qrs_col: user selected QSAR-ready SMILES col from data
            ignore_cols: user selected columns to ignore
        Returns:
            processed data df
        """

        # Set index, drop user ignored columns, and return a deep copy of data
        return data.copy(deep=True).set_index(id_col)\
            .drop(columns=[col for col in ignore_cols if not col == qrs_col])

    def _clear_and_close():
        """Clear entered data and close the modal."""
        _clear_temp()
        ui.modal_remove()

    @reactive.effect
    @reactive.event(input.file)
    def upload_temp():
        """Read the uploaded file into the temp reactive when input changes."""

        # Check if user has provided a file
        file = input.file()
        if not file:
            # Reset temp data and stop processing if no file contents
            _clear_temp()
            return

        try:
            # Attempt parsing file contents
            temp.set(_read_file(file[0]))
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            # Reset temp data if parser errored out
            _clear_temp()
        finally:
            # If final data is empty for any reason, notify user
            if temp().empty:
                error_notification(ValidationErrors.FILE_INVALID)

    @reactive.effect()
    @reactive.event(temp)
    def update_select():
        """Update select inputs with columns from temp when it changes."""

        # Get available columns from temp data (or empty list if temp is empty)
        choices = [] if temp().empty else list(temp().columns)

        # Update select inputs with available columns
        ui.update_select('id_col', choices=choices)
        ui.update_select('qrs_col', choices=choices)
        ui.update_selectize('ignore_cols', choices=choices)

    @reactive.effect
    @reactive.event(input.upload)
    def upload():
        """Perform data validation and final upload on upload button click."""

        # Check for dataset name validation errors
        errors = _validate_name(name := input.name())
        # Check for data and column selection validation errors
        errors.extend(
            _validate_data(
                temp(),
                id_col := input.id_col(),
                qrs_col := input.qrs_col()
            )
        )

        # Short-circuit with notification(s) if needed
        if len(errors) > 0:
            # Display all error messages
            for err in errors:
                error_notification(err)
            return # Stop processing, but do not close the modal

        # Process data and calculate descriptors
        data = _process_data(temp(), id_col, qrs_col, input.ignore_cols())
        desc = calculate_ionization_efficiency(data[qrs_col], data.index)

        # Save data frames as parquet files
        save_data(name, data, desc)

        # Use callback to update global app data
        _set_data(data, desc)

        # Show success notification, clear temp data, and close modal
        load_success_notification(data.shape[0], desc.shape[0])
        _clear_and_close()

    @reactive.effect
    @reactive.event(input.close)
    def close():
        """Clear temp data and close modal on close button click."""
        _clear_and_close()
