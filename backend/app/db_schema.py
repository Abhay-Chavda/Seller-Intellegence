from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.core.security import hash_password


def ensure_user_profile_columns(engine: Engine, schema: str | None) -> None:
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("users", schema=schema)}

    qualified_table = "users" if not schema else f"{schema}.users"

    with engine.begin() as connection:
        if "role" not in columns:
            connection.execute(text(f"ALTER TABLE {qualified_table} ADD COLUMN role VARCHAR(50)"))
        if "subscription_type" not in columns:
            connection.execute(text(f"ALTER TABLE {qualified_table} ADD COLUMN subscription_type VARCHAR(50)"))

        connection.execute(
            text(
                f"""
                UPDATE {qualified_table}
                SET role = COALESCE(NULLIF(role, ''), 'user'),
                    subscription_type = COALESCE(NULLIF(subscription_type, ''), 'Demo')
                """
            )
        )


def seed_admin_user(
    engine: Engine,
    schema: str | None,
    *,
    email: str,
    password: str,
    name: str = "Admin User",
    subscription_type: str = "Demo",
) -> None:
    qualified_table = "users" if not schema else f"{schema}.users"
    normalized_email = email.strip().lower()
    hashed_password = hash_password(password)

    with engine.begin() as connection:
        existing = connection.execute(
            text(f"SELECT id FROM {qualified_table} WHERE lower(email) = :email"),
            {"email": normalized_email},
        ).first()

        if existing:
            connection.execute(
                text(
                    f"""
                    UPDATE {qualified_table}
                    SET name = :name,
                        hashed_password = :hashed_password,
                        role = 'admin',
                        subscription_type = :subscription_type
                    WHERE lower(email) = :email
                    """
                ),
                {
                    "name": name,
                    "hashed_password": hashed_password,
                    "subscription_type": subscription_type,
                    "email": normalized_email,
                },
            )
        else:
            connection.execute(
                text(
                    f"""
                    INSERT INTO {qualified_table}
                        (name, email, hashed_password, role, subscription_type, is_active, created_at)
                    VALUES
                        (:name, :email, :hashed_password, 'admin', :subscription_type, TRUE, CURRENT_TIMESTAMP)
                    """
                ),
                {
                    "name": name,
                    "email": normalized_email,
                    "hashed_password": hashed_password,
                    "subscription_type": subscription_type,
                },
            )
