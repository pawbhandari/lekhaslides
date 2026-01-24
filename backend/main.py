from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import io
from typing import List
import json

from slide_generator import generate_slide_image
from docx_parser import parse_questions_from_docx, parse_questions_from_md
from pptx_builder import create_pptx_from_images

app = FastAPI(title="Lekhaslides API")

try:
    with open("startup_log.txt", "w") as f:
        f.write("Backend main.py loaded\n")
except:
    pass

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    import datetime
    try:
        with open("validation_error_log.txt", "w") as f:
            f.write(f"Timestamp: {datetime.datetime.now()}\n")
            f.write(f"URL: {request.url}\n")
            f.write(f"Errors: {str(exc.errors())}\n")
    except:
        pass
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/parse-docx")
async def parse_docx(file: UploadFile = File(...)):
    try:
        with open("parse_request_log.txt", "a") as f:
            import datetime
            f.write(f"{datetime.datetime.now()}: Parse Request Received\n")
    except:
        pass
    """
    Parse .docx or .md/.txt file and return structured questions
    
    Returns: 
    {
        "questions": [
            {
                "number": 1,
                "question": "Define Strategic Cost Management...",
                "pointers": [
                    ["Definition:", "SCM is the proactive use..."],
                    ["Strategic Focus:", "It shifts the focus..."]
                ]
            }
        ],
        "total": 12
    }
    """
    try:
        filename = file.filename.lower()
        if filename.endswith('.gdoc'):
             raise HTTPException(status_code=400, detail="Google Docs shortcut files (.gdoc) cannot be processed directly. Please open the document in Google Docs, go to File > Download > Microsoft Word (.docx), and upload that file.")

        content = await file.read()
        
        if filename.endswith('.md') or filename.endswith('.txt'):
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                text_content = content.decode('latin-1')
            
            questions = parse_questions_from_md(text_content)
        else:
            # Default to docx
            questions = parse_questions_from_docx(content)
        
        return {
            "questions": questions,
            "total": len(questions)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing docx: {str(e)}")


@app.post("/api/parse-text")
async def parse_text(text: str = Form(...)):
    """
    Parse raw text input directly
    """
    try:
        print(f"Parsing raw text input: {len(text)} chars")
        questions = parse_questions_from_md(text)
        return {
            "questions": questions,
            "total": len(questions)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing text: {str(e)}")


@app.post("/api/generate-preview")
async def generate_preview(
    background: UploadFile = File(...),
    question_data: str = Form(...),  # JSON string
    config: str = Form(...)  # JSON string with instructor_name, subtitle, badge_text
):
    """
    Generate preview image for first question
    
    Returns: PNG image
    """
    print(f"\n{'='*60}")
    print("📸 GENERATING PREVIEW")
    try:
        with open("request_log.txt", "a") as f:
            import datetime
            f.write(f"{datetime.datetime.now()}: Preview Request Received\n")
            
        print(f"{'='*60}")
        print(f"{'='*60}")
        
        # Load background image
        print("📁 Loading background image...")
        bg_bytes = await background.read()
        bg_image = Image.open(io.BytesIO(bg_bytes))
        print(f"✓ Background loaded: {bg_image.size}")
        
        # Parse JSON data
        print("📋 Parsing question data...")
        print(f"DEBUG: question_data raw value: {repr(question_data[:200] if len(question_data) > 0 else 'EMPTY')}")
        print(f"DEBUG: config raw value: {repr(config[:200] if len(config) > 0 else 'EMPTY')}")
        question = json.loads(question_data)
        cfg = json.loads(config)
        print(f"✓ Question {question.get('number')}: {question.get('question', '')[:50]}...")
        print(f"✓ Config: {cfg.get('instructor_name')}")
        
        # Generate slide
        print("🎨 Generating slide image...")
        slide_img = generate_slide_image(question, bg_image, cfg, preview_mode=True, use_cache=False)
        print(f"✓ Slide generated: {slide_img.size}")
        
        # Convert to bytes
        print("💾 Converting to PNG...")
        img_byte_arr = io.BytesIO()
        slide_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        print("✅ Preview ready!")
        print(f"{'='*60}\n")
        
        return StreamingResponse(img_byte_arr, media_type="image/png")
        
    except Exception as e:
        print(f"❌ ERROR generating preview: {str(e)}")
        import traceback
        import datetime
        traceback.print_exc()
        
        # Write to log file for debugging
        try:
            with open("error_log.txt", "w") as f: # Overwrite to get latest
                f.write(f"Timestamp: {datetime.datetime.now()}\n")
                f.write(f"Error: {str(e)}\n")
                traceback.print_exc(file=f)
        except:
             pass
             
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")


@app.post("/api/generate-pptx")
async def generate_pptx(
    background: UploadFile = File(...),
    questions_data: str = Form(...),  # JSON array
    config: str = Form(...)
):
    """
    Generate complete PPTX with all slides - Returns Server-Sent Events for progress,
    then the final PPTX as a base64 encoded payload.
    """
    import base64
    from fastapi.responses import StreamingResponse
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # Read file immediately to prevent context loss
    bg_content = await background.read()
    
    async def generate_with_progress():
        try:
            # Load background
            bg_image = Image.open(io.BytesIO(bg_content))
            bg_id = id(bg_image)  # Unique ID for caching
            
            # Parse data
            questions = json.loads(questions_data)
            cfg = json.loads(config)
            total = len(questions)
            
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'total': total})}\n\n"
            
            # Generate slides with parallel processing for speed
            slide_images = [None] * total
            completed = 0
            
            # Use ThreadPool for parallel generation (with caching, this is very fast)
            def generate_one(idx_question):
                idx, question = idx_question
                return idx, generate_slide_image(question, bg_image, cfg, bg_id=bg_id)
            
            # Process in batches of 4 for parallelism
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(generate_one, (i, q)): i 
                          for i, q in enumerate(questions)}
                
                for future in as_completed(futures):
                    idx, img = future.result()
                    slide_images[idx] = img
                    completed += 1
                    
                    # Send progress event
                    progress = {"type": "progress", "current": completed, "total": total, "percent": round((completed/total)*100)}
                    yield f"data: {json.dumps(progress)}\n\n"
            
            # Build PPTX
            pptx_bytes_io = create_pptx_from_images(slide_images)
            pptx_bytes = pptx_bytes_io.read()
            
            # Encode as base64 for SSE delivery
            b64_pptx = base64.b64encode(pptx_bytes).decode('utf-8')
            
            # Send complete event with the file
            yield f"data: {json.dumps({'type': 'complete', 'file': b64_pptx})}\n\n"
            
            # Clear caches after generation
            from slide_generator import clear_caches
            clear_caches()
            
        except Exception as e:
            print(f"❌ ERROR generating PPTX: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_with_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
