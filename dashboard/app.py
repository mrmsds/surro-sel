"""Parent module for qNTA SurroSel app."""

import pandas as pd
from shiny import App, reactive, ui

from dashboard.cards.colorable_scatterplot import (
    colorable_scatterplot_card,
    colorable_scatterplot_card_server
)
from dashboard.modals.load import load_modal, load_modal_server
from dashboard.modals.upload import upload_modal, upload_modal_server
from dashboard.sidebar import dashboard_sidebar, dashboard_sidebar_server
from dashboard.utils.files import LAST_UPDATED, update_log, get_datasets

# App formatting constants
NAVBAR_OPTIONS = {'class': 'bg-primary', 'theme': 'dark'}

# Initialize the data folder and log file on app start
update_log()

# Main application page UI
page = ui.page_navbar(
    ui.nav_panel(
        '',
        colorable_scatterplot_card('tsne')
    ),
    ui.nav_spacer(),
    ui.nav_control(ui.input_action_button('load', 'Load Existing Data')),
    ui.nav_control(ui.input_action_button('upload', 'Upload New Data')),
    title='qNTA SurroSel',
    fillable=True,
    navbar_options=ui.navbar_options(**NAVBAR_OPTIONS),
    # pylint: disable-next=E1121 # Silence errors from module call
    sidebar=dashboard_sidebar('sidebar')
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
    # Surrogate selection data
    surr = reactive.value({})

    def set_data(data_, desc_):
        """Callback function to allow child modules to set global data.

        Args:
            data_: df containing new data
            desc_: df containing calculated descriptors
        """

        data.set(data_)
        desc.set(desc_)
        surr.set({}) # Any time data is changed, surrogates should reset

    def set_surr(surr_):
        """Callback function to allow child modules to set global surrogates.

        Args:
            surr_: dict of new surrogate selection results
        """

        surr.set(surr_)

    # Register server information for input modules
    load_modal_server('load_modal', datasets=datasets, _set_data=set_data)
    upload_modal_server('upload_modal', datasets=datasets, _set_data=set_data)
    dashboard_sidebar_server('sidebar', desc=desc, _set_surr=set_surr)

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

    @reactive.calc
    def surrogate_labels():
        """Reactively convert surrogate selection data to data point labels."""
        labels = {i: [] for i in range(desc().shape[0])}
        for strat, (idx, _) in surr().items():
            for i in idx:
                labels[i].append(strat)
        return ['&'.join(sorted(x)) if x else 'none' for x in labels.values()]

    # Register server information for output modules
    colorable_scatterplot_card_server(
        'tsne',
        'Ionization Efficiency TSNE',
        desc,
        'TSNE1',
        'TSNE2',
        surrogate_labels,
        legend_title='Surrogate Set'
    )

# Run app
app = App(page, server)
