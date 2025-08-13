"""Modal containing existing dataset load functionality.

This module contains definitions for a modal allowing users to reload an
existing dataset (previously uploaded and stored as a parquet file).
"""

from shiny import module, reactive, render, ui

from notifications import notify_error, notify_load_success, ValidationErrors
from files import load_data

@module.ui
def load_modal():
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
            notify_error(ValidationErrors.NO_NAME)
            return # Stop processing, but do not close the modal

        # Otherwise, read data files and update global app data
        data, desc = load_data(input.name())
        _set_data(data, desc)

        # Show success notification
        notify_load_success(data.shape[0], desc.shape[0])

        # Close modal
        ui.modal_remove()
