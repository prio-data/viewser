import numpy as np
import scipy
from views_tensor_utilities import objects, mappings
from . import config_drift as config
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

        results, translation_dict = self.test_function(
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

    def __init__(self, df, drift_config_dict=None):
        self.config_dict = drift_config_dict
        self.tensor_container = objects.ViewsDataframe(df).to_numpy_time_space()
        self.numeric_part = self.tensor_container.get_numeric_part()
        self.tensor = self.numeric_part.tensor
        self.index = self.tensor_container.index
        self.columns = self.numeric_part.columns

        self.default_config_dict = config.default_config_dict
        self.testers = []

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
