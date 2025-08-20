"""Parent module for Shiny dashboard app."""

import pandas as pd
from shiny import App, reactive, ui
from shinyswatch import theme

from dashboard.files import get_datasets, update_log, LAST_UPDATED
from dashboard.modals.load import load_modal, load_modal_server
from dashboard.modals.upload import upload_modal, upload_modal_server

# App formatting constants
THEME = theme.pulse
NAVBAR_OPTIONS = {'class': 'bg-primary', 'theme': 'dark'}

# Initialize the data file and update log folder on app start
update_log()

# Main application page UI
page = ui.page_navbar(
    fillable=True,
    theme=THEME,
    navbar_options=ui.navbar_options(**NAVBAR_OPTIONS)
)

# Main application page server
# pylint: disable-next=C0116,W0622,W0613 # Silence errors from server syntax
def server(input, output, session):
    # pylint: disable=E1120,E1121 # Silence errors from all module calls

    # Reactive value for list of available loaded dataset names
    datasets = reactive.value([])
    # Original data and calculated descriptors for current dataset
    data = reactive.value(pd.DataFrame())
    desc = reactive.value(pd.DataFrame())
    # Data labels (displayed as colors)
    labels = reactive.value(None)

    def set_data(data_, desc_):
        """Callback function to allow child modules to set global data.

        Args:
            data_: df containing new data
            desc_: df containing calculated descriptors
        """

        data.set(data_)
        desc.set(desc_)
        labels.set(None) # Any time data is changed, labels should reset

    def set_labels(labels_):
        """Callback function to allow child modules to set global labels.

        Args:
            labels_: array-like of new labels
        """

        labels.set(labels_)

    # Register server information for child modules
    load_modal_server('load_modal', datasets=datasets, _set_data=set_data)
    upload_modal_server('upload_modal', datasets=datasets, _set_data=set_data)

    @reactive.effect
    @reactive.file_reader(LAST_UPDATED)
    def update_datasets():
        """Reactively update available datasets on log file change."""
        datasets.set(get_datasets())

    @reactive.effect
    @reactive.event(input.load)
    def show_load_modal():
        """Show load modal on button click."""
        ui.modal_show(load_modal('load_modal'))

    @reactive.effect
    @reactive.event(input.upload)
    def show_upload_modal():
        """Show upload modal on button click."""
        ui.modal_show(upload_modal('upload_modal'))

# Run app
app = App(page, server)
