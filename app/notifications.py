"""Define content and config for reusable pop-up notifications to the user."""

from enum import auto, StrEnum

from shiny.ui import notification_show

DEFAULT_DURATION = 3
DEFAULT_TYPE = 'message'

def _notify(message, type=DEFAULT_TYPE):
    notification_show(message, type=type, duration=DEFAULT_DURATION)

LOAD_SUCCESS_MESSAGE = 'Successfully loaded %d records (%d structurable).'

def notify_load_success(n_records, n_structs):
    """Display a notification for successful data load."""
    _notify(LOAD_SUCCESS_MESSAGE % (n_records, n_structs))

class ValidationErrors(StrEnum):
    """Enum for application form validation error types."""
    NO_NAME = auto()
    NAME_LEN = auto()
    NAME_INVALID = auto()
    NAME_DUP = auto()
    NO_FILE = auto()
    COLS_DUP = auto()
    NO_STRAT = auto()
    NO_N = auto()

ERROR_MESSAGES = {
    ValidationErrors.NO_NAME: 'Dataset name is required.',
    ValidationErrors.NAME_LEN: 'Dataset name must be at least two chars and '
        'no more than 32 chars.',
    ValidationErrors.NAME_INVALID: 'Invalid characters in dataset name. '
        'Only alphanumerics, underscores, dashes, and spaces are permitted.',
    ValidationErrors.NAME_DUP: 'Dataset name already in use.',
    ValidationErrors.NO_FILE: 'Missing CSV file for upload.',
    ValidationErrors.COLS_DUP: 'Primary ID and QSAR-ready SMILES column '
        'selections may not be the same.',
    ValidationErrors.NO_STRAT: 'At least one surrogate selection strategy '
        'is required.',
    ValidationErrors.NO_N: 'Number of surrogates must be greater than zero.'
}

def notify_error(key):
    """Display an error notification based on key."""
    if key in ERROR_MESSAGES:
        _notify(ERROR_MESSAGES[key], type='error')
    else:
        raise ValueError(f'Error key {key} not found.')
