"""Card UI element displaying a scatterplot of user selected properties."""

import numpy as np
from shiny import module, reactive, render, ui

from dashboard.cards.shared import (
    colorable_scatterplot, colorable_scatterplot_server)

@module.ui
def property_card(): # pylint: disable=C0116 # Silence docstring error
    return ui.card(
        ui.card_header('Property Comparison Plot'),
        ui.card_body(
            # pylint: disable=E1121 # Silence error from module call
            ui.layout_column_wrap(
                ui.output_ui('xcol_select'),
                ui.output_ui('ycol_select')
            ),
            colorable_scatterplot('plot')
        ),
        full_screen=True
    )

@module.server
# pylint: disable-next=C0116,W0613,W0622 # Silence server syntax errors
def property_card_server(input, output, session, data, labels):

    @reactive.calc
    def num_cols():
        """Reactive calculation of numerical columns in input data."""
        return data().select_dtypes(include=np.number).columns.tolist()

    def _num_cols_select(ax):
        return ui.input_select(
            ax.lower() + 'col', ax.upper() + '-axis Property', choices=num_cols())

    @render.ui
    def xcol_select():
        return _num_cols_select('x')

    @render.ui
    def ycol_select():
        return _num_cols_select('y')

    # pylint: disable-next=E1120 # Silence error from module call
    colorable_scatterplot_server(
        'plot',
        data,
        labels,
        input.xcol,
        input.ycol,
        showlog=True,
        legend_title='Surrogate Set'
    )
