import numpy as np
import pandas as pd
from views_transform_library import utilities
import config_drift as config
from ForecastDrift import alarm
class InputGate:

    def __init__(self, df):
        self.tensor = df_to_numpy(df)
        self.index = df.index
        self.columns = df.columns
        self.times, self.time_to_index, self.index_to_time = utilities.map_times(self.index)
        self.spaces, self.space_to_index, self.index_to_space = utilities.map_times(self.index)
        self.uoa_mask = self.get_valid_uoa_mask()

    def get_valid_uoa_mask(self):
        return ~np.where(self.tensor==-np.inf,True,False)

    def test_global_nan_frac(self):
        if severity:=(np.count_nonzero(np.isnan(self.tensor[self.uoa_mask]))/np.count_nonzero(self.uoa_mask))/config.threshold_global_nan_frac>1:
            return alarm.Alarm(f"Global missingness exceeded threshold {config.threshold_global_nan_frac}",int(severity))
        else:
            return None

    def get_time_nan_fracs(self):
        time_nan_fracs = []
        nans = np.where(np.isnan(self.tensor),1,0)
        for itime in range(self.tensor.shape[0]):
            time_nan_fracs.append(
                              np.count_nonzero(nans[itime,:,:])/np.count_nonzero(self.uoa_mask[itime,:,:])
            )

        return np.array(time_nan_fracs)

    def test_time_nan_fracs(self):

        results = self.get_time_nan_fracs()/config.threshold_time_unit_nan_frac
        offenders = np.where(results>1)

        if len(offenders) > 0:
            alarms = []
            for offender,severity in zip(offenders,results):
                al = alarm.Alarm(
                    f"Missingness for time unit {self.index_to_time[offender]} exceeded threshold {config.threshold_time_unit_nan_frac}",
                    int(severity))
                alarms.append(al)

            return alarms
        else:
            return None

    def get_space_nan_fracs(self):
        space_nan_fracs = []
        nans = np.where(np.isnan(self.tensor), 1, 0)
        for ispace in range(self.tensor.shape[1]):
            space_nan_fracs.append(
                np.count_nonzero(nans[:, ispace, :]) / np.count_nonzero(self.uoa_mask[:, ispace, :])
            )

        return np.array(space_nan_fracs)

    def test_space_nan_fracs(self):

        results = self.get_space_nan_fracs() / config.threshold_space_unit_nan_frac
        offenders = np.where(results > 1)

        if len(offenders) > 0:
            alarms = []
            for offender, severity in zip(offenders, results):
                al = alarm.Alarm(
                    f"Missingness for space unit {self.index_to_space[offender]} exceeded threshold {config.threshold_space_unit_nan_frac}",
                    int(severity))
                alarms.append(al)

            return alarms
        else:
            return None

    def get_feature_nan_fracs(self):
        feature_nan_fracs = []
        nans = np.where(np.isnan(self.tensor), 1, 0)
        for ifeature in range(self.tensor.shape[2]):
            feature_nan_fracs.append(
                np.count_nonzero(nans[:, :, ifeature]) / np.count_nonzero(self.uoa_mask[:, :, ifeature])
            )

        return np.array(feature_nan_fracs)

    def test_feature_nan_fracs(self):

        results = self.get_feature_nan_fracs() / config.threshold_feature_nan_frac
        offenders = np.where(results > 1)

        if len(offenders) > 0:
            alarms = []
            for offender, severity in zip(offenders, results):
                al = alarm.Alarm(
                    f"Missingness for feature {self.columns[offender]} exceeded threshold {config.threshold_feature_nan_frac}",
                    int(severity))
                alarms.append(al)

            return alarms
        else:
            return None

    def get_delta_completeness(self):
        delta_completenesses = []
        standard_partition, test_partition = self.partitioner()
        standard, test = self.partition(standard_partition, test_partition)

        for ifeature in range(self.tensor.shape[2]):
            standard_nans = np.where(np.isnan(standard[:,:,ifeature]), 1, 0)
            test_nans = np.where(np.isnan(test[:,:,ifeature]), 1, 0)
            standard_uoa_mask = ~np.where(standard==-np.inf,True,False)
            test_uoa_mask = ~np.where(test==-np.inf,True,False)

            standard_nan_frac = np.count_nonzero(standard_nans)/np.count_nonzero(standard_uoa_mask)
            test_nan_frac = np.count_nonzero(test_nans)/np.count_nonzero(test_uoa_mask)

            delta_completenesses.append(np.abs(test_nan_frac-standard_nan_frac)/standard_nan_frac+1e-20)

        return np.array(delta_completenesses)

    def test_delta_completeness(self):

        results = self.get_delta_completeness()/config.threshold_delta
        offenders = np.where(results > 1)

        if len(offenders) > 0:
            alarms = []
            for offender, severity in zip(offenders, results):
                al = alarm.Alarm(
                    f"Delta-completeness for feature {self.columns[offender]} exceeded threshold {config.threshold_delta}",
                    int(severity))
                alarms.append(al)

            return alarms
        else:
            return None


    def partitioner(self):
        tend = self.times[-1]
        tboundary = tend - config.test_partition_length
        tstart = tboundary - config.standard_partition_length

        return (tstart,tboundary), (tboundary, tend)

    def partition(self, standard_partition, test_partition):

        standard_data = self.tensor[standard_partition[0]:standard_partition[1], :, :]
        test_data = self.tensor[test_partition[0]:test_partition[1], :, :]

        return standard_data, test_data


    def assemble_alerts(self):
        alerts = []
        alerts.append(self.test_global_nan_frac())
        alerts.append(self.test_time_nan_fracs())
        alerts.append(self.test_space_nan_fracs())
        alerts.append(self.test_feature_nan_fracs())
        alerts.append(self.test_delta_completeness())

        return alerts

def df_to_numpy(df):
    """
    df: dataframe to be tensorised

    this_hash: fileneme corresponding to hash of column's path

    """

    index = df.index
    time_indices = index.levels[0].to_list()
    space_indices = index.levels[1].to_list()

    original_index_tuples = index.to_list()
    original_values = df.values

    nrow = len(original_index_tuples)

    ntime = len(time_indices)
    nspace = len(space_indices)
    nfeature = len(df.columns)

    if nrow != ntime * nspace:

        if df[df == -np.inf].count() > 0:
            raise RuntimeError(f'Default does-not-exist token {-np.inf} found in input data')

        tensor = np.full((ntime, nspace, nfeature), -np.inf)

        for irow in range(len(original_index_tuples)):
            idx = original_index_tuples[irow]
            itime = time_indices.index(idx[0])
            ispace = space_indices.index(idx[1])
            tensor[itime, ispace, :] = original_values[irow]

    else:
        tensor = utilities.df_to_tensor_strides(df)

    return tensor
