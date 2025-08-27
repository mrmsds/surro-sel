"""Card UI element displaying a TSNE plot of ionization efficiency."""

from shiny import module, reactive, ui

from dashboard.cards._shared import (
    colorable_scatterplot, colorable_scatterplot_server)

@module.ui
def tsne_card(): # pylint: disable=C0116 # Silence docstring error
    return ui.card(
        ui.card_header('Ionization Efficiency TSNE'),
        # pylint: disable-next=E1121 # Silence error from module call
        ui.card_body(colorable_scatterplot('plot')),
        full_screen=True
    )

@module.server
# pylint: disable-next=C0116,W0613,W0622 # Silence server syntax errors
def tsne_card_server(input, output, session, desc, labels):

    def _make_constant_reactive(cnst):
        return reactive.calc(lambda: cnst)

    # pylint: disable-next=E1120 # Silence error from module call
    colorable_scatterplot_server(
        'plot',
        desc,
        labels,
        _make_constant_reactive('TSNE1'),
        _make_constant_reactive('TSNE2'),
        showlog=False,
        legend_title='Surrogate Set'
    )
