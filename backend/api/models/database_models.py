"""
SQLAlchemy Models for Internal Application Data
Defines all database models for the NLP Query Engine
"""
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, BigInteger, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

Base = declarative_base()

class QueryHistory(Base):
    """Model for tracking user queries and their performance"""
    
    __tablename__ = "query_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(20), nullable=False)  # sql, document, hybrid
    response_time = Column(Float, nullable=False)
    cache_hit = Column(Boolean, default=False)
    user_session_id = Column(UUID(as_uuid=True), nullable=True)
    sql_generated = Column(Text, nullable=True)
    entities_extracted = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    performance_metrics = relationship("PerformanceMetrics", back_populates="query")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "query_text": self.query_text,
            "query_type": self.query_type,
            "response_time": self.response_time,
            "cache_hit": self.cache_hit,
            "user_session_id": str(self.user_session_id) if self.user_session_id else None,
            "sql_generated": self.sql_generated,
            "entities_extracted": self.entities_extracted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class DocumentMetadata(Base):
    """Model for storing document information and processing status"""
    
    __tablename__ = "document_metadata"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    upload_date = Column(DateTime, default=func.now())
    processing_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    chroma_id = Column(String(255), unique=True, nullable=True)
    user_session_id = Column(UUID(as_uuid=True), nullable=True)
    document_metadata = Column(JSONB, nullable=True)  # Additional document metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "processing_status": self.processing_status,
            "chroma_id": self.chroma_id,
            "user_session_id": str(self.user_session_id) if self.user_session_id else None,
            "document_metadata": self.document_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class SchemaCache(Base):
    """Model for caching discovered database schemas"""
    
    __tablename__ = "schema_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_string_hash = Column(String(64), nullable=False)
    schema_data = Column(JSONB, nullable=False)
    discovered_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "connection_string_hash": self.connection_string_hash,
            "schema_data": self.schema_data,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def is_expired(self) -> bool:
        """Check if schema cache is expired"""
        return datetime.utcnow() > self.expires_at

class PerformanceMetrics(Base):
    """Model for storing performance metrics and monitoring data"""
    
    __tablename__ = "performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), ForeignKey("query_history.id"), nullable=True)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # ms, bytes, count, etc.
    recorded_at = Column(DateTime, default=func.now())
    
    # Relationships
    query = relationship("QueryHistory", back_populates="performance_metrics")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "query_id": str(self.query_id) if self.query_id else None,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metric_unit": self.metric_unit,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }

class UserSession(Base):
    """Model for managing user sessions and authentication"""
    
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String(255), unique=True, nullable=False)
    user_id = Column(String(100), nullable=True)  # External user ID
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "session_token": self.session_token,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "is_active": self.is_active,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at

class SystemLog(Base):
    """Model for application logging and audit trails"""
    
    __tablename__ = "system_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger_name = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    line_number = Column(BigInteger, nullable=True)
    exception_info = Column(Text, nullable=True)
    user_session_id = Column(UUID(as_uuid=True), nullable=True)
    request_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "level": self.level,
            "logger_name": self.logger_name,
            "message": self.message,
            "module": self.module,
            "function": self.function,
            "line_number": self.line_number,
            "exception_info": self.exception_info,
            "user_session_id": str(self.user_session_id) if self.user_session_id else None,
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class DatabaseConnection(Base):
    """Model for tracking external database connections"""
    
    __tablename__ = "database_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_name = Column(String(100), nullable=False)
    connection_string = Column(Text, nullable=False)
    connection_type = Column(String(20), nullable=False)  # postgresql, mysql, sqlite, etc.
    is_active = Column(Boolean, default=True)
    last_health_check = Column(DateTime, nullable=True)
    health_status = Column(String(20), default="unknown")  # healthy, unhealthy, unknown
    connection_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "connection_name": self.connection_name,
            "connection_string": self.connection_string,
            "connection_type": self.connection_type,
            "is_active": self.is_active,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_status": self.health_status,
            "connection_metadata": self.connection_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
