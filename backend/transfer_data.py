"""Copy an existing database into an EMPTY deployment database without changing passwords."""
import argparse
from flask_migrate import upgrade
from sqlalchemy import create_engine, select, func, Integer, text
from sqlalchemy.exc import SQLAlchemyError
from backend.app import create_app
from backend.config import BASE_DIR
from backend.extensions import db


def transfer(source, target):
    if source.url == target.url:
        raise RuntimeError("Source and target must be different databases.")
    counts = {}
    # The destination check and every row insert share a single transaction.
    with source.connect() as reader, target.begin() as writer:
        for table in db.metadata.sorted_tables:
            if writer.scalar(select(func.count()).select_from(table)):
                raise RuntimeError("Destination is not empty; refusing to overwrite existing data.")
        for table in db.metadata.sorted_tables:
            order = list(table.primary_key.columns)
            rows = reader.execute(select(table).order_by(*order)).mappings()
            count = 0
            while batch := rows.fetchmany(100):
                writer.execute(table.insert(), [dict(row) for row in batch])
                count += len(batch)
            counts[table.name] = count
        if target.dialect.name == "postgresql":
            for table in db.metadata.sorted_tables:
                column = table.c.get("id")
                if column is not None and isinstance(column.type, Integer):
                    quoted = target.dialect.identifier_preparer.quote(table.name)
                    writer.execute(text(f"SELECT setval(pg_get_serial_sequence(:name, 'id'), "
                                        f"COALESCE((SELECT MAX(id) FROM {quoted}), 0) + 1, false)"),
                                   {"name": table.name})
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Source SQLAlchemy URL; use an absolute path for SQLite.")
    options = parser.parse_args()
    app = create_app()
    source = create_engine(options.source)
    try:
        with app.app_context():
            upgrade(directory=str(BASE_DIR / "migrations"))
            counts = transfer(source, db.engine)
        # Log counts only; never print credentials, password hashes, or user records.
        print("Copied existing data: " + ", ".join(f"{name}={count}" for name, count in counts.items()))
    except (SQLAlchemyError, RuntimeError) as error:
        if isinstance(error, RuntimeError):
            parser.exit(1, str(error) + "\n")
        parser.exit(1, "Data transfer failed. Check connectivity and source schema; target inserts were rolled back.\n")
    finally:
        source.dispose()


if __name__ == "__main__":
    main()
