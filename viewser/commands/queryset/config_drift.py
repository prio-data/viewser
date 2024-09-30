import numpy as np

default_dne = -np.inf
default_missing = np.nan

default_config_dict = {

    'global_missingness':  {'threshold': 0.05,
                            'test_function': 'global_nan_fracs',
                            'message': 'dataset missingness',
                            'self_test': 0.10},

    'global_zeros':        {'threshold': 0.75,
                            'test_function': 'global_zero_fracs',
                            'message': 'dataset zero',
                            'self_test': 0.999},

    'time_missingness':    {'threshold': 0.01,
                            'test_function': 'time_nan_fracs',
                            'message': 'time-unit missingness',
                            'self_test': 0.02},

    'space_missingness':   {'threshold': 0.03,
                            'test_function': 'space_nan_fracs',
                            'message': 'space-unit missingness',
                            'self_test': 0.06},

    'feature_missingness': {'threshold': 0.01,
                            'test_function': 'feature_nan_fracs',
                            'message': 'feature missingness',
                            'self_test': 0.02},

    'time_zeros':          {'threshold': 0.75,
                            'test_function': 'time_zero_fracs',
                            'message': 'time-unit zero',
                            'self_test': 0.9999},

    'space_zeros':         {'threshold': 0.95,
                            'test_function': 'space_zero_fracs',
                            'message': 'space-unit zero',
                            'self_test': 0.99},

    'feature_zeros':       {'threshold': 0.75,
                            'test_function': 'feature_zero_fracs',
                            'message': 'feature zero',
                            'self_test': 0.9999},

    'delta_completeness':  {'threshold': 1.01,
                            'test_function': 'delta_completeness',
                            'message': 'feature delta_completeness',
                            'self_test': 0.99},

    'delta_zeroes':        {'threshold': 1.01,
                            'test_function': 'delta_zeroes',
                            'message': 'feature delta_zeroes',
                            'self_test': 0.99},

    'extreme_values':      {'threshold': 4.0,
                            'test_function': 'extreme_values',
                            'message': 'feature extreme values',
                            'self_test': 8.0},

    'ks_drift':            {'threshold': 100.,
                            'test_function': 'ks_drift',
                            'message': 'feature KS drift',
                            'self_test': None},

    'ecod_drift':          {'threshold': 0.05,
                            'test_function': 'ecod_drift',
                            'message': 'dataset ECOD drift',
                            'self_test': None},

    'standard_partition_length': 10,
    'test_partition_length': 1,

    }
