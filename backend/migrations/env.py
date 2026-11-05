from alembic import context
from app.db import engine, Base
from app import models

def migrate(connection):
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()

# Allows isolated migration tests and externally managed transactions.
connection = context.config.attributes.get("connection")
if connection is not None:
    migrate(connection)
else:
    with engine.connect() as connection:
        migrate(connection)
