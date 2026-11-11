"""Add calls

Revision ID: e5b1c9a7f3d2
Revises: 6a45e82d77a2
Create Date: 2026-11-11 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5b1c9a7f3d2'
down_revision = '6a45e82d77a2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('calls',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('caller_id', sa.Integer(), nullable=False),
    sa.Column('callee_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=12), nullable=False),
    sa.Column('offer', sa.Text(), nullable=False),
    sa.Column('answer', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('answered_at', sa.DateTime(), nullable=True),
    sa.Column('ended_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['callee_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['caller_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('calls', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_calls_callee_id'), ['callee_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_calls_caller_id'), ['caller_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_calls_conversation_id'), ['conversation_id'], unique=False)


def downgrade():
    with op.batch_alter_table('calls', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_calls_conversation_id'))
        batch_op.drop_index(batch_op.f('ix_calls_caller_id'))
        batch_op.drop_index(batch_op.f('ix_calls_callee_id'))

    op.drop_table('calls')
