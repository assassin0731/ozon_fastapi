"""add operation

Revision ID: acd069692d77
Revises: 70afe35f6f9b
Create Date: 2024-02-12 13:29:23.839469

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'acd069692d77'
down_revision: Union[str, None] = '70afe35f6f9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('price',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('article', sa.String(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('date', sa.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('price')
    # ### end Alembic commands ###
