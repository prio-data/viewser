
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

Show all tables in the database:

`viewser tables list` 

Show columns in a particular table:

`viewser tables show table-name`

Show all transforms sorted by level of analysis:

`viewser transforms list`

Show docstring for a particular transform:

`viewser transforms show transform-name`

(note that the transform name should be the full name, e.g. 'any/temporal.entropy')

## Via API

The full functionality of viewser is exposed via its API for use in scripts and notebooks

The two fundemntal objects used to define what data is fetched by the client are the *Queryset* and the *Column*, where a 
Queryset consists of one or more Columns. 

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

## Aggregation/disaggregation

The definition of a queryset must include the *target* level of analysis, at which the resulting data will be presented to the user.

The definition of each column in a queryset must specify the *source* level of analysis, at which the raw data used to define that column is stored in the database.

If these loas differ for a given column, the necessary aggregation or disaggregation is performed automatically.

If an `aggregation` is required, the user may choose from the following aggregation functions:

- `sum` (default): sums over necessary spatial and time units
- `avg`: averages over necessary spatial and time units
- `max`: takes the maxmimum value over necessary spatial and time units
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

## Transforms

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

## Publising a queryset

Before a queryset can be fetched, it must be published to a permanent database on the server. This is done using the `publish()` method:

    data = new_queryset.publish()

## Fetching a queryset

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

'validation failed with illegal aggregation functions:   [list of bad aggregation functions]' - indicates that one or more non-existent aggregations was requested

'validation failed with repeated column names:   [list of repeated column names]' - indicates that one or more column names has been used more than once in the queryset definition

'validation failed with non-existent transforms:   [list of bad transforms]' - indicates that one or more non-existent transforms was requested

'validation failed with disallowed transform loas: [list of bad transform:loa combinations] - indicates that the transform:loa pairings in the list are illegal

### Runtime errors

Other kinds of error are only detectable once processing the queryset has started, so these errors may take considerably longer to appear:

'db fetch failed - missing columns: [list of bad column names]' - indicates that the listed columns do not exist in the VIEWS database

'db fetch failed, to_loa = country_month, columns = ['/base/<bad_loa>.ged_sb_best_sum_nokgi/country_month.sum'], exception = no such loa is available right now!' - indicates that when trying to fetch the column 'ged_sb_best_sum_nokgi', the source loa <bad_loa> does not exist

'transform failed,   file (path to transform function on server), line XX, in (transform), (specific error message)' - indicates that a transform operation failed, likely because of non-sensical parameters - the specific error message gives more details


## Funding

The contents of this repository is the outcome of projects that have received funding from the European Research Council (ERC) under the European Union’s Horizon 2020 research and innovation programme (Grant agreement No. 694640, *ViEWS*) and Horizon Europe (Grant agreement No. 101055176, *ANTICIPATE*; and No. 101069312, *ViEWS* (ERC-2022-POC1)), Riksbankens Jubileumsfond (Grant agreement No. M21-0002, *Societies at Risk*), Uppsala University, Peace Research Institute Oslo, the United Nations Economic and Social Commission for Western Asia (*ViEWS-ESCWA*), the United Kingdom Foreign, Commonwealth & Development Office (GSRA – *Forecasting Fatalities in Armed Conflict*), the Swedish Research Council (*DEMSCORE*), the Swedish Foundation for Strategic Environmental Research (*MISTRA Geopolitics*), the Norwegian MFA (*Conflict Trends* QZA-18/0227), and the United Nations High Commissioner for Refugees (*the Sahel Predictive Analytics project*).
