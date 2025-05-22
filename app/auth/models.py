# Import the database object (db) from the main application module
# We will define this inside /app/__init__.py in the next sections.
from app import db
from app.utils.tacacs.crypt import generate_hash, verify_hash

# Define a base model for other database tables to inherit
class Base(db.Model):

    __abstract__  = True

    id            = db.Column(db.Integer, primary_key=True)
    date_created  = db.Column(db.DateTime,  default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                                           onupdate=db.func.current_timestamp())

# Define a User model
class User(Base):

    __tablename__ = 'auth_user'

    # User Name
    username = db.Column(db.String(128), nullable=False)

    # Password
    password = db.Column(db.String(192), nullable=False)

    # New instance instantiation procedure
    def __init__(self, username, password):

        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % (self.username)

class SystemUser(db.Model):
    __tablename__ = 'system_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    @property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, plaintext):
        self.password_hash = generate_hash(plaintext)

    def check_password(self, plaintext):
        try:
            return verify_hash(plaintext, self.password_hash)
        except Exception:
            return False
