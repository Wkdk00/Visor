import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from database.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True, # Полезно для автоматического обнаружения изменений
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    # Создаем асинхронный движок
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Выполняем миграции
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online():
    # Запускаем асинхронный цикл
    asyncio.run(run_async_migrations())

# Миграции в "оффлайн" режиме оставим как есть (они почти не нужны в контейнерах)
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()