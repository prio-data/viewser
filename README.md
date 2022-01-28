
# viewser

This package contains many useful user operations that are used by the views 3
team. These operations include fetching and publishing data, finding
documentation on both transforms and database structure, and more.


## CLI

`viewser` functionality is exposed via a CLI on your system after installation.
An overview of available commands can be seen by running `viewser --help`.

## API

In addition to the CLI, viewser exposes many useful operations as functions
that can be used in scripts.

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
