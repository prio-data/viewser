import numpy as np
from . import config_drift as config
from views_tensor_utilities import mappings
import scipy
from pyod.models.ecod import ECOD


def get_valid_uoa_mask(tensor):
    """
    get_valid_uoa_mask

    Compute a boolean mask to mask out units-of-analysis which do not exist (e.g countries that do not exist
    in a given month)

    """

    return ~np.where(tensor == config.default_dne, True, False)


def partitioner(tensor, index, test_partition_length, standard_partition_length):

    """
    partitioner

    Partition the input data tensor according to partitions in drift_config

    """

    times = mappings.TimeUnits.from_pandas(index)

    tend = times.times[-1]
    tboundary = tend - test_partition_length
    tstart = tboundary - standard_partition_length

    tstart_index = times.time_to_index[tstart]
    tboundary_index = times.time_to_index[tboundary]
    tend_index = times.time_to_index[tend]

    standard_partition, test_partition = (tstart_index, tboundary_index), (tboundary_index, tend_index)

    standard_data = tensor[standard_partition[0]:standard_partition[1], :, :]
    test_data = tensor[test_partition[0]:test_partition[1], :, :]

    return standard_data, test_data


def global_nan_fracs(**kwargs):

    tensor = kwargs['tensor']

    uoa_mask = get_valid_uoa_mask(tensor)

    results = np.count_nonzero(np.isnan(tensor[uoa_mask]))/np.count_nonzero(uoa_mask)

    return np.array([results, 0.0]), None


def global_zero_fracs(**kwargs):

    tensor = kwargs['tensor']

    uoa_mask = get_valid_uoa_mask(tensor)

    results = 1. - np.count_nonzero(tensor[uoa_mask])/np.count_nonzero(uoa_mask)

    return np.array([results, 0.0]), None


def time_nan_fracs(**kwargs):
    """
    time_nan_fracs

    Compute missing fractions for all time units

    """

    tensor = kwargs['tensor']
    index = kwargs['index']

    times = mappings.TimeUnits.from_pandas(index)

    uoa_mask = get_valid_uoa_mask(tensor)

    time_nan_fracs = []
    nans = np.where(np.isnan(tensor), 1, 0)
    for itime in range(tensor.shape[0]):
        time_nan_fracs.append(np.count_nonzero(nans[itime, :, :])/np.count_nonzero(uoa_mask[itime, :, :]))

    return np.array(time_nan_fracs), times.index_to_time


def space_nan_fracs(**kwargs):
    """
    space_nan_fracs

    Compute missing fractions for all space units

    """

    tensor = kwargs['tensor']
    index = kwargs['index']

    spaces = mappings.SpaceUnits.from_pandas(index)

    uoa_mask = get_valid_uoa_mask(tensor)

    space_nan_fracs = []
    nans = np.where(np.isnan(tensor), 1, 0)
    for ispace in range(tensor.shape[1]):
        space_nan_fracs.append(np.count_nonzero(nans[:, ispace, :]) / np.count_nonzero(uoa_mask[:, ispace, :]))

    return np.array(space_nan_fracs), spaces.index_to_space


def feature_nan_fracs(**kwargs):
    """
    feature_nan_fracs

    Compute missing fractions for all features

    """

    tensor = kwargs['tensor']
    index_to_feature = {}
    for ifeature, feature in enumerate(kwargs['features']):
        index_to_feature[ifeature] = feature

    uoa_mask = get_valid_uoa_mask(tensor)

    feature_nan_fracs = []
    nans = np.where(np.isnan(tensor), 1, 0)
    for ifeature in range(tensor.shape[2]):
        feature_nan_fracs.append(np.count_nonzero(nans[:, :, ifeature]) / np.count_nonzero(uoa_mask[:, :, ifeature]))

    return np.array(feature_nan_fracs), index_to_feature


def time_zero_fracs(**kwargs):
    """
    time_nan_fracs

    Compute missing fractions for all time units

    """

    tensor = kwargs['tensor']
    index = kwargs['index']

    times = mappings.TimeUnits.from_pandas(index)

    uoa_mask = get_valid_uoa_mask(tensor)

    time_zero_fracs = []

    for itime in range(tensor.shape[0]):
        time_zero_fracs.append(1. - np.count_nonzero(tensor[itime, :, :])/np.count_nonzero(uoa_mask[itime, :, :]))

    return np.array(time_zero_fracs), times.index_to_time


def space_zero_fracs(**kwargs):
    """
    get_space_nan_fracs

    Compute missing fractions for all space units

    """

    tensor = kwargs['tensor']
    index = kwargs['index']

    spaces = mappings.SpaceUnits.from_pandas(index)

    uoa_mask = get_valid_uoa_mask(tensor)

    space_zero_fracs = []

    for ispace in range(tensor.shape[1]):
        space_zero_fracs.append(1. - np.count_nonzero(tensor[:, ispace, :]) / np.count_nonzero(uoa_mask[:, ispace, :]))

    return np.array(space_zero_fracs), spaces.index_to_space


def feature_zero_fracs(**kwargs):
    """
    get_feature_nan_fracs

    Compute missing fractions for all features

    """

    tensor = kwargs['tensor']
    index_to_feature = {}
    for ifeature, feature in enumerate(kwargs['features']):
        index_to_feature[ifeature] = feature

    uoa_mask = get_valid_uoa_mask(tensor)

    feature_zero_fracs = []

    for ifeature in range(tensor.shape[2]):
        feature_zero_fracs.append(1. - np.count_nonzero(tensor[:, :, ifeature]) /
                                  np.count_nonzero(uoa_mask[:, :, ifeature]))

    return np.array(feature_zero_fracs), index_to_feature


def delta_completeness(**kwargs):
    """
    get_delta_completeness

    Compute delta_completenesses for every feature with the specified standard (i.e. trustworthy) and test
    (untrustworthy) partitions.

    """

    tensor = kwargs['tensor']
    index = kwargs['index']
    test_partition_length = kwargs['test_partition_length']
    standard_partition_length = kwargs['standard_partition_length']
    index_to_feature = {}
    for ifeature, feature in enumerate(kwargs['features']):
        index_to_feature[ifeature] = feature

    delta_completenesses = []

    standard, test = partitioner(tensor, index, test_partition_length, standard_partition_length)

    for ifeature in range(tensor.shape[2]):
        standard_nans = np.where(np.isnan(standard[:, :, ifeature]), 1, 0)
        test_nans = np.where(np.isnan(test[:, :, ifeature]), 1, 0)

        standard_uoa_mask = ~np.where(standard == config.default_dne, True, False)
        test_uoa_mask = ~np.where(test == config.default_dne, True, False)

        standard_nan_frac = np.count_nonzero(standard_nans)/(np.count_nonzero(standard_uoa_mask)+1e-20)
        test_nan_frac = np.count_nonzero(test_nans)/(np.count_nonzero(test_uoa_mask)+1e-20)

        delta_completenesses.append(np.abs(test_nan_frac-standard_nan_frac)/(standard_nan_frac+1e-20))

    return np.array(delta_completenesses), index_to_feature


def delta_zeroes(**kwargs):
    """
    get_delta_zeroes

    Compute delta in zero-fraction for every feature with the specified standard (i.e. trustworthy) and test
    (untrustworthy) partitions.

    """

    tensor = kwargs['tensor']
    index = kwargs['index']
    test_partition_length = kwargs['test_partition_length']
    standard_partition_length = kwargs['standard_partition_length']
    index_to_feature = {}
    for ifeature, feature in enumerate(kwargs['features']):
        index_to_feature[ifeature] = feature

    delta_zeroes = []

    standard, test = partitioner(tensor, index, test_partition_length, standard_partition_length)

    for ifeature in range(tensor.shape[2]):
        standard_zeroes = np.where(standard[:, :, ifeature] == 0, 1, 0)
        test_zeroes = np.where(test[:, :, ifeature] == 0, 1, 0)

        standard_uoa_mask = ~np.where(standard == config.default_dne, True, False)
        test_uoa_mask = ~np.where(test == config.default_dne, True, False)

        standard_zero_frac = np.count_nonzero(standard_zeroes)/(np.count_nonzero(standard_uoa_mask)+1e-20)
        test_zero_frac = np.count_nonzero(test_zeroes)/(np.count_nonzero(test_uoa_mask)+1e-20)

        delta_zeroes.append(np.abs(test_zero_frac-standard_zero_frac)/(standard_zero_frac+1e-20))

    return np.array(delta_zeroes), index_to_feature


def extreme_values(**kwargs):

    tensor = kwargs['tensor']
    index = kwargs['index']
    test_partition_length = kwargs['test_partition_length']
    standard_partition_length = kwargs['standard_partition_length']
    index_to_feature = {}
    for ifeature, feature in enumerate(kwargs['features']):
        index_to_feature[ifeature] = feature

    extreme_values = []

    standard, test = partitioner(tensor, index, test_partition_length, standard_partition_length)
    standard_non_zero = np.where(np.logical_or(standard == config.default_dne, np.isnan(standard)), np.nan, standard)

#    print(standard_partition_length,test_partition_length)
#    print('tester',standard.shape,test.shape,tensor.shape)

    for ifeature in range(tensor.shape[2]):

        standard_mean_non_zero = np.nanmean(standard_non_zero[:, :, ifeature])
        standard_sigma_non_zero = np.nanstd(standard_non_zero[:, :, ifeature])

#        print(test[:, :, ifeature].shape)

        test_max = np.max(test[:, :, ifeature])

        extreme_values.append(abs(test_max - standard_mean_non_zero)/(standard_sigma_non_zero + 1e-20))

    return np.array(extreme_values), index_to_feature


def ks_drift(**kwargs):

    """
    get_ks_drift

    Function which uses a two-sample Kolmogorov-Smirnoff test to determine the probability (in the sense of an
    hypothesis test) that the data in the test partition and standard partition are drawn from the same
    underlying distribution (regardless of what that distribution might be).

    To harmonise functionality with the rest of the testing machinery, what is returned is 1/(p_value), so that
    large numbers represent likely divergence between the test and standard data.

    Only the distribution of non-zero values is tested. If either partition contains only zeros, a very large
    dummy value is returned as a test result.

    """

    tensor = kwargs['tensor']
    index = kwargs['index']
    test_partition_length = kwargs['test_partition_length']
    standard_partition_length = kwargs['standard_partition_length']
    index_to_feature = {}
    for ifeature, feature in enumerate(kwargs['features']):
        index_to_feature[ifeature] = feature

    ks_pvalues = []

    standard, test = partitioner(tensor, index, test_partition_length, standard_partition_length)

    for ifeature in range(tensor.shape[2]):

        standard_feature = standard[:, :, ifeature]
        test_feature = test[:, :, ifeature]

        standard_feature = standard_feature[standard_feature > 0]
        test_feature = test_feature[test_feature > 0]

        if len(standard_feature) == 0 or len(test_feature) == 0:
            ks_pvalues.append(1e10)
        else:
            ks_pvalues.append(1./scipy.stats.ks_2samp(standard_feature, test_feature).pvalue)

    return np.array(ks_pvalues), index_to_feature


def ecod_drift(**kwargs):

    """
    get_ecod_drift

    Function that uses outlier detection (Empirical Cumulative Distribution functions) to detect drift
    between the standard and test partitions. This test can be done simultaneously on the entire
    (time x space * feature) datacube.

    An outlier model is generated for the standard partition, which will contains a fraction of examples
    labelled as outliers.

    The same model is then used to label the examples in the test partition and the fraction of outliers
    compared with that in the standard partition. A substantial difference between these two outlier
    fractions is taken to indicate possible inconsistency between the partitions.

    """

    tensor = kwargs['tensor']
    index = kwargs['index']

    test_partition_length = kwargs['test_partition_length']
    standard_partition_length = kwargs['standard_partition_length']

    ecod_drifts = []

    standard, test = partitioner(tensor, index, test_partition_length, standard_partition_length)

    # rearrange tensors to panels

    standard_panel = standard.reshape(-1, standard.shape[-1])
    test_panel = test.reshape(-1, test.shape[-1])

    # eliminate NaNs

    standard_panel = standard_panel[~np.isnan(standard_panel).any(axis=1)]
    test_panel = test_panel[~np.isnan(test_panel).any(axis=1)]

    # eliminate +/- Infs

    standard_panel = standard_panel[np.isfinite(standard_panel).any(axis=1)]
    test_panel = test_panel[np.isfinite(test_panel).any(axis=1)]

    clf = ECOD()
    clf.fit(standard_panel)
    standard_labels = clf.labels_
    outlier_fraction_standard = np.count_nonzero(standard_labels)/len(standard_labels)

    test_labels = clf.predict(test_panel)
    outlier_fraction_test = np.count_nonzero(test_labels)/len(test_labels)

    ecod_drifts.append(abs(outlier_fraction_test - outlier_fraction_standard)/(outlier_fraction_standard + 1e-20))

    ecod_drifts.append(0.0)

    return np.array(ecod_drifts), None
