from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import uuid
import asyncio

from crewai import Crew, Process
from agents import financial_analyst
from task import analyze_financial_document as analyze_task

app = FastAPI(title="Financial Document Analyzer")

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
    return {"message": "Financial Document Analyzer API is running"}

@app.post("/analyze")
async def analyze_financial_document(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    """Analyze financial document and provide comprehensive investment recommendations"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    
    try:
        # Create data directory
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            if not content:
                raise HTTPException(status_code=400, detail="Uploaded file is empty")
            f.write(content)
        
        # Set default query if empty
        if not query or not query.strip():
            query = "Analyze this financial document for investment insights"
        
        # Extract text from PDF
        document_text = _extract_pdf_text(file_path)
        
        if not document_text.strip():
            raise HTTPException(
                status_code=400, 
                detail="Uploaded PDF contains no readable text"
            )

        # Run the crew analysis
        response = await asyncio.to_thread(run_crew, query.strip(), document_text)

        return {
            "status": "success",
            "query": query,
            "analysis": str(response),
            "file_processed": file.filename,
            "document_length": len(document_text)
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error processing document: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing financial document: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not remove temporary file {file_path}: {cleanup_error}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)