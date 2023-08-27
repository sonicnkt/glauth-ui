"""Add raw additional user config

Revision ID: 59f281c20fe3
Revises: 8a2c49f0f728
Create Date: 2023-08-27 10:38:48.668005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59f281c20fe3'
down_revision = '8a2c49f0f728'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.alter_column('anonymousDSE',
               existing_type=sa.BOOLEAN(),
               nullable=False)

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('raw_addition_user_config', sa.String(length=65536), nullable=False, server_default=''))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('raw_addition_user_config')

    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.alter_column('anonymousDSE',
               existing_type=sa.BOOLEAN(),
               nullable=True)

    # ### end Alembic commands ###
