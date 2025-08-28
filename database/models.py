from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    analyses = relationship("AnalysisResult", back_populates="user")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(50), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # File information
    original_filename = Column(String(255))
    file_size = Column(Integer)  # in bytes
    file_hash = Column(String(64))  # SHA256 hash for duplicate detection
    
    # Analysis details
    query = Column(Text)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    
    # Results
    analysis_report = Column(Text)
    financial_metrics = Column(Text)  # JSON string of extracted metrics
    investment_recommendations = Column(Text)
    risk_assessment = Column(Text)
    
    # Metadata
    processing_time = Column(Float)  # in seconds
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationship
    user = relationship("User", back_populates="analyses")

class TaskQueue(Base):
    __tablename__ = "task_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True)
    analysis_id = Column(String(50), ForeignKey("analysis_results.analysis_id"))
    
    task_type = Column(String(50))  # document_verification, financial_analysis, etc.
    status = Column(String(50), default="queued")  # queued, processing, completed, failed
    priority = Column(Integer, default=1)  # 1-10, higher is more priority
    
    # Task data
    task_data = Column(Text)  # JSON string of task parameters
    result_data = Column(Text)  # JSON string of task results
    
    # Timing
    queued_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Error handling
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text)

class SystemMetrics(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100))
    metric_value = Column(Float)
    metric_type = Column(String(50))  # counter, gauge, histogram
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Additional metadata
    tags = Column(Text)  # JSON string of tags/labels