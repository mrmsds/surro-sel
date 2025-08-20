"""Modal containing existing dataset load functionality.

This module contains definitions for a modal allowing users to reload an
existing dataset (previously uploaded and stored as a parquet file).
"""

from shiny import module, reactive, render, ui

from dashboard.notifications import (
    ValidationErrors, error_notification, load_success_notification)
from dashboard.files import load_data

@module.ui
def load_modal(): # pylint: disable=C0116 # Silence missing docstring error
    return ui.modal(
        ui.output_ui('name_select'),
        title='Load Existing Dataset',
        easy_close=False,
        footer=[
            ui.input_task_button('load', 'Load'),
            ui.modal_button('Close')
        ]
    )

@module.server
# pylint: disable-next=C0116,W0622,W0613 # Silence errors from server syntax
def load_modal_server(input, output, session, datasets, _set_data):

    @render.ui
    def name_select():
        return ui.input_selectize(
            'name', 'Dataset Name', choices=[''] + datasets())

    @reactive.effect
    @reactive.event(input.load)
    def load():
        """Perform data load on button click."""

        # Show an error if button clicked without a selection
        if not input.name():
            error_notification(ValidationErrors.NO_NAME)
            return # Stop processing, but leave the modal open

        # Otherwise, read data files and update global app data
        data, desc = load_data(input.name())
        _set_data(data, desc)

        # Show success notification
        load_success_notification(data.shape[0], desc.shape[0])

        # Close modal
        ui.modal_remove()
