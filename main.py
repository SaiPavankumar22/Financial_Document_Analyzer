from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import uuid
import asyncio
import hashlib
import time
from datetime import datetime
from sqlalchemy.orm import Session

from crewai import Crew, Process
from agents import financial_analyst
from task import analyze_financial_document as analyze_task

# Database imports
from database.database import get_db, create_tables, DatabaseManager
from database.models import User, AnalysisResult

# Initialize FastAPI app
app = FastAPI(title="Financial Document Analyzer")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    print("Database tables created successfully!")

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def _extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF using pypdf"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        pages_text = []
        for page in reader.pages:
            try:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            except Exception as e:
                print(f"Error extracting from page: {e}")
                pages_text.append("")
        return "\n".join(pages_text)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def run_crew(query: str, document_text: str):
    """Run the crew with provided inputs"""
    try:
        financial_crew = Crew(
            agents=[financial_analyst],
            tasks=[analyze_task],
            process=Process.sequential,
            verbose=True
        )
        
        inputs = {
            'query': query,
            'document_text': document_text
        }
        
        result = financial_crew.kickoff(inputs=inputs)
        return result
    except Exception as e:
        print(f"Error running crew: {e}")
        raise e

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running", "database": "integrated"}

@app.post("/users/")
async def create_user(email: str, full_name: str, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return {"message": "User already exists", "user_id": existing_user.user_id}
        
        # Create new user
        user = User(email=email, full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "message": "User created successfully",
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.post("/analyze")
async def analyze_financial_document(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    user_email: str = Form(default="guest@example.com"),
    user_name: str = Form(default="Guest User"),
    db: Session = Depends(get_db)
):
    """Analyze financial document and provide comprehensive investment recommendations"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    start_time = time.time()
    
    try:
        # Create data directory
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Calculate file hash and size
        file_hash = calculate_file_hash(file_path)
        file_size = len(content)
        
        # Create or get user
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(email=user_email, full_name=user_name)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Check for duplicate analysis (same file hash from same user in last 24 hours)
        from datetime import datetime, timedelta
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        
        duplicate_analysis = db.query(AnalysisResult).filter(
            AnalysisResult.user_id == user.id,
            AnalysisResult.file_hash == file_hash,
            AnalysisResult.created_at >= recent_cutoff,
            AnalysisResult.status == "completed"
        ).first()
        
        if duplicate_analysis:
            return {
                "status": "duplicate_found",
                "message": "Similar analysis found from recent history",
                "analysis_id": duplicate_analysis.analysis_id,
                "previous_analysis": {
                    "analysis_report": duplicate_analysis.analysis_report,
                    "created_at": duplicate_analysis.created_at.isoformat(),
                    "processing_time": duplicate_analysis.processing_time
                }
            }
        
        # Create analysis record
        analysis = AnalysisResult(
            user_id=user.id,
            original_filename=file.filename,
            file_size=file_size,
            file_hash=file_hash,
            query=query.strip() if query.strip() else "Analyze this financial document for investment insights",
            status="processing",
            progress=10
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Extract text from PDF
        try:
            document_text = _extract_pdf_text(file_path)
            if not document_text.strip():
                analysis.status = "failed"
                analysis.error_message = "Uploaded PDF contains no readable text"
                db.commit()
                raise HTTPException(status_code=400, detail="Uploaded PDF contains no readable text")
        except Exception as e:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()
            raise
        
        # Update progress
        analysis.progress = 30
        db.commit()
        
        # Run the crew analysis
        try:
            response = await asyncio.to_thread(run_crew, analysis.query, document_text)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update analysis with results
            analysis.analysis_report = str(response)
            analysis.status = "completed"
            analysis.progress = 100
            analysis.processing_time = processing_time
            analysis.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                "status": "success",
                "analysis_id": analysis.analysis_id,
                "query": analysis.query,
                "analysis": str(response),
                "file_processed": file.filename,
                "document_length": len(document_text),
                "processing_time": round(processing_time, 2),
                "user_id": user.user_id
            }
            
        except Exception as e:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Error during analysis: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing financial document: {str(e)}")
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not remove temporary file {file_path}: {cleanup_error}")

@app.get("/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str, db: Session = Depends(get_db)):
    """Get analysis result by ID"""
    try:
        analysis = db.query(AnalysisResult).filter(
            AnalysisResult.analysis_id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get user info
        user = db.query(User).filter(User.id == analysis.user_id).first()
        
        return {
            "analysis_id": analysis.analysis_id,
            "status": analysis.status,
            "progress": analysis.progress,
            "query": analysis.query,
            "original_filename": analysis.original_filename,
            "file_size": analysis.file_size,
            "analysis_report": analysis.analysis_report,
            "processing_time": analysis.processing_time,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "error_message": analysis.error_message,
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "full_name": user.full_name
            } if user else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analysis: {str(e)}")

@app.get("/users/{user_id}/analyses")
async def get_user_analyses(user_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """Get user's analysis history"""
    try:
        # Get user
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get analyses
        analyses = db.query(AnalysisResult).filter(
            AnalysisResult.user_id == user.id
        ).order_by(AnalysisResult.created_at.desc()).limit(limit).all()
        
        return {
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "full_name": user.full_name
            },
            "analyses": [
                {
                    "analysis_id": analysis.analysis_id,
                    "status": analysis.status,
                    "progress": analysis.progress,
                    "original_filename": analysis.original_filename,
                    "query": analysis.query,
                    "processing_time": analysis.processing_time,
                    "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                    "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
                }
                for analysis in analyses
            ],
            "total_count": len(analyses)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user analyses: {str(e)}")

@app.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        from sqlalchemy import func
        
        total_users = db.query(func.count(User.id)).scalar()
        total_analyses = db.query(func.count(AnalysisResult.id)).scalar()
        completed_analyses = db.query(func.count(AnalysisResult.id)).filter(
            AnalysisResult.status == "completed"
        ).scalar()
        failed_analyses = db.query(func.count(AnalysisResult.id)).filter(
            AnalysisResult.status == "failed"
        ).scalar()
        
        # Get average processing time
        avg_processing_time = db.query(func.avg(AnalysisResult.processing_time)).filter(
            AnalysisResult.processing_time.is_not(None)
        ).scalar()
        
        return {
            "total_users": total_users,
            "total_analyses": total_analyses,
            "completed_analyses": completed_analyses,
            "failed_analyses": failed_analyses,
            "success_rate": round((completed_analyses / total_analyses * 100), 2) if total_analyses > 0 else 0,
            "average_processing_time": round(float(avg_processing_time), 2) if avg_processing_time else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)