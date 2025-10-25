"""Initial database schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create query_history table
    op.create_table('query_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(length=20), nullable=False),
        sa.Column('response_time', sa.Float(), nullable=False),
        sa.Column('cache_hit', sa.Boolean(), nullable=True),
        sa.Column('user_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sql_generated', sa.Text(), nullable=True),
        sa.Column('entities_extracted', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create document_metadata table
    op.create_table('document_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('upload_date', sa.DateTime(), nullable=True),
        sa.Column('processing_status', sa.String(length=20), nullable=True),
        sa.Column('chroma_id', sa.String(length=255), nullable=True),
        sa.Column('user_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('document_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chroma_id')
    )
    
    # Create schema_cache table
    op.create_table('schema_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('connection_string_hash', sa.String(length=64), nullable=False),
        sa.Column('schema_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('discovered_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create performance_metrics table
    op.create_table('performance_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metric_name', sa.String(length=50), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(length=20), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['query_id'], ['query_history.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token')
    )
    
    # Create system_logs table
    op.create_table('system_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('logger_name', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=True),
        sa.Column('function', sa.String(length=100), nullable=True),
        sa.Column('line_number', sa.BigInteger(), nullable=True),
        sa.Column('exception_info', sa.Text(), nullable=True),
        sa.Column('user_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create database_connections table
    op.create_table('database_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('connection_name', sa.String(length=100), nullable=False),
        sa.Column('connection_string', sa.Text(), nullable=False),
        sa.Column('connection_type', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_health_check', sa.DateTime(), nullable=True),
        sa.Column('health_status', sa.String(length=20), nullable=True),
        sa.Column('connection_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_query_history_created_at', 'query_history', ['created_at'])
    op.create_index('idx_query_history_query_type', 'query_history', ['query_type'])
    op.create_index('idx_query_history_user_session', 'query_history', ['user_session_id'])
    
    op.create_index('idx_document_metadata_file_type', 'document_metadata', ['file_type'])
    op.create_index('idx_document_metadata_processing_status', 'document_metadata', ['processing_status'])
    op.create_index('idx_document_metadata_user_session', 'document_metadata', ['user_session_id'])
    
    op.create_index('idx_schema_cache_connection_hash', 'schema_cache', ['connection_string_hash'])
    op.create_index('idx_schema_cache_expires_at', 'schema_cache', ['expires_at'])
    
    op.create_index('idx_performance_metrics_query_id', 'performance_metrics', ['query_id'])
    op.create_index('idx_performance_metrics_metric_name', 'performance_metrics', ['metric_name'])
    op.create_index('idx_performance_metrics_recorded_at', 'performance_metrics', ['recorded_at'])
    
    op.create_index('idx_user_sessions_session_token', 'user_sessions', ['session_token'])
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    
    op.create_index('idx_system_logs_level', 'system_logs', ['level'])
    op.create_index('idx_system_logs_created_at', 'system_logs', ['created_at'])
    op.create_index('idx_system_logs_user_session', 'system_logs', ['user_session_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_system_logs_user_session', table_name='system_logs')
    op.drop_index('idx_system_logs_created_at', table_name='system_logs')
    op.drop_index('idx_system_logs_level', table_name='system_logs')
    
    op.drop_index('idx_user_sessions_expires_at', table_name='user_sessions')
    op.drop_index('idx_user_sessions_user_id', table_name='user_sessions')
    op.drop_index('idx_user_sessions_session_token', table_name='user_sessions')
    
    op.drop_index('idx_performance_metrics_recorded_at', table_name='performance_metrics')
    op.drop_index('idx_performance_metrics_metric_name', table_name='performance_metrics')
    op.drop_index('idx_performance_metrics_query_id', table_name='performance_metrics')
    
    op.drop_index('idx_schema_cache_expires_at', table_name='schema_cache')
    op.drop_index('idx_schema_cache_connection_hash', table_name='schema_cache')
    
    op.drop_index('idx_document_metadata_user_session', table_name='document_metadata')
    op.drop_index('idx_document_metadata_processing_status', table_name='document_metadata')
    op.drop_index('idx_document_metadata_file_type', table_name='document_metadata')
    
    op.drop_index('idx_query_history_user_session', table_name='query_history')
    op.drop_index('idx_query_history_query_type', table_name='query_history')
    op.drop_index('idx_query_history_created_at', table_name='query_history')
    
    # Drop tables
    op.drop_table('database_connections')
    op.drop_table('system_logs')
    op.drop_table('user_sessions')
    op.drop_table('performance_metrics')
    op.drop_table('schema_cache')
    op.drop_table('document_metadata')
    op.drop_table('query_history')
