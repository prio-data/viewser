import numpy as np
from . import integrity_checks as ic

default_dne = -np.inf
default_missing = np.nan


default_config_dict = {

    'global_missingness':  {'threshold': 0.05,
                            'test_function': ic.get_global_nan_fracs,
                            'message': 'dataset missingness'},

    'time_missingness':    {'threshold': 0.01,
                            'test_function': ic.get_time_nan_fracs,
                            'message': 'time-unit missingness'},

    'space_missingness':   {'threshold': 0.03,
                            'test_function': ic.get_space_nan_fracs,
                            'message': 'space-unit missingness'},

    'feature_missingness': {'threshold': 0.01,
                            'test_function': ic.get_feature_nan_fracs,
                            'message': 'feature missingness'},

    'delta_completeness':  {'threshold': 1.25,
                            'test_function': ic.get_delta_completeness,
                            'message': 'feature delta_completeness'},

    'delta_zeroes':        {'threshold': 1.25,
                            'test_function': ic.get_delta_zeroes,
                            'message': 'feature delta_zeroes'},

    'ks_drift':            {'threshold': 100.,
                            'test_function': ic.get_ks_drift,
                            'message': 'feature KS drift'},

    'ecod_drift':          {'threshold': 0.05,
                            'test_function': ic.get_ecod_drift,
                            'message': 'dataset ECOD drift'},

    'standard_partition_length': 10,
    'test_partition_length': 1

    }
