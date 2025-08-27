"""Sidebar containing user inputs to surrogate selection.

This module defines a sidebar interface for users to input parameters for
automated surrogate selection or to manually select surrogates for
comparison.
"""

import numpy as np
from faicons import icon_svg
from shiny import module, reactive, ui

from calculation.ionization_efficiency import IONIZATION_EFFICIENCY_EMBEDDING
from calculation.surrogate_selection import SurrogateSelection
from dashboard.utils.notifications import ValidationErrors, error_notification

# Surrogate selection defaults
DEFAULT_STRATS = [SurrogateSelection.Strategy.HIERARCHICAL]
DEFAULT_N = 0.2
# Random simulated surrogate selection comparison parameters
RANDOM_REPS = 100
RANDOM_NS = [0.01, 0.1, 0.2, 0.5]

@module.ui
# pylint: disable-next=C0116 # Silence missing docstring error
def dashboard_sidebar():
    return ui.sidebar(
        ui.input_switch(
            'include_auto', 'Include auto selected surrogates?', True),
        ui.panel_conditional(
            'input.include_auto',
            ui.input_selectize(
                'strats',
                'Selection Strategies',
                [s.value for s in SurrogateSelection.Strategy],
                selected=DEFAULT_STRATS,
                multiple=True
            ),
            ui.input_numeric(
                'n',
                ui.span(
                    'Number of Surrogates ',
                    ui.tooltip(
                        icon_svg('circle-info'),
                        (
                            'Values < 1 will be treated as a fraction of the '
                            'dataset size; values >= 1 will be treated as a '
                            'raw count.'
                        ),
                        placement='right'
                    )
                ),
                DEFAULT_N,
                min=0.01,
                step=0.01
            )
        ),
        ui.input_switch('include_user', 'Include user selected surrogates?'),
        ui.panel_conditional(
            'input.include_user',
            ui.input_text_area(
                'user_ids',
                'User Selected Surrogate IDs',
                placeholder='One per line'
            )
        ),
        ui.input_task_button('select', 'Select')
    )

@module.server
# pylint: disable-next=C0116,W0613,W0622 # Silence server syntax errors
def dashboard_sidebar_server(input, output, session, desc, _set_surr):

    @reactive.calc
    def user_idx():
        """Reactively process user entered surrogate IDs to list of indices."""
        return np.where(
            np.isin(desc().index, input.user_ids().splitlines()))[0]

    def _validate_auto(n, strats):
        """Validate inputs to automated surrogate selection.
        
        Args:
            n: user input for number of surrogates to select
            strats: user selected surrogate selection strategies
        Returns:
            error keys if validation failed, or empty list
        """

        errors = []
        if not n or n <= 0:
            errors.append(ValidationErrors.N_INVALID)

        if not strats:
            errors.append(ValidationErrors.NO_STRAT)

        return errors

    def _process_auto(selector, n, strats):
        """Process automated surrogate selection with user inputs.
        
        Args:
            selector: SurrogateSelection instance with relevant data
            n: user input number of surrogates
            strats: user selected surrogate selection strategies
        Returns:
            dict of surrogate selections and score for each strategy
        """

        return {
            strat: selector.select(n=n, strategy=strat)
            for strat in strats
        }

    def _validate_user(user_idx):
        """Validate inputs to manual user surrogate selection.
        
        Args:
            user_idx: indices of user selected surrogates
        Returns:
            error keys if validation failed, or empty list
        """

        errors = []
        if user_idx.size == 0:
            errors.append(ValidationErrors.NO_USER)

        return errors

    def _process_user(selector, user_idx):
        """Process manual user surrogate selection with user inputs.
        
        Args:
            user_idx: indices of user selected surrogates
        Returns:
            dict entry of surrogate selection and score
        """

        return {'user': (user_idx, selector.score(user_idx))}

    def _process_conditional(switch, selector, _validate_fn, _process_fn, *args):
        """Chain validation, error display, and processing of selection.
        
        Args:
            switch: condition to check whether selection should be processed
            selector: SurrogateSelection instance
            _validate_fn: input validation function
            _process_fn: input processing function
            *args: arguments to validation and processing functions
        Returns:
            dict of surrogate selections and score for each strategy
        """

        surr = {}
        if switch:
            errors = _validate_fn(*args)
            if errors:
                for err in errors:
                    error_notification(err)
            else:
                surr = _process_fn(selector, *args)

        return surr

    def _simulate_random(selector, ns):
        scores = []
        for n in ns:
            scores.extend([
                selector.select(n, SurrogateSelection.Strategy.RANDOM)[1]
                for _ in range(RANDOM_REPS)
            ])
        return {
            'scores': scores,
            'ns': np.repeat(ns, RANDOM_REPS)
        }

    @reactive.effect
    @reactive.event(input.select)
    def select():
        """Perform surrogate selection on click."""

        # Check data is loaded
        if desc().empty:
            error_notification(ValidationErrors.NO_DATA)
            return # Short-circuit with error notification if not

        # Initialize selector instance
        selector = SurrogateSelection(desc()[IONIZATION_EFFICIENCY_EMBEDDING])
        # Process automated and/or user surrogate selection
        surr = _process_conditional(
            include_auto := input.include_auto(),
            selector,
            _validate_auto,
            _process_auto,
            n_auto := input.n(),
            input.strats()
        ) | _process_conditional(
            include_user := input.include_user(),
            selector,
            _validate_user,
            _process_user,
            user_idx()
        )

        # Proceed if selection succeeded
        if surr:
            ns = RANDOM_NS
            if include_user and (n_user := len(user_idx())) > 0:
                ns.append(n_user)
            if include_auto:
                ns.append(n_auto)

            # Get effective size of fractional n values and ensure uniqueness
            unique_int_ns = [
                n if n >= 1 else round(desc().shape[0] * n)
                for n in list(set(ns))
            ]

            # Execute random simulation
            sim = _simulate_random(selector, sorted(unique_int_ns))

            # Update global surrogate selection data using callback
            _set_surr(surr, sim)

    @reactive.effect
    @reactive.event(desc)
    def clear():
        """Clear surrogate selection inputs when dataset changes."""
        ui.update_switch('include_auto', value=True)
        ui.update_selectize('strats', selected=DEFAULT_STRATS)
        ui.update_numeric('n', value=DEFAULT_N)
        ui.update_switch('include_user', value=False)
        ui.update_text_area('user_surr', value='')
