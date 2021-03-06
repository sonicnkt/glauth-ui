"""added missing glauth settings

Revision ID: ab19472d3d97
Revises: ea1b74e55123
Create Date: 2021-05-04 11:50:53.955319

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab19472d3d97'
down_revision = 'ea1b74e55123'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('groupformat', sa.String(length=4), nullable=True))
        batch_op.add_column(sa.Column('nameformat', sa.String(length=4), nullable=True))
        batch_op.add_column(sa.Column('sshkeyattr', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.drop_column('sshkeyattr')
        batch_op.drop_column('nameformat')
        batch_op.drop_column('groupformat')

    # ### end Alembic commands ###
