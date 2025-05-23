"""imagesslots

Revision ID: 1bdd58f333fd
Revises: f38390341273
Create Date: 2025-05-10 03:29:30.171026

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '1bdd58f333fd'
down_revision = 'f38390341273'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_image')
    with op.batch_alter_table('preferences', schema=None) as batch_op:
        batch_op.drop_column('images')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image1', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('image2', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('image3', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('image4', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('image5', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('image5')
        batch_op.drop_column('image4')
        batch_op.drop_column('image3')
        batch_op.drop_column('image2')
        batch_op.drop_column('image1')

    with op.batch_alter_table('preferences', schema=None) as batch_op:
        batch_op.add_column(sa.Column('images', sqlite.JSON(), nullable=True))

    op.create_table('user_image',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('image_url', sa.VARCHAR(length=255), nullable=False),
    sa.Column('caption', sa.VARCHAR(length=255), nullable=True),
    sa.Column('position', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
