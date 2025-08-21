"""Sidebar containing user inputs to surrogate selection.

This module defines a sidebar interface for users to input parameters for
automated surrogate selection or to manually select surrogates for
comparison.
"""

import numpy as np
from shiny import module, reactive, req, ui

from calculation.ionization_efficiency import IONIZATION_EFFICIENCY_EMBEDDING
from calculation.surrogate_selection import SurrogateSelection
from dashboard.utils.notifications import ValidationErrors, error_notification

# Surrogate selection defaults
DEFAULT_STRATS = [SurrogateSelection.Strategy.HIERARCHICAL]
DEFAULT_N = 0.2

@module.ui
# pylint: disable-next=C0116 # Silence missing docstring error
def dashboard_sidebar():
    return ui.sidebar(
        ui.input_selectize(
            'strats',
            'Selection Strategies',
            [s.value for s in SurrogateSelection.Strategy],
            selected=DEFAULT_STRATS,
            multiple=True
        ),
        ui.tooltip(
            ui.input_numeric(
                'n', 'Number of Surrogates', DEFAULT_N, min=0.01, step=0.01),
            'Values < 1 will be treated as a fraction of the dataset'
            ' size; values >= 1 will be treated as a raw count.'
        ),
        ui.input_switch('include_user', 'Include user selected surrogates?'),
        ui.panel_conditional(
            'input.include_user',
            ui.input_text_area(
                'user_surr',
                'User Selected Surrogate IDs',
                placeholder='One per line, optional'
            )
        ),
        ui.input_task_button('select', 'Select')
    )

@module.server
# pylint: disable-next=C0116,W0613,W0622 # Silence server syntax errors
def dashboard_sidebar_server(input, output, session, desc, _set_labels):

    @reactive.effect
    @reactive.event(input.select)
    def select():
        # Check input validity
        valid_n = input.n() > 0
        valid_strategies = input.strategies() and len(input.strategies()) > 0

        # Identify user-input surrogates
        user_surr = np.where(
            np.isin(desc().index, input.user_surr().splitlines()))[0]
        user_n = len(user_surr)

        # Require at least one valid input to proceed, otherwise exit silently
        req(valid_n or valid_strategies or user_n > 0)

        # Provide error notifications for invalid inputs to automated selection
        if valid_n and not valid_strategies:
            error_notification(ValidationErrors.NO_STRAT)
            return

        if valid_strategies and not valid_n:
            error_notification(ValidationErrors.NO_N)
            return

        # Process automated surrogate selection if inputs are valid
        selector = SurrogateSelection(desc()[IONIZATION_EFFICIENCY_EMBEDDING])
        surr = {
            strat: selector.select(n=input.n(), strategy=strat)
            for strat in input.strategies()
        } if valid_n and valid_strategies else {}

        # Process user-selected surrogates if provided
        if user_n > 0:
            surr['user'] = (user_surr, selector.score(user_surr))

        # Update plot colors
        strats = {i: [] for i in range(desc().shape[0])}
        for s, (idx, _) in surr.items():
            for i in idx:
                strats[i].append(s)
        _set_labels(
            ['&'.join(sorted(s)) if s else 'none' for s in strats.values()])

    @reactive.effect
    @reactive.event(desc)
    def clear():
        """Clear surrogate selection inputs when dataset changes."""
        ui.update_selectize('strats', selected=DEFAULT_STRATS)
        ui.update_numeric('n', value=DEFAULT_N)
        ui.update_switch('include_user', value=False)
        ui.update_text_area('user_surr', value='')
