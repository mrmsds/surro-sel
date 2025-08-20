"""Define content and config for reusable pop-up notifications to the user."""

from enum import auto, StrEnum

from shiny.ui import notification_show

DEFAULT_DURATION = 3
DEFAULT_TYPE = 'message'
LOAD_SUCCESS_MESSAGE = 'Successfully loaded %d records (%d structurable).'

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
    ValidationErrors.NAME_INVALID: 'Invalid dataset name. Requires 2-32 chars;'
        ' only alphanumerics, underscores, dashes, and spaces are permitted.',
    ValidationErrors.NAME_DUP: 'Dataset name already in use.',
    ValidationErrors.NO_FILE: 'Missing CSV file for upload.',
    ValidationErrors.COLS_DUP: 'Primary ID and QSAR-ready SMILES column '
        'selections may not be the same.',
    ValidationErrors.NO_STRAT: 'At least one surrogate selection strategy '
        'is required.',
    ValidationErrors.NO_N: 'Number of surrogates must be greater than zero.'
}

# pylint: disable-next=W0622 # Silence error from overriding built-in 'type'
def _notification(message, type=DEFAULT_TYPE):
    # Generic notification function with a specified type and default duration
    notification_show(message, type=type, duration=DEFAULT_DURATION)

def load_success_notification(n_records, n_structs):
    """Display a notification for successful data load.
    
    Args:
        n_records: total number of records loaded
        n_structs: number of loaded records with structures
    """

    _notification(LOAD_SUCCESS_MESSAGE % (n_records, n_structs))

def error_notification(key):
    """Display an error notification based on key.
    
    Args:
        key: dictionary key (from ValidationErrors enum) for error type
    """

    if key in ERROR_MESSAGES:
        _notification(ERROR_MESSAGES[key], type='error')
    else:
        raise ValueError(f'Error key {key} not found.')
