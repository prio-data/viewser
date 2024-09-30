import numpy as np
from views_tensor_utilities import mappings

#from .models import Queryset, Column

#from viewser.commands.queryset.models import Queryset, Column


#def get_test_data(start_date, end_date):
#    qs_self_test = (Queryset("drift_detection_self_test", "country_month")

#                    .with_column(Column("ln_ged_ns", from_loa="country_month",
#                                        from_column="ged_ns_best_sum_nokgi")
#                                 .transform.ops.ln()
#                                 .transform.missing.fill()
#                                 )

#                    .with_column(Column("ln_ged_os", from_loa="country_month",
#                                        from_column="ged_os_best_sum_nokgi")
#                                 .transform.ops.ln()
#                                 .transform.missing.fill()
#                                 )

#                    .with_column(Column("ln_ged_sb", from_loa="country_month",
#                                        from_column="ged_sb_best_sum_nokgi")
#                                 .transform.ops.ln()
#                                 .transform.missing.fill()
#                                 )

#                    .with_column(Column("wdi_sp_pop_totl", from_loa="country_year",
#                                        from_column="wdi_sp_pop_totl")
#                                 .transform.missing.replace_na()
#                                 .transform.ops.ln()
#                                 )
#                    )

#    return qs_self_test.publish().fetch(start_date=start_date, end_date=end_date)


def perturbation_partitioner(tensor, index, test_partition_length, standard_partition_length):
    """
    partitioner

    Partition the input data tensor according to partitions in drift_config - for the purposes of
    perturbation, the beginning of the standard partition is the beginning of the dataset - otherwise
    datasets will be partitioned twice.

    """

    times = mappings.TimeUnits.from_pandas(index)

    tend = times.times[-1]
    tboundary = tend - test_partition_length
    tstart = times.times[0]

    tstart_index = times.time_to_index[tstart]
    tboundary_index = times.time_to_index[tboundary]
    tend_index = times.time_to_index[tend]

    standard_partition, test_partition = (tstart_index, tboundary_index), (tboundary_index, tend_index)

    standard_data = tensor[standard_partition[0]:standard_partition[1], :, :]
    test_data = tensor[test_partition[0]:test_partition[1], :, :]

    return standard_data, test_data


def get_random_indices(array, fraction=0.01):

    """
    Draw a random selection of indices pointing to locations in the input array

    """

    nsample = int(fraction*array.size)
    ncoord = len(array.shape)

    coords = []
    for icoord in range(ncoord):
        coord = []
        for sample in range(nsample):
            co = np.random.choice(array.shape[icoord])
            coord.append(co)
        coords.append(coord)

    return tuple(coords)


def perturb_global(data, what, **kwargs):

    """
    Perturb the whole input dataset so that it contains approximately (fraction) of (what)
    """

    fraction = kwargs['self_test']

    data_copy = data.copy()

    indices = get_random_indices(data_copy, fraction=fraction)

    data_copy[indices] = what

    return data_copy


def perturb_global_zero_fracs(data, **kwargs):

    what = 0.0

    perturbed_data = perturb_global(data, what, **kwargs)

    return perturbed_data


def perturb_global_nan_fracs(data, **kwargs):

    what = np.nan

    perturbed_data = perturb_global(data, what, **kwargs)

    return perturbed_data


def perturb_time(data, what, **kwargs):

    """
    Perturb a timestep so that it contains approximately (fraction) of (what)

    """

    fraction = kwargs['self_test']

    data_copy = data.copy()

    itime = int(data.shape[0] / 2)

    indices = get_random_indices(data_copy[itime, :, :], fraction=fraction)

    data_copy[itime, :, :][indices] = what

    return data_copy


def perturb_time_zero_fracs(data, **kwargs):

    what = 0.0

    perturbed_data = perturb_time(data, what, **kwargs)

    return perturbed_data


def perturb_time_nan_fracs(data, **kwargs):

    what = np.nan

    perturbed_data = perturb_time(data, what, **kwargs)

    return perturbed_data


def perturb_space(data, what, **kwargs):

    """
    Perturb a spatial unit so that it contains approximately (fraction) of (what)
    """

    fraction = kwargs['self_test']

    data_copy = data.copy()

    ispace = int(data.shape[1]/2)

    indices = get_random_indices(data_copy[:, ispace, :], fraction=fraction)

    data_copy[:, ispace, :][indices] = what

    return data_copy


def perturb_space_zero_fracs(data, **kwargs):

    what = 0.0

    perturbed_data = perturb_space(data, what, **kwargs)

    return perturbed_data


def perturb_space_nan_fracs(data, **kwargs):

    what = np.nan

    perturbed_data = perturb_space(data, what, **kwargs)

    return perturbed_data


def perturb_feature(data, what, **kwargs):

    """
    Perturb a feature so that it contains approximately (feature) of (what)
    """

    fraction = kwargs['self_test']

    data_copy = data.copy()

    ifeature = int(data.shape[2]/2)

    indices = get_random_indices(data_copy[:, :, ifeature], fraction=fraction)

    data_copy[:, :, ifeature][indices] = what

    return data_copy


def perturb_feature_zero_fracs(data, **kwargs):

    what = 0.0

    perturbed_data = perturb_feature(data, what, **kwargs)

    return perturbed_data


def perturb_feature_nan_fracs(data, **kwargs):

    what = np.nan

    perturbed_data = perturb_feature(data, what, **kwargs)

    return perturbed_data


def perturb_delta(data, what, whatever, **kwargs):

    """
    Perturb standard and test partitions so that the test partition has a substantially higher fraction of
    (what), filling in instances of (what) in the standard partition with (whatever)

    """

    index = kwargs['index']
    test_partition_length = kwargs['test_partition_length']
    standard_partition_length = kwargs['standard_partition_length']
    fraction = kwargs['self_test']

    data_copy = data.copy()

    standard, test = perturbation_partitioner(data_copy, index, test_partition_length, standard_partition_length)

    indices = get_random_indices(test, fraction=fraction)

    test[indices] = what

    indices = get_random_indices(standard, fraction=fraction)

    standard[indices] = whatever

    data_copy = np.concatenate((standard, test), axis=0)

    return data_copy


def perturb_delta_zeroes(data, **kwargs):

    what = 0.0

    whatever = 1.0

    perturbed_data = perturb_delta(data, what, whatever, **kwargs)

    return perturbed_data


def perturb_delta_completeness(data, **kwargs):

    what = np.nan

    whatever = 1.0

    perturbed_data = perturb_delta(data, what, whatever, **kwargs)

    return perturbed_data


def perturb_extreme_values(data, **kwargs):

    """
    Perturb the most extreme value in the test partition
    """

    index = kwargs['index']
    test_partition_length = kwargs['test_partition_length']
    standard_partition_length = kwargs['standard_partition_length']
    fraction = kwargs['self_test']

    data_copy = data.copy()

    standard, test = perturbation_partitioner(data_copy, index, test_partition_length, standard_partition_length)

    itime = int(test.shape[0]/2)

    ispace = int(test.shape[1]/2)

    ifeature = 0

    standard = np.nan_to_num(standard, nan=0.0, posinf=0.0, neginf=0.0)
    test = np.nan_to_num(test, nan=0.0, posinf=0.0, neginf=0.0)

    test_mean = np.nanmean(test[:, :, ifeature])

    test_std = np.nanstd(test[:, :, ifeature])

    test[itime, ispace, ifeature] = test_mean + (1 + fraction)*test_std

    data_copy = np.concatenate((standard, test), axis=0)

    return data_copy


def perturb_ks_drift(data, **kwargs):

    """
    Perturb the distribution of data in the test partition to a Normal, which is expected to be strongly
    different from the standard partition
    """

    index = kwargs['index']
    test_partition_length = kwargs['test_partition_length']
    standard_partition_length = kwargs['standard_partition_length']

    data_copy = data.copy()

    standard, test = perturbation_partitioner(data_copy, index, test_partition_length, standard_partition_length)

    ifeature = 0

    test = np.nan_to_num(test, nan=0.0, posinf=0.0, neginf=0.0)

    test_mean = np.mean(test[:, :, ifeature])

    test_std = np.std(test[:, :, ifeature])

    test[:, :, ifeature] = np.random.normal(test_mean, test_std, (test.shape[0], test.shape[1]))

    data_copy = np.concatenate((standard, test), axis=0)

    return data_copy


def perturb_ecod_drift(data, **kwargs):

    """
    Perturb the test partition by switching two very unlike features
    """

    index = kwargs['index']
    test_partition_length = kwargs['test_partition_length']
    standard_partition_length = kwargs['standard_partition_length']

    data_copy = data.copy()

    standard, test = perturbation_partitioner(data_copy, index, test_partition_length, standard_partition_length)

    f0copy = test[:, :, 0].copy()

    test[:, :, 0] = test[:, :, -1]
    test[:, :, -1] = f0copy

    data_copy = np.concatenate((standard, test), axis=0)

    return data_copy

