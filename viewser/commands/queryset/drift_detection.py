import numpy as np
from views_tensor_utilities import objects, mappings
from . import config_drift as config
import datetime


class Alarm:
    def __repr__(self):
        return f"Alarm: {self.message} Severity: {self.severity} Timestamp: {self.timestamp}"

    def __str__(self):
        return f"Alarm: {self.message} Severity: {self.severity} Timestamp: {self.timestamp}"

    def __init__(self, message, severity=1):
        self.message = message
        self.severity = severity
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class InputGate:

    def __init__(self, df, drift_config_dict):
        self.config_dict = drift_config_dict
        self.tensor_container = objects.ViewsDataframe(df).to_numpy_time_space()
        self.numeric_part = self.tensor_container.get_numeric_part()
        self.tensor = self.numeric_part.tensor
        self.index = self.tensor_container.index
        self.columns = self.numeric_part.columns
        self.times = mappings.TimeUnits.from_pandas(self.index)
        self.spaces = mappings.SpaceUnits.from_pandas(self.index)
        self.uoa_mask = self.get_valid_uoa_mask()
        self.default_config_dict = self.get_default_config_dict()

    def get_valid_uoa_mask(self):
        """
        get_valid_uoa_mask

        Compute a boolean mask to mask out units-of-analysis which do not exist (e.g countries that do not exist
        in a given month)

        """

        return ~np.where(self.tensor == config.default_dne, True, False)

    def get_default_config_dict(self):

        return {
            'global_missingness':  0.05,
            'time_missingness':    0.01,
            'space_missingness':   0.03,
            'feature_missingness': 0.01,
            'delta_completeness':   1.25,
            'standard_partition_length': 10,
            'test_partition_length': 1

        }

    def test_global_nan_frac(self, threshold):
        """
        test_global_nan_frac

        Raise alarm if global missingness fraction exceeds threshold

        """

        if severity := (np.count_nonzero(np.isnan(self.tensor[self.uoa_mask]))/
                        np.count_nonzero(self.uoa_mask))/threshold > 1:
            return Alarm(f"Global missingness exceeded threshold {threshold}",
                         int(1+severity))
        else:
            return None

    def get_time_nan_fracs(self):
        """
        get_time_nan_fracs

        Compute missing fractions for all time units

        """

        time_nan_fracs = []
        nans = np.where(np.isnan(self.tensor), 1, 0)
        for itime in range(self.tensor.shape[0]):
            time_nan_fracs.append(
                              np.count_nonzero(nans[itime, :, :])/np.count_nonzero(self.uoa_mask[itime, :, :])
            )

        return np.array(time_nan_fracs)

    def test_time_nan_fracs(self, threshold):
        """
        test_time_nan_fracs

        Generate alarms for any time units whose missingness exceeds a threshold

        """

        results = self.get_time_nan_fracs()/threshold
        offenders = np.where(results>1)[0]

        if len(offenders) > 0:
            alarms = []
            for offender, severity in zip(offenders, results):
                al = Alarm(
                    f"Missingness for time unit {self.times.index_to_time[offender]} "
                    f"exceeded threshold {threshold}",
                    int(1+severity))
                alarms.append(al)

            return alarms
        else:
            return None

    def get_space_nan_fracs(self):
        """
        get_space_nan_fracs

        Compute missing fractions for all space units

        """

        space_nan_fracs = []
        nans = np.where(np.isnan(self.tensor), 1, 0)
        for ispace in range(self.tensor.shape[1]):
            space_nan_fracs.append(
                np.count_nonzero(nans[:, ispace, :]) / np.count_nonzero(self.uoa_mask[:, ispace, :])
            )

        return np.array(space_nan_fracs)

    def test_space_nan_fracs(self, threshold):
        """
        test_space_nan_fracs

        Generate alarms for any space units whose missingness exceeds a threshold

        """

        results = self.get_space_nan_fracs() / threshold
        offenders = np.where(results > 1)[0]

        if len(offenders) > 0:
            alarms = []
            for offender, severity in zip(offenders, results):
                al = Alarm(
                    f"Missingness for space unit {self.spaces.index_to_space[offender]} "
                    f"exceeded threshold {threshold}",
                    int(1+severity))
                alarms.append(al)

            return alarms
        else:
            return None

    def get_feature_nan_fracs(self):
        """
        get_feature_nan_fracs

        Compute missing fractions for all features

        """
        feature_nan_fracs = []
        nans = np.where(np.isnan(self.tensor), 1, 0)
        for ifeature in range(self.tensor.shape[2]):
            feature_nan_fracs.append(
                np.count_nonzero(nans[:, :, ifeature]) / np.count_nonzero(self.uoa_mask[:, :, ifeature])
            )

        return np.array(feature_nan_fracs)

    def test_feature_nan_fracs(self, threshold):
        """
        test_feature_nan_fracs

        Generate alarms for any features whose missingness exceeds a threshold

        """

        results = self.get_feature_nan_fracs() / threshold
        offenders = np.where(results > 1)[0]

        if len(offenders) > 0:
            alarms = []
            for offender, severity in zip(offenders, results):
                al = Alarm(
                    f"Missingness for feature {self.columns[offender]} "
                    f"exceeded threshold {threshold}",
                    int(1+severity))
                alarms.append(al)

            return alarms
        else:
            return None

    def get_delta_completeness(self):
        """
        get_delta_completeness

        Compute delta_completenesses for every feature with the specified standard (i.e. trustworthy) and test
        (untrustworthy) partitions.

        """

        delta_completenesses = []

        standard, test = self.partition()

        for ifeature in range(self.tensor.shape[2]):
            standard_nans = np.where(np.isnan(standard[:, :, ifeature]), 1, 0)
            test_nans = np.where(np.isnan(test[:, :, ifeature]), 1, 0)

            standard_uoa_mask = ~np.where(standard == config.default_dne, True, False)
            test_uoa_mask = ~np.where(test == config.default_dne, True, False)

            standard_nan_frac = np.count_nonzero(standard_nans)/(np.count_nonzero(standard_uoa_mask)+1e-20)
            test_nan_frac = np.count_nonzero(test_nans)/(np.count_nonzero(test_uoa_mask)+1e-20)

            delta_completenesses.append(np.abs(test_nan_frac-standard_nan_frac)/(standard_nan_frac+1e-20))

        return np.array(delta_completenesses)

    def test_delta_completeness(self, threshold):
        """
        test_delta_completeness

        Generate alarms for any features whose delta-completeness exceeds a threshold

        """

        results = self.get_delta_completeness()/threshold

        offenders = np.where(results > 1)[0]

        if len(offenders) > 0:
            alarms = []
            for offender, severity in zip(offenders, results):
                al = Alarm(
                    f"Delta-completeness for feature {self.columns[offender]} "
                    f"exceeded threshold {threshold}",
                    int(1+severity))
                alarms.append(al)

            return alarms
        else:
            return None

    def partition(self):
        """
        partitioner

        Partition the input data tensor according to partitions in drift_config

        """

        tend = self.times.times[-1]
        tboundary = tend - self.default_config_dict['test_partition_length']
        tstart = tboundary - self.default_config_dict['standard_partition_length']

        tstart_index = self.times.time_to_index[tstart]
        tboundary_index = self.times.time_to_index[tboundary]
        tend_index = self.times.time_to_index[tend]

        standard_partition, test_partition = (tstart_index, tboundary_index), (tboundary_index, tend_index)

        standard_data = self.tensor[standard_partition[0]:standard_partition[1], :, :]
        test_data = self.tensor[test_partition[0]:test_partition[1], :, :]

        return standard_data, test_data

    def assemble_alerts(self):
        """
        assemble_alerts

        Get lists of alerts generated by alert-generators

        """

        # override defaults

        for key in self.config_dict.keys():
            if key not in self.default_config_dict.keys():
                raise KeyError(f'missingness {key} not in allowed missingness types:'
                               f'{self.default_config_dict.keys()}')

            else:
                self.default_config_dict[key] = self.config_dict[key]

        alerts = []
        for key in self.default_config_dict.keys():
            if key in self.config_dict.keys():
                match key:
                    case 'global_missingness':
                        alerts.append(self.test_global_nan_frac(self.default_config_dict[key]))
                    case 'time_missingness':
                        alerts.append(self.test_time_nan_fracs(self.default_config_dict[key]))
                    case 'space_missingness':
                        alerts.append(self.test_space_nan_fracs(self.default_config_dict[key]))
                    case 'feature_missingness':
                        alerts.append(self.test_feature_nan_fracs(self.default_config_dict[key]))
                    case 'delta_completeness':
                        alerts.append(self.test_delta_completeness(self.default_config_dict[key]))

        return alerts
