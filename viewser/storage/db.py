import logging
import os
from cryptography import x509
from psycopg2 import connect, OperationalError
from sqlalchemy import create_engine
from viewser import settings

logger = logging.getLogger(__name__)

def _cert_user() -> str:
    """
    Fetch the ViEWS user name. Each user authenticates to ViEWS using a username and a ViEWS signed PEM certificate.
    The certificate, which should be installed in .postgres contains the user name as part of the CN field.
    This fetches the user name from the certificate.
    :return:
    """

    with open(os.path.expanduser('~/.postgresql/postgresql.crt'), 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read())
    common_name = cert.subject.rfc4514_string().split(',')
    try:
        # Extract the content of the CN field from the x509 formatted string.
        views_user_name = [i.split('=')[1] for i in common_name if i.split('=')[0] == 'CN'][0]
    except IndexError:
        raise ConnectionError("Something is wrong with the ViEWS Certificate. Contact ViEWS to obtain authentication!")
    return views_user_name

def get_metadata_con():
    parameters = {
            "host":    settings.config.get("MODEL_METADATA_DATABASE_HOSTNAME","0.0.0.0"),
            "port":    settings.config.get("MODEL_METADATA_DATABASE_PORT", 5432),
            "dbname":  settings.config.get("MODEL_METADATA_DATABASE_NAME", "postgres"),
            "sslmode": settings.config.get("MODEL_METADATA_DATABASE_SSLMODE", "require"),
        }

    if user := settings.config.get("MODEL_METADATA_DATABASE_USER", ""):
        parameters["user"] = user
    else:
        # Try to infer
        try:
            parameters["user"] = _cert_user()
        except ConnectionError:
            logger.warning("Failed to get cert user")
            parameters["user"] = "postgres"

    if password := settings.config.get("MODEL_METADATA_DATABASE_PASSWORD", ""):
        parameters["password"] = password

    try:
        return connect(" ".join([str(k)+"="+str(v) for k,v in parameters.items()]))
    except OperationalError:
        raise ValueError((
            "Something went wrong when connecting to the metadata database. Make sure that the following config values are set: "
            "MODEL_METADATA_DATABASE_HOST, "
            "MODEL_METADATA_DATABASE_NAME, "
            "MODEL_METADATA_DATABASE_USER"
        ))

metadata_engine = create_engine("postgresql://", creator = get_metadata_con)
