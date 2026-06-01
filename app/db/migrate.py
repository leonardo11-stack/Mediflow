from sqlalchemy import text

from app.db.session import engine


def run_migrations() -> None:
    """Aplica migrações incrementais (create_all não altera tabelas existentes)."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE triagens
                ADD COLUMN IF NOT EXISTS email VARCHAR(255);
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE triagens
                SET email = 'pendente@mediflow.local'
                WHERE email IS NULL OR email = '';
                """
            )
        )
        conn.execute(
            text(
                """
                ALTER TABLE triagens
                ALTER COLUMN email SET NOT NULL;
                """
            )
        )
