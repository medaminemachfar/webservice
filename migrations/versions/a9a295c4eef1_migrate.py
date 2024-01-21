"""migrate

Revision ID: a9a295c4eef1
Revises: 
Create Date: 2024-01-16 17:13:07.144371

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9a295c4eef1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('google_id', sa.String(length=128), nullable=True),
    sa.Column('email', sa.String(length=128), nullable=True),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('google_id')
    )
    op.create_table('recipe',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('ingredients', sa.String(length=1000), nullable=False),
    sa.Column('instructions', sa.String(length=2000), nullable=False),
    sa.Column('nutrition_facts', sa.String(length=500), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('rating',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('value', sa.Integer(), nullable=False),
    sa.Column('recipe_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['recipe_id'], ['recipe.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('review',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('recipe_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['recipe_id'], ['recipe.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('review')
    op.drop_table('rating')
    op.drop_table('recipe')
    op.drop_table('user')
    op.drop_table('category')
    # ### end Alembic commands ###