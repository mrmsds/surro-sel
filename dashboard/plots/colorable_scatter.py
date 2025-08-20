"""Custom reactive colorable scatter plot module.

This module contains definitions for a plotly scatterplot data visualization
with changeable color and event handling for data hover and click.

It may be reused in multiple contexts, such as to display the TSNE embedding
of ionization efficiency descriptors or other properties.
"""

import plotly.express as px
import plotly.graph_objects as go
from shiny import module, reactive, req
from shinywidgets import output_widget, render_widget

from dashboard.plots.shared import PLOTLY_TEMPLATE, PLOTLY_COLORS

@module.ui
# pylint: disable-next=C0116 # Silence docstring error
def colorable_scatterplot():
    return output_widget('scatter')

@module.server
# pylint: disable-next=C0116,R0913,R0917 # Silence server syntax errors
def colorable_scatterplot_server(
    # pylint: disable-next=W0622,W0613 # Silence (more) server syntax errors
    input, output, session, data, xcol, ycol, labels, **layout_kwargs):

    hovered = reactive.value()
    clicked = reactive.value()

    def _set_point_index_callback(value):
        # Define a function to set the provided reactive value based on event
        # pylint: disable-next=W0613 # Silence error from handler syntax
        def _callback(trace, points, state):
            if len(pt_idx := points.point_inds) == 1:
                # Cheat workaround to get the index from the hovertext
                value.set(trace['hovertext'][pt_idx][0])
        # Return the function to be used as a callback
        return _callback

    @render_widget
    def scatter():
        req(not data().empty)
        fig = px.scatter(
            data(),
            x=xcol,
            y=ycol,
            color=labels(),
            # Required for point indexing
            hover_name=data().index,
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=PLOTLY_COLORS
        ).update_layout(**layout_kwargs)

        # Set up the figure widget to register event handlers
        wi = go.FigureWidget(fig.data, fig.layout)
        for tr in wi.data:
            tr.on_hover(_set_point_index_callback(hovered))
            tr.on_click(_set_point_index_callback(clicked))

        return wi

    return hovered, clicked
