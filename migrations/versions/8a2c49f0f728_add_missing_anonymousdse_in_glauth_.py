"""add missing AnonymousDSE in glauth config

Revision ID: 8a2c49f0f728
Revises: ab19472d3d97
Create Date: 2022-11-07 07:20:45.178425

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a2c49f0f728'
down_revision = 'ab19472d3d97'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('anonymousDSE', sa.Boolean, nullable=True))


def downgrade():
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.drop_column('anonymousDSE')
