"""migrate3

Revision ID: 2997f19d1b98
Revises: a9a295c4eef1
Create Date: 2024-01-17 01:33:08.884070

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2997f19d1b98'
down_revision = 'a9a295c4eef1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rating', schema=None) as batch_op:
        batch_op.drop_constraint('rating_recipe_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'recipe', ['recipe_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('rating', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('rating_recipe_id_fkey', 'recipe', ['recipe_id'], ['id'])

    # ### end Alembic commands ###
