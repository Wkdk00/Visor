"""v1

Revision ID: caf0835a94b8
Revises: 6dec050e6d00
Create Date: 2025-06-26 13:07:48.814875

"""
from typing import Sequence, Union
from sqlalchemy.dialects import postgresql

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'caf0835a94b8'
down_revision: Union[str, None] = '6dec050e6d00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # departments_table
    op.create_table(
        'departments_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('department', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='departments_table_pkey')
    )
    op.create_index('ix_departments_table_id', 'departments_table', ['id'], unique=True)

    # positions_table
    op.create_table(
        'positions_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['department_id'], ['departments_table.id'],
            name='positions_department_id_fkey',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', name='positions_table_pkey')
    )
    op.create_index('ix_positions_table_id', 'positions_table', ['id'], unique=True)

    # zones_table
    op.create_table(
        'zones_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone_name', sa.Text(), nullable=False),
        sa.Column('security_level', sa.SmallInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=False), nullable=False),
        sa.PrimaryKeyConstraint('id', name='zones_table_pkey')
    )
    op.create_index('ix_zones_table_id', 'zones_table', ['id'], unique=True)

    # employees_table
    op.create_table(
        'employees_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.Text(), nullable=False),
        sa.Column('passport', sa.Text(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('position_id', sa.Integer(), nullable=True),
        sa.Column('post', sa.Text(), nullable=False),
        sa.Column('badge_id', sa.Integer(), nullable=False),
        sa.Column('security_level', sa.SmallInteger(), nullable=False),
        sa.Column('phone_number', sa.Text(), nullable=True),
        sa.Column('mail', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('birth', sa.Date(), nullable=False),
        sa.Column('updated_at', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ['department_id'], ['departments_table.id'],
            name='employees_department_id_fkey',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['position_id'], ['positions_table.id'],
            name='employees_position_id_fkey',
            ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id', name='employees_table_pkey'),
        sa.UniqueConstraint('passport', name='employees_passport_key')
    )
    op.create_index('ix_employees_table_id', 'employees_table', ['id'], unique=True)

    # entrances_table
    op.create_table(
        'entrances_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('zone_id', sa.Integer(), nullable=False),
        sa.Column('access', sa.Boolean(), nullable=False),
        sa.Column('entrance_time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['employee_id'], ['employees_table.id'],
            name='entrances_employee_id_fkey',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['zone_id'], ['zones_table.id'],
            name='entrances_zone_id_fkey',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', name='entrances_table_pkey')
    )
    op.create_index('ix_entrances_table_id', 'entrances_table', ['id'], unique=True)

    # biometrics_table
    op.create_table(
        'biometrics_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('photo_path', sa.String(), nullable=False),
        sa.Column('created_at', sa.Date, nullable=False),
        sa.ForeignKeyConstraint(
            ['employee_id'], ['employees_table.id'],
            name='biometrics_employee_id_fkey',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', name='biometrics_table_pkey'),
        sa.UniqueConstraint('employee_id', name='biometrics_employee_id_key')
    )


def downgrade() -> None:
    op.drop_table('entrances_table')
    op.drop_table('employees_table')
    op.drop_table('zones_table')
    op.drop_table('positions_table')
    op.drop_table('departments_table')
    op.drop_table('biometrics_table')