# Statement for enabling the development environment
DEBUG = True

# Define the application directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

TACPLUS_APP = "/usr/local/sbin/tac_plus"
TACPLUS_CONFIG = "/usr/local/etc/tac_plus.cfg"
TACPLUS_SYSTEMD_SERVICE = "tac_plus.service"

TACACSGUI_USER = "www-data"
TACACSGUI_GROUP = "www-data"

# Define the database 
# Replace MySQL connection string with SQLite
SQLALCHEMY_DATABASE_URI = "sqlite:///tacacsgui.db"
DATABASE_CONNECT_OPTIONS = {}

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED     = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "ItCishyonCusOvroquofsEmmadGoaFuo"

# Secret key for signing cookies
SECRET_KEY = "knavMecNovKilNovmujchajwywoawdUk"

