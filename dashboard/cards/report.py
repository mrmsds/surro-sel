"""Card UI element displaying a text report of surrogate selection results."""

from shiny import module, render, req, ui

@module.ui
def report_card(): # pylint: disable=C0116 # Silence docstring error
    return ui.card(
        ui.card_header('Surrogate Selection Report'),
        ui.card_body(
            ui.output_text_verbatim('text')
        ),
    )

@module.server
# pylint: disable-next=C0116,W0613,W0622 # Silence server syntax errors
def report_card_server(input, output, session, desc, surr):

    @render.text
    def text():
        req(surr())
        return '\n====================\n'.join([
            f'{strat.upper()}\nLARD: {float(res[1]):.3g}\n'
            + f'Surrogates Selected:\n{'\n'.join(desc().index[res[0]])}'
            for strat, res in surr().items()
        ])
