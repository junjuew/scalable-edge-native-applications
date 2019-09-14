"""modify trace table

Revision ID: 1803db7440fa
Revises: f361eec28fab
Create Date: 2019-05-30 17:27:35.232399

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '1803db7440fa'
down_revision = 'f361eec28fab'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Trace',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=512), nullable=False),
    sa.Column('trace', sa.String(length=512), nullable=False),
    sa.Column('fid', sa.String(length=32), nullable=False),
    sa.Column('symbolic_state', sa.String(length=65534), nullable=True),
    sa.Column('rot_x', sa.FLOAT(precision=53), nullable=True),
    sa.Column('rot_y', sa.FLOAT(precision=53), nullable=True),
    sa.Column('rot_z', sa.FLOAT(precision=53), nullable=True),
    sa.Column('acc_x', sa.FLOAT(precision=53), nullable=True),
    sa.Column('acc_y', sa.FLOAT(precision=53), nullable=True),
    sa.Column('acc_z', sa.FLOAT(precision=53), nullable=True),
    sa.Column('sensor_timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('Sec6IntraAppBk')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Sec6IntraAppBk',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('name', mysql.VARCHAR(length=512), nullable=False),
    sa.Column('index', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('app', mysql.VARCHAR(length=32), nullable=True),
    sa.Column('client', mysql.VARCHAR(length=32), nullable=True),
    sa.Column('arrival', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('finished', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('reply', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('utility', mysql.FLOAT(), nullable=True),
    sa.Column('result', mysql.VARCHAR(length=512), nullable=True),
    sa.Column('is_gt_active', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.drop_table('Trace')
    # ### end Alembic commands ###