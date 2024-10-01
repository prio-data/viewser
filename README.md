
# viewser

Viewser is a software package allowing any user to fetch raw data from the VIEWS database, apply a wide range 
of transforms to the raw data, and download the resulting dataset as a single pandas dataframe.
The following documentation refers to viewser v>=6.0.0. This is a major update to viewser. Principal changes from
older versions of viewser are

- data is now fetched from the database hosted on new dedicated hardware hosted at PRIO
- the API which fetches data has been changed - users no longer specify the table from which raw data is 
fetched, only the level of analysis. 

## Installing viewser

Viewser is a python package and it is strongly advised that it be installed in a conda enviroment. Viewser itself 
is not available on conda and can only be installed via pip

`pip install viewser`

## Configuration

The tool is configured using the `viewser config set KEY VALUE` and `viewser
config load JSON` commands. The settings shown without defaults here, or with
defaults that don't make sense for the average user (`REMOTE_URL`) must be
configured before use.

|Setting                          |Description                                        |Default            |
|---------------------------------|---------------------------------------------------|-------------------|
|RETRY_FREQUENCY                  |General request retry frequency in seconds         |5                  |
|QUERYSET_MAX_RETRIES             |How many times a queryset is queried before failing|500                |
|LOG_LEVEL                        |Determines what logging messages are shown         |INFO               |
|ERROR_DUMP_DIRECTORY             |Determines where error dumps are written to        |~/.views/dumps     |
|REMOTE_URL                       |URL of a views 3 instance                          |http://0.0.0.0:4000|
|MODEL_METADATA_DATABASE_HOSTNAME |Hostname of database for storing model metadata    |hermes             |
|MODEL_METADATA_DATABASE_NAME     |DBname of database for storing model metadata      |forecasts3         |
|MODEL_METADATA_DATABASE_USER     |Username for database for storing model metadata   |Inferred from cert |
|MODEL_METADATA_DATABASE_SSLMODE  |SSLmode for database for storing model metadata    |required           |
|MODEL_METADATA_DATABASE_PORT     |Port of database for storing model metadata        |5432               |
|MODEL_METADATA_DATABASE_SCHEMA   |Schema of database for storing model metadata      |forecasts          |
|MODEL_METADATA_DATABASE_TABLE    |Table of database for storing model metadata       |model              |
|AZURE_BLOB_STORAGE_ACCOUNT_NAME  |Name of Azure blob storage account                 |                   |
|AZURE_BLOB_STORAGE_ACCOUNT_KEY   |Access key of Azure blob storage account           |                   |

## Usage

The viewser client can be used in two ways:

## Via command-line interface (CLI)

`viewser` functionality is exposed via a CLI on your system after installation.
An overview of available commands can be seen by running `viewser --help`.

The CLI is envisaged mainly as a tool to help users with issues such as selecting appropriate transforms, exploring the database, determining the level of analysis of a given feature, etc.

## Useful commands

Show all features in the database:

`viewser features list <loa>`

with <loa> being one of ['pgm', 'cm', 'pgy', 'cy', 'pg', 'c', 'am', 'a', 'ay', 'm', 'y']

Show all transforms sorted by level of analysis:

`viewser transforms list`

Show all transforms available at a particular level of analysis:

`viewser transforms at_loa <loa>`

with <loa> being one of ['any', 'country_month', 'priogrid_month', 'priogrid_year']

Show docstring for a particular transform:

`viewser transforms show <transform-name>`

List querysets stored in the queryset database:

`viewser queryset list`

Produce code required to generate a queryset

`viewser queryset show <queryset-name>`

## Via API

The full functionality of viewser is exposed via its API for use in scripts and notebooks

The two fundamental objects used to define what data is fetched by the client are the *Queryset* and the *Column*, where a 
Queryset consists of one or more Columns. 

### Defining a new queryset from scratch

To define a queryset, one first imports the Queryset and Column classes

`from viewser import Queryset, Column`

A new queryset is then created by 

`new_queryset = (Queryset("queryset_name", "level of analysis"))`

Every queryset must have

- a (meaningful) name.
- a level of analysis. This defines the level of analysis that all columns in the queryset will be aggregated/disaggregated to, and therefore the level of analysis at which the final dataset will be presented.

The level of analysis must be a string of the form spatial-unit`_`time-unit, where the spatial-unit must be one of

- country
- priogrid

and the time unit must be one of 

- month
- year

Column objects representing data are added to the queryset using the `with_column` method:

    new_queryset = (Queryset("simple_conflict", "country_month")

               .with_column(Column("ged_sb", from_loa="country_month", from_column="ged_sb_best_sum_nokgi")
                            )
                )

Each call to `with_column` takes a single Column instance as its argument.

The Column instance in turn defines what the column is to be called and what data will go into it. The first argument to the Column instance is the column name. This again should be meaningful. 

Note that, unlike older versions of viewser (<6.0.0), all column names in a queryset *must* be unique. If two or more columns are given the same name, the queryset will be rejected by the server and an error massage detailing which columns have repeated names will be returned.

The second argument to the Column instance `from_loa` specifies which level of analysis the requested raw data is defined at. If the user does not know this, they need to examine the database using the viewser CLI. 

If the wrong loa is specified, the queryset will be rejected by the server and an error message detailing which columns have been requested from the wrong loa will be returned.

The final argument to the Column instance is the name of the raw column to be fetched from the database. If a non-existant column is requested, the queryset will be rejected by the server and an error message detailing which columns are unavailable will be returned.

#### Aggregation/disaggregation

The definition of a queryset must include the *target* level of analysis, at which the resulting data will be presented to the user.

The definition of each column in a queryset must specify the *source* level of analysis, at which the raw data used to define that column is stored in the database.

If these loas differ for a given column, the necessary aggregation or disaggregation is performed automatically.

If an `aggregation` is required, the user may choose from the following aggregation functions:

- `sum` (default): sums over necessary spatial and time units
- `avg`: averages over necessary spatial and time units
- `max`: takes the maximum value over necessary spatial and time units
- `min`: takes the minimum value over necessary spatial and time units
- `count`: counts non-zero values over necessary spatial and time units

*If no aggregation function is specified but aggregation is required, the default choice (sum) will be automatically (and silently) selected.*

It is up to users to ensure that they select the correct aggregation functions. If something other than the default is required, an aggregation function can be specified by 

    new_queryset = (Queryset("simple_conflict", "country_month")

               .with_column(Column("ged_sb", from_loa="country_month", from_column="ged_sb_best_sum_nokgi")
                            .aggregate('avg')
                           )
                   )

If a non-existent aggregation function is specified, the queryset will be rejected by the server and an error message detailing which columns have incorrect aggregation functions will be returned.

#### Transforms

Any queryset column may specify an arbitrary number of transforms to be done to the raw data *after* any necessary aggregation/disaggregation has been done.

Transforms are added to columns using the `transform` method

    new_queryset = (Queryset("simple_conflict", "country_month")

               .with_column(Column("ged_sb", from_loa="country_month", from_column="ged_sb_best_sum_nokgi")
                            .aggregate('avg')
                            .transform.ops.ln()
                            .transform.missing.replace_na()
                           )          
                   )

Each transform method has a general transform type, e.g. `missing` followed by a specific function with brackets for arguments.

A list of available transforms can be obtained using the viewser CLI. A notebook giving examples of what each transform does can be found at https://github.com/prio-data/views3/tree/master/examples.

Note that not all transforms are available at all levels of analysis. If a transform is requested at an innapproprite loa, the queryset will be rejected by the server and an error message detailing which columns have requested incompatible transforms and loas will be returned.

### Making a new queryset by merging two or more existing querysets

It is sometimes desirable to make a larger queryset by merging several existing querysets. This can be done with the from_merger method. The method requires at mininum a list of querysets to be merged and a name for the merged queryset. Optionally, a theme and description can also be passed. There is also a boolean verbose flag, described below.
For example
    
    querysets_to_merge = ['queryset1','querysets2','queryset3']
    merged_queryset = Queryset.from_merger(querysets_to_merge,'my_merged_queryset',theme='my_theme',description='description')

Before merging, some checks are performed. The querysets to be merged must all have the same target LOA. If the querysets to be merged contain two or more columns with the same name, the method checks that all the definitions of that column are exactly the same (same raw data, same transforms with same parameters). If this is the case, one copy of this column is included in the merged queryset (if the verbose flag is True, the method reports that this has been done). If there are multiple definitions of the columns with the same column name, the attempt at merging is aborted.

### Recreating a queryset from storage

If a queryset has already been published to the queryset store (see below), the queryset object can be regenerated by doing

    queryset = Queryset.from_storage(queryset_name)

### Publising a queryset

Before a new queryset (written from scratch or created by merging existing querysets) can be fetched, it must be published to a permanent database on the server. This is done using the `publish()` method:

    data = new_queryset.publish()

### Fetching a queryset

A published queryset can be fetched using the `.fetch()` method

    data = new_queryset.fetch()

which can also be chained with the `publish()` method:

    data = new_queryset.publish().fetch()

Communication between the viewser client and the server is by a simple polling model. The client sends the queryset to the server again and again with a pause (currently 5 seconds) between each send.

Each time, the server responds with one of 

- a status message informing the user of progress on computing their queryset
- an error message detailing something that has gone wrong
- a compressed completed dataset

The fetch process proceeds as follows:

(i) At the first request, the server enters the queryset into a temporary database of 'in-progress' querysets that it is currently working on. Querysets are removed from this database if they cause an error to be generated, or once the completed dataset has been sent to the client.

(ii) Once the queryset has been entered into the temporary database, it is validated to check that, e.g. no non-existent database columns, aggregation functions or transforms have been requested. If this is the case, an error message is sent back to the client and the queryset is deleted from the 'in-progress' database.

(iii) If the queryset passes validation, the server compares the requested columns with what is in its cache to see if some or all of some or all of the columns have already been computed. Already computed columns are not computed again, and partially computed columns are 'pruned' of stages that are already in the cache, so that work is not repeated.

(iv) If raw data needs to be fetched from the database, a job is dispatched to a database queue, which fetches the missing raw data to the cache. While this is in progress, the server returns status messages to the client detailing whether the database fetch is still waiting in the queue, or its progress if the fetch has started.

(v) Once all necessary raw data is in the cache, any transforms that remain to be done are dispatched to a transform queue. During this phase, status messages are returned to the client detailing whether the transforms have been started, and what their progress is.

If errors are encountered during the database fetch or transform stages, an error message is returned to the client and the queryset is removed from the 'in-progress' database.

(vi) Otherwise, all completed queryset columns are written to the cache, then assembled into a single pandas dataframe, which is compressed into parquet format and sent back to the client. The queryset is removed from the 'in-progress' database.

Note that priogrid-level dataframes, even compressed, can be large and can take significant time to download.

## Common viewser error messages

### Validation errors

When a queryset is passed to the service, it is examined by a validation function which checks for easily-detected errors. Errors found by the validator will be received immediately by the client:

    validation failed with illegal aggregation functions:   [list of bad aggregation functions] 

-> indicates that one or more non-existent aggregations was requested

    validation failed with repeated column names:   [list of repeated column names]
-> indicates that one or more column names has been used more than once in the queryset definition

    validation failed with non-existent transforms:   [list of bad transforms]
-> indicates that one or more non-existent transforms was requested

    validation failed with disallowed transform loas: [list of bad transform:loa combinations]
-> indicates that the transform:loa pairings in the list are illegal

### Runtime errors

Other kinds of error are only detectable once processing the queryset has started, so these errors may take considerably longer to appear:

    db fetch failed - missing columns: [list of bad column names]
-> indicates that the listed columns do not exist in the VIEWS database

    db fetch failed, to_loa = country_month, columns = ['/base/<bad_loa>.ged_sb_best_sum_nokgi/country_month.sum'], exception = no such loa is available right now!
-> indicates that when trying to fetch the column 'ged_sb_best_sum_nokgi', the source loa <bad_loa> does not exist

    transform failed,   file (path to transform function on server), line XX, in (transform), (specific error message)
-> indicates that a transform operation failed, likely because of non-sensical parameters - the specific error message gives more details

## viewser status messages

While running, viewser attempts to keep users informed of the progress of their queryset's computation. Status messages are displayed on a single self-replacing line which starts with a counter, incrementing every time the client pings the server. A queryset usually passes through two separate queues - one handles fetching of raw data from the database, the second handles transforms. A queryset which passes validation will usually be passed to the database queue. A user will see a message of the form 

`Queryset [queryset name] dispatched to database queue - n columns to compute`

with n the number of columns in the queryset. This message indicates that the queryset is *waiting* in the database queue.
Once fetching of raw data has started, the message will be replaced by one of the form 

`Queryset [queryset name] db fetch in progress - l of m jobs remaining`

where the total number of jobs is summed over all columns and

- Fetching one raw feature from the database is 1 job
- Every transform is 1 job
- Renaming the column after all the transforms have been done is 1 job

Note that the value of m is the total number of jobs required to compute the queryset *from scratch*. If there are jobs in the cache, this shows itself by the value of l starting out less than m.

If the database fetch completes without errors, the queryset will be passed to the transform queue, and a status message of the form

`Queryset [queryset name] dispatched to database queue - n columns to compute`

This message indicates only that the queryset is waiting in the transform queue. Once computation of transforms begins, the status message will be replaced by one of the form

`Queryset [queryset name] transform in progress - l of m jobs remaining`

When all transforms have completed, downloading of the completed dataframe begins. The status message at this point will cease updating, which can make it appear that the client is hung in the case of large querysets. Users are asked to be patient :) .

## Input drift detection

The viewser package is able to perform a series of tests on the data fetched from the remote service which are designed to detect, and issue warnings about, anomalies in the data. 

Two broad types of anomaly can be monitored

### Global anomalies

These examine the whole dataset, whatever its dimensions (thought on terms of time_units x space_units x features). The available anomaly detectors are

 - global_missingness: simply reports if the total fraction of missing (i.e. NaN) values across the whole dataset exceeds a threshold. Threshold should be a small number between 0 and 1, e.g. 0.05.


 - global zeros: reports if the total fraction of zero values across the whole dataset exceeds a threshold. Threshold should be a small number between 0 and 1, e.g. 0.05.


 - time_missingness: reports if the fraction of missingness across any (space_units x features) slices exceeds a threshold. Threshold should be a small number between 0 and 1, e.g. 0.05.


 - space_missingness: reports if the fraction of missingness across any (time_units x features) slices exceeds a threshold. Threshold should be a small number between 0 and 1, e.g. 0.05.


 - feature_missingness: reports if the fraction of missingness for any feature (over all time and space units) exceeds a threshold. Threshold should be a small number between 0 and 1, e.g. 0.05.


 - time_zeros: reports if the fraction of zeros across any (space_units x features) slices exceeds a threshold. Threshold should be a number between 0 and 1 and close to 1, e.g. 0.95.


 - space_zeros: reports if the fraction of zeros across any (time_units x features) slices exceeds a threshold. Threshold should be a number between 0 and 1 close to 1, e.g. 0.95.


 - feature_zeros: reports if the fraction of zeros for any feature (over all time and space units) exceeds a threshold. Threshold should be a number between 0 and 1 close to 1, e.g. 0.95.


### Recent data anomalies
These partition the dataset into three partitions, defined by two integers n and m. If the most recent time unit in the dateset is k: the test partition consists of the most recent n time units, i.e. k-n+1 to k inclusive (usually n would be 1 so the test parition simply consists of the most recent time unit k), the standard partition consists of the most recent k-m-n to k-n time units. The time units before k-m-n are discarded. The available anomaly detectors are
- delta_completeness: reports, for each feature, if the ratio of missingness fractions in the test and standard partitions is greater than a threshold. Threshold should be a number between 0 and 1, e.g. 0.25.


- delta_zeros: reports, for each feature, if the ratio of the fraction of zeros in the test and standard partitions is greater than a threshold. Threshold should be a number between 0 and 1, e.g. 0.25.


- extreme_values: reports, for each feature, if the most extreme value in the test partition is more than (threshold) standard deviations from the mean of the data in the test partition. Threshold should be a number in the range 2-7, e.g. 5.


- ks_drift: for each feature, performs a two-sample Kolmogorov-Smirnoff test (https://en.wikipedia.org/wiki/Kolmogorov–Smirnov_test#Two-sample_Kolmogorov–Smirnov_test) between the data in the test and standard partitions and reports if (1/the returned p-value) exceeds a threshold. Threshold should be a large number, e.g. 100.


- ecod_drift: for all features simultaneously, reports if the fraction of data-points considered outliers in the test partition exceeds that in the standard partition, according to an ECOD model (https://pyod.readthedocs.io/en/latest/_modules/pyod/models/ecod.html#ECOD) trained on the standard partition, exceeds a threshold. Threshold should be a number between 0 and 1, e.g. 0.25.

### Drift-detection self-test functionality

The drift-detection machinery is provided with self-testing infrastructure. 

This requires a small standard queryset named 'drift_detection_self_test' which MUST have been published to the views queryset database BEFORE the self-test can be executed. This queryset should consist of a few conlict features and at least one very differently structured feature, e.g. GDP from the WDI.

The self-test machinery is invoked by passing a True self-test flag in the call to the 'fetch_with_drift_detection' function, e.g.

    data,alerts = qs.publish().fetch_with_drift_detection(start_date=start_date,
                                                      end_date=end_date,
                                                      drift_config_dict=drift_config_dict,
                                                      self_test=True
                                                     )

For every requested drift-detection function in the drift_config_dict dictionary, the standard dataset will be copied and a perturbation particular to that function will be applied to the copy before passing it to the drift-detector, in a fashion designed to trigger an alert.

If all drift-detection functions work correctly and trigger alerts, a message is printed to the terminal. If one of more of the drift-detectors fails to trigger, an error is raised with a list of offending drift-detectors. It is then up to the user to determine why the machinery failed.

## Funding

The contents of this repository is the outcome of projects that have received funding from the European Research Council (ERC) under the European Union’s Horizon 2020 research and innovation programme (Grant agreement No. 694640, *ViEWS*) and Horizon Europe (Grant agreement No. 101055176, *ANTICIPATE*; and No. 101069312, *ViEWS* (ERC-2022-POC1)), Riksbankens Jubileumsfond (Grant agreement No. M21-0002, *Societies at Risk*), Uppsala University, Peace Research Institute Oslo, the United Nations Economic and Social Commission for Western Asia (*ViEWS-ESCWA*), the United Kingdom Foreign, Commonwealth & Development Office (GSRA – *Forecasting Fatalities in Armed Conflict*), the Swedish Research Council (*DEMSCORE*), the Swedish Foundation for Strategic Environmental Research (*MISTRA Geopolitics*), the Norwegian MFA (*Conflict Trends* QZA-18/0227), and the United Nations High Commissioner for Refugees (*the Sahel Predictive Analytics project*).
