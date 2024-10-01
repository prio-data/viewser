import numpy as np
from views_tensor_utilities import objects, mappings
from . import config_drift as config
from . import integrity_checks as ic
from . import self_test as st
#import viewser.commands.queryset.models.self_test_data as std
import datetime


class InputAlarm:
    def __repr__(self):
        return f"Input alarm: {self.message} Severity: {self.severity} Timestamp: {self.timestamp}\n"

    def __str__(self):
        return f"Input alarm: {self.message} Severity: {self.severity} Timestamp: {self.timestamp}\n"

    def __init__(self, message, severity=1):
        self.message = message
        self.severity = severity
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Tester:

    """
    Tester

    Class that mediates between the InputGate class and the testing functions. Brings together the relevant
    test function, the partitions, the threshold, the message describing the test in the alarms, and the input data
     - tensor, index, and feature names (required for useful reporting in the alarms)

    """

    def __init__(self, test_function=None,
                 test_partition_length=1,
                 standard_partition_length=1,
                 threshold=0,
                 message='',
                 data=None,
                 index=None,
                 features=None,
                 ):

        self.test_function = test_function
        self.test_partition_length = test_partition_length
        self.standard_partition_length = standard_partition_length
        self.threshold = threshold
        self.message = message
        self.data = data
        self.index = index
        self.features = features

    def generate_alarms(self):

        """
        generate alarms

        Calls the object's assigned testing function with a kwarg dict that the function picks and chooses from
        as needed.
        The function returns an array of results and a dictionary translating the indexes of the results in the
        array into units of analysis or features for reporting in the alarms.

        """

#        print(self.test_function,self.test_partition_length,self.standard_partition_length,self.data.shape,
#              self.features)

        results, translation_dict = getattr(ic, self.test_function)(
                                              tensor=self.data,
                                              index=self.index,
                                              features=self.features,
                                              test_partition_length=self.test_partition_length,
                                              standard_partition_length=self.standard_partition_length)

        results /= self.threshold

        try:
            offenders = np.where(results > 1)[0]
            severities = results[offenders]
        except:

            return None

        if len(offenders) > 0:
            alarms = []
            for offender, severity in zip(offenders, severities):
                if translation_dict is not None:
                    offender_id = translation_dict[offender]
                else:
                    offender_id = offender

                al = InputAlarm(
                    f"{self.message}; offender: {offender_id}, "
                    f"threshold: {self.threshold}",
                    int(1+severity))
                alarms.append(al)

            return alarms
        else:
            return f"{self.message} passed"


class InputGate:

    """
    InputGate

    Class which superintends the input warning machinery. Accepts a dataframe containing the data to be examined
    and a configuration dictionary which users can use to override the default settings in config_drift.

    The df is converted to a tensor container and non-numeric parts of the data are stripped out.

    """

    def __init__(self, df, drift_config_dict=None, self_test=False, self_test_data=None):
        self.config_dict = drift_config_dict
        self.default_config_dict = config.default_config_dict

        if self_test:
            self.__self_test(self_test_data)

        self.tensor_container = (objects.ViewsDataframe(df, split_strategy='float_string', cast_strategy='to_64').
                                 to_numpy_time_space())
        self.numeric_part = self.tensor_container.get_numeric_views_tensors()[0]
        self.tensor = self.numeric_part.tensor
        self.index = self.tensor_container.index
        self.columns = self.numeric_part.columns

        self.testers = []

    def __self_test(self, self_test_data):

        """
        ___self_test

        Method driving the self-test machinery for the drift detection system

        A standard dataframe is fetched and custom perturbation functions, one per integrity-checking function, are
        called upon to perturb the standard data in ways designed to trigger alerts from the drift-detector.
        Perturbed data is passed to the Tester method as normal and alerts are collected.
        By design, all integrity checks should be failed. If this is not the case, it implies a problem with one
        or more of the integrity-checking routines, or with the input data, which must be investigated.

        """

        self_test_container = (objects.ViewsDataframe(self_test_data,
                                                      split_strategy='float_string',
                                                      cast_strategy='to_64').to_numpy_time_space())

        self_test_index = self_test_container.index
        self_test_features = self_test_container.get_numeric_views_tensors()[0].columns

        self_test_data = self_test_container.get_numeric_numpy_tensors()[0]

        testers = []

        for key in self.config_dict.keys():
            try:

                self_test_dict = self.default_config_dict[key]

                self_test_dict['index'] = self_test_index

                self_test_dict['test_partition_length'] = self.config_dict['test_partition_length']

                self_test_dict['standard_partition_length'] = self.config_dict['standard_partition_length']

                perturbed_self_test_data = getattr(st, 'perturb_'+self_test_dict['test_function'])(self_test_data,
                                                                                                   **self_test_dict)

                testers.append(Tester(test_function=self_test_dict['test_function'],
                                      test_partition_length=self.config_dict['test_partition_length'],
                                      standard_partition_length=self.config_dict['standard_partition_length'],
                                      threshold=self_test_dict['threshold'],
                                      message=self_test_dict['message'],
                                      data=perturbed_self_test_data,
                                      index=self_test_index,
                                      features=self_test_features,
                                      ))

            except:
                pass

        alerts = [tester.generate_alarms() for tester in testers]

        failures = []
        for alert in alerts:
            if 'passed' in str(alert):
                failures.append(str(alert))

        if len(failures) > 0:
            raise RuntimeError(f'drift-detection self test failed: {failures}')
        else:
            print(f'Drift-detection self test passed')

    def assemble_alerts(self):
        """
        assemble_alerts

        Method which compares the default configuration dictionary with that supplied when the InputGate object is
        instantiated, removes test functions that are not required and updates thresholds of those requested.

        The resulting configuration dictionary is then used to generate a list of Tester objects, whose
        generate_alarm methods are then called in sequence.

        """

        # override defaults
        if self.config_dict is None:
            self.config_dict = self.default_config_dict
        else:
            for key in self.default_config_dict.keys():
                if key in self.config_dict.keys():
                    try:
                        detector_dict = self.default_config_dict[key]
                        detector_dict['threshold'] = self.config_dict[key]['threshold']
                        self.config_dict[key] = detector_dict
                    except:
                        pass
                else:
                    try:
                        _ = self.default_config_dict[key]['threshold']
                    except:
                        self.config_dict[key] = self.default_config_dict[key]

        testers = []
        for key in self.config_dict.keys():
            try:
                tester_dict = self.config_dict[key]
                testers.append(Tester(test_function=tester_dict['test_function'],
                                      test_partition_length=self.config_dict['test_partition_length'],
                                      standard_partition_length=self.config_dict['standard_partition_length'],
                                      threshold=tester_dict['threshold'],
                                      message=tester_dict['message'],
                                      data=self.tensor,
                                      index=self.index,
                                      features=self.columns,
                                      ))
            except:
                pass

        return [tester.generate_alarms() for tester in testers]
