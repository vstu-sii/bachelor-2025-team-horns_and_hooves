# Import all test cases to make them discoverable
from .test_forms_validation import *
from .test_views_extended import *
from .tests import *
from .tests_e2e import *
from .tests_plot import *
from .tests_tasks import *
from .tests_views_additional import *
from .test_error_handling import *

__all__ = [
    'test_forms_validation',
    'test_views_extended',
    'tests',
    'tests_e2e',
    'tests_plot',
    'tests_tasks',
    'tests_views_additional',
    'test_error_handling'
]
