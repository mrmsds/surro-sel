"""Custom reactive colorable scatter plot module.

This module contains definitions for a plotly scatterplot data visualization
with changeable color and event handling for data hover and click.

It may be reused in multiple contexts, such as to display the TSNE embedding
of ionization efficiency descriptors or other properties.
"""

import plotly.express as px
from shiny import module, render, ui
from shinywidgets import output_widget, render_plotly

from dashboard.cards.shared import PLOTLY_TEMPLATE, PLOTLY_COLORS

@module.ui
# pylint: disable-next=C0116 # Silence docstring error
def colorable_scatterplot_card():
    return ui.output_ui('card')

@module.server
# pylint: disable-next=C0116,R0913,R0917 # Silence server syntax errors
def colorable_scatterplot_card_server(
    # pylint: disable-next=W0622,W0613 # Silence (more) server syntax errors
    input, output, session, title, data, xcol, ycol, labels, **layout_kwargs):

    @render_plotly
    def plot():
        return px.scatter(
            data(),
            x=xcol,
            y=ycol,
            color=labels(),
            # Required for point indexing
            hover_name=data().index,
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=PLOTLY_COLORS
        ).update_layout(**layout_kwargs)

    @render.ui
    def card():
        return ui.card(
            ui.card_header(title),
            ui.card_body(
                output_widget('plot')
            ),
            full_screen=True,
            height='100%'
        )
