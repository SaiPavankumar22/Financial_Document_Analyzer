import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
from .models import Base
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./financial_analyzer.db"
)

# For PostgreSQL in production:
# DATABASE_URL = "postgresql://user:password@localhost/financial_analyzer"

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL logging
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

class DatabaseManager:
    """Database manager class for common operations"""
    
    @staticmethod
    def create_user(email: str, full_name: str) -> str:
        """Create a new user and return user_id"""
        with get_db_session() as db:
            from .models import User
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return existing_user.user_id
            
            # Create new user
            user = User(email=email, full_name=full_name)
            db.add(user)
            db.flush()  # Get the ID without committing
            return user.user_id
    
    @staticmethod
    def create_analysis_record(
        user_id: str,
        filename: str,
        file_size: int,
        file_hash: str,
        query: str
    ) -> str:
        """Create a new analysis record and return analysis_id"""
        with get_db_session() as db:
            from .models import AnalysisResult, User
            
            # Get user
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Create analysis record
            analysis = AnalysisResult(
                user_id=user.id,
                original_filename=filename,
                file_size=file_size,
                file_hash=file_hash,
                query=query,
                status="pending"
            )
            db.add(analysis)
            db.flush()
            return analysis.analysis_id
    
    @staticmethod
    def update_analysis_status(analysis_id: str, status: str, progress: int = None):
        """Update analysis status and progress"""
        with get_db_session() as db:
            from .models import AnalysisResult
            from datetime import datetime
            
            analysis = db.query(AnalysisResult).filter(
                AnalysisResult.analysis_id == analysis_id
            ).first()
            
            if analysis:
                analysis.status = status
                if progress is not None:
                    analysis.progress = progress
                
                if status == "completed":
                    analysis.completed_at = datetime.utcnow()
    
    @staticmethod
    def save_analysis_results(
        analysis_id: str,
        analysis_report: str,
        financial_metrics: str = None,
        investment_recommendations: str = None,
        risk_assessment: str = None,
        processing_time: float = None
    ):
        """Save analysis results to database"""
        with get_db_session() as db:
            from .models import AnalysisResult
            from datetime import datetime
            
            analysis = db.query(AnalysisResult).filter(
                AnalysisResult.analysis_id == analysis_id
            ).first()
            
            if analysis:
                analysis.analysis_report = analysis_report
                analysis.financial_metrics = financial_metrics
                analysis.investment_recommendations = investment_recommendations
                analysis.risk_assessment = risk_assessment
                analysis.processing_time = processing_time
                analysis.status = "completed"
                analysis.progress = 100
                analysis.completed_at = datetime.utcnow()
    
    @staticmethod
    def get_analysis_result(analysis_id: str) -> dict:
        """Get analysis result by ID"""
        with get_db_session() as db:
            from .models import AnalysisResult, User
            
            result = db.query(AnalysisResult).filter(
                AnalysisResult.analysis_id == analysis_id
            ).first()
            
            if not result:
                return None
            
            return {
                "analysis_id": result.analysis_id,
                "status": result.status,
                "progress": result.progress,
                "query": result.query,
                "original_filename": result.original_filename,
                "analysis_report": result.analysis_report,
                "financial_metrics": result.financial_metrics,
                "investment_recommendations": result.investment_recommendations,
                "risk_assessment": result.risk_assessment,
                "processing_time": result.processing_time,
                "created_at": result.created_at.isoformat() if result.created_at else None,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "error_message": result.error_message
            }
    
    @staticmethod
    def get_user_analyses(user_id: str, limit: int = 50) -> list:
        """Get user's analysis history"""
        with get_db_session() as db:
            from .models import AnalysisResult, User
            
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                return []
            
            analyses = db.query(AnalysisResult).filter(
                AnalysisResult.user_id == user.id
            ).order_by(AnalysisResult.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "analysis_id": analysis.analysis_id,
                    "status": analysis.status,
                    "progress": analysis.progress,
                    "original_filename": analysis.original_filename,
                    "query": analysis.query,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                    "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
                }
                for analysis in analyses
            ]