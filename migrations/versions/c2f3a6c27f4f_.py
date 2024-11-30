"""empty message

Revision ID: c2f3a6c27f4f
Revises: 
Create Date: 2024-11-13 22:28:14.497065

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c2f3a6c27f4f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Drop the foreign key constraints first
    op.drop_constraint('task_assigned_to_fkey', 'task', type_='foreignkey')
    op.drop_constraint('task_history_assigned_to_fkey', 'task_history', type_='foreignkey')

    # Now drop the table
    op.drop_table('employee')
    op.drop_table('task_history')
    op.drop_table('task')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('task',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('room', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(length=500), autoincrement=False, nullable=False),
    sa.Column('assigned_to', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('complete', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('verified', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('notes', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    sa.Column('priority', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('assigned_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('completed_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['assigned_to'], ['employee.id'], name='task_assigned_to_fkey'),
    sa.PrimaryKeyConstraint('id', name='task_pkey')
    )
    op.create_table('task_history',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('room', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(length=500), autoincrement=False, nullable=False),
    sa.Column('assigned_to', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('completed_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('assigned_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('verified_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['assigned_to'], ['employee.id'], name='task_history_assigned_to_fkey'),
    sa.PrimaryKeyConstraint('id', name='task_history_pkey')
    )
    op.create_table('employee',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('employee_number', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('role', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('email', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('password', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='employee_pkey'),
    sa.UniqueConstraint('email', name='employee_email_key'),
    sa.UniqueConstraint('employee_number', name='employee_employee_number_key')
    )
    # ### end Alembic commands ###