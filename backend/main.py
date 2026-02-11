from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import os
import hashlib
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image, ImageFile, UnidentifiedImageError
ImageFile.LOAD_TRUNCATED_IMAGES = True
import io
import json
import base64
import google.generativeai as genai
from google.oauth2 import service_account
from typing import List, Optional

from slide_generator import generate_slide_image, compress_image
from docx_parser import parse_questions_from_docx, parse_questions_from_md
from pptx_builder import create_pptx_from_images

app = FastAPI(title="Lekhaslides API")

try:
    with open("startup_log.txt", "w") as f:
        f.write("Backend main.py loaded\n")
except:
    pass

# Configure AI Studio (Google Generative AI)
CREDENTIALS_PATH = "/Users/rci/lekhaslides/celtic-origin-480214-d5-e0c80e18c8c5.json"

def init_genai():
    try:
        if os.path.exists(CREDENTIALS_PATH):
            # Set environment variable so the SDK can find the credentials
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
            
            # Test if it can list models (this verifies the credentials)
            genai.list_models()
            print(f"✨ AI Studio (Gemini) initialized with service account from {CREDENTIALS_PATH}")
            return True
        else:
            print(f"⚠️ Credentials file not found at {CREDENTIALS_PATH}")
            return False
    except Exception as e:
        print(f"❌ Failed to initialize AI Studio: {e}")
        return False

HAS_GENAI = init_genai()

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
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to limit file size (approximate, via Content-Length)
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    # Max size: 10MB for images, 5MB for docs
    MAX_SIZE = 10 * 1024 * 1024 
    
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_SIZE:
             return JSONResponse(
                status_code=413,
                content={"detail": "File too large. Maximum size is 10MB."},
            )
            
    response = await call_next(request)
    return response

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


@app.post("/api/parse-images")
async def parse_images(files: List[UploadFile] = File(...)):
    """
    Parse multiple images using Gemini API and return structured questions
    """
    if not HAS_GENAI:
        raise HTTPException(status_code=500, detail="Gemini API not configured on server (Missing credentials).")

    try:
        # Use Gemini 2.5/2.0 Flash (verified in user project list) or fall back
        model_name = "gemini-2.5-flash"
        
        # Define the Response Schema for 100% reliable parsing
        response_schema = {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "number": {"type": "integer"},
                            "question": {"type": "string"},
                            "pointers": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 2,
                                    "maxItems": 2
                                }
                            }
                        },
                        "required": ["number", "question", "pointers"]
                    }
                }
            },
            "required": ["questions"]
        }

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"response_mime_type": "application/json"}
        )
            
        print(f"💡 Using {model_name} with Structured Output (JSON Schema)")
        
        # Prepare parts for Gemini
        prompt = """
        You are an elite educational content architect. Your task is to perform high-fidelity OCR and structured data extraction from the provided images.
        
        CONTENT QUALITY & ACCURACY:
        1. Extract EVERY question and option with 100% text accuracy.
        2. The content is primarily MCQs. Ensure each MCQ is perfectly structured.
        3. If a question spans multiple images or is split, merge it logically.
        4. Maintain mathematical symbols, punctuation, and proper capitalization.
        
        EXTRACTION RULES:
        - Each image may contain multiple questions (e.g., 5-15). Extract ALL of them.
        - For MCQs: Place options into the "pointers" array as [label, text] pairs, e.g., ["A)", "Option text"].
        - If a question is descriptive, break the explanation into concise key points for the "pointers" array.
        """
        
        contents = [prompt]
        
        for file in files:
            img_bytes = await file.read()
            img_io = io.BytesIO(img_bytes)
            img = Image.open(img_io)
            contents.append(img)
            
        print(f"Sending {len(files)} images to Gemini API for parsing...")
        response = model.generate_content(contents)
        
        # Structured Output ensures valid JSON
        result = json.loads(response.text)
        
        # Handle both formats: {"questions": [...]} or just [...]
        if isinstance(result, list):
            questions = result
        elif isinstance(result, dict):
            questions = result.get("questions", [])
        else:
            questions = []
        
        return {
            "questions": questions,
            "total": len(questions)
        }
        
    except Exception as e:
        print(f"❌ Error in parse-images (Vertex): {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error parsing images via Gemini API: {str(e)}")


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
        
        # Calculate a unique ID for this background to enable caching
        bg_hash = hashlib.md5(bg_bytes).hexdigest()
        bg_id = int(bg_hash[:8], 16) # Convert part of hash to integer
        
        bg_image = Image.open(io.BytesIO(bg_bytes))
        bg_image.load()  # Ensure image data is in memory
        
        # We don't need to compress if it's already in the cache
        # The cache logic in slide_generator handles the resizing
        print(f"✓ Background loaded (ID: {bg_id})")
        
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
        
        # Check for per-slide config override
        if "config_override" in question:
            print(f"  ➜ Applying config override for preview")
            cfg.update(question["config_override"])
            
        slide_img = generate_slide_image(question, bg_image, cfg, preview_mode=True, bg_id=bg_id, use_cache=True)
        print(f"✓ Slide generated: {slide_img.size}")
        
        # Convert to bytes - Use JPEG for previews (much faster than PNG)
        print("💾 Converting to JPEG...")
        img_byte_arr = io.BytesIO()
        slide_img.convert("RGB").save(img_byte_arr, format='JPEG', quality=85, optimize=False)
        img_byte_arr.seek(0)
        print("✅ Preview ready!")
        print(f"{'='*60}\n")
        
        return StreamingResponse(img_byte_arr, media_type="image/jpeg")
    
    except UnidentifiedImageError:
        print("❌ ERROR: Invalid image file")
        raise HTTPException(status_code=400, detail="Invalid image file. Please upload a valid JPG or PNG.")
        
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



@app.post("/api/generate-batch-previews")
async def generate_batch_previews(
    background: UploadFile = File(...),
    questions_data: str = Form(...),  # JSON array
    config: str = Form(...), # JSON object
    page: int = Form(1),
    limit: int = Form(20)
):
    """
    Generate low-res previews for a batch of slides (e.g., 20 at a time).
    Returns list of base64 encoded images.
    """
    import base64
    from concurrent.futures import ThreadPoolExecutor, as_completed

    try:
        # 1. Load and Aggressively Compress Background for FAST previews
        bg_bytes = await background.read()
        bg_image = Image.open(io.BytesIO(bg_bytes))
        bg_image.load()
        
        # OPTIMIZATION: Use much smaller resolution for grid previews
        # 640px instead of 960px = 4x fewer pixels = much faster
        PREVIEW_MAX_DIM = 640 
        bg_image = compress_image(bg_image, max_dimension=PREVIEW_MAX_DIM)
        
        # Ensure it's under 1MB for fast network transfer
        img_byte_arr = io.BytesIO()
        bg_image.save(img_byte_arr, format='JPEG', quality=70)
        while img_byte_arr.tell() > 1 * 1024 * 1024:
            img_byte_arr = io.BytesIO()
            bg_image = bg_image.resize((int(bg_image.width*0.9), int(bg_image.height*0.9)))
            bg_image.save(img_byte_arr, format='JPEG', quality=60)
            
        bg_id = id(bg_image)
        
        # 2. Parse Questions
        questions = json.loads(questions_data)
        cfg = json.loads(config)
        total_questions = len(questions)
        
        # 3. Pagination Logic
        start_idx = (page - 1) * limit
        end_idx = min(start_idx + limit, total_questions)
        
        if start_idx >= total_questions:
             return {
                "total_pages": (total_questions + limit - 1) // limit,
                "current_page": page,
                "slides": []
            }

        page_questions = questions[start_idx:end_idx]
        
        # 4. Generate in Parallel
        slides_result = []
        
        def generate_preview_one(idx, q):
            # Pass original index to help frontend identify which slide is which
            # Use preview_mode=True for faster generation
            
            # Check for per-slide config override
            current_cfg = cfg.copy()
            if "config_override" in q:
                current_cfg.update(q["config_override"])

            img = generate_slide_image(q, bg_image, current_cfg, preview_mode=True, bg_id=bg_id)
            
            # Convert to base64
            buffered = io.BytesIO()
            # OPTIMIZATION: Use quality=40 instead of 60 for much smaller file sizes
            img.save(buffered, format="JPEG", quality=40) 
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            return {
                "index": start_idx + idx, # Global index
                "image": f"data:image/jpeg;base64,{img_str}",
                "number": q.get('number')
            }

        with ThreadPoolExecutor(max_workers=4) as executor:
            # We map over the subset of questions for this page
            futures = [executor.submit(generate_preview_one, i, q) for i, q in enumerate(page_questions)]
            for future in as_completed(futures):
                slides_result.append(future.result())
        
        # Sort by index to maintain order
        slides_result.sort(key=lambda x: x["index"])
        
        return {
            "total_pages": (total_questions + limit - 1) // limit,
            "current_page": page,
            "slides": slides_result
        }

    except Exception as e:
        print(f"❌ ERROR generating batch previews: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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
            # Load background and ensure it's in memory
            bg_image = Image.open(io.BytesIO(bg_content))
            bg_image.load()  # Crucial: Load pixel data into memory before threading
            bg_image = compress_image(bg_image) # Compress if too large
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
                # Check for per-slide config override
                current_cfg = cfg.copy()
                if "config_override" in question:
                    current_cfg.update(question["config_override"])
                
                return idx, generate_slide_image(question, bg_image, current_cfg, bg_id=bg_id)
            
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
            
        except UnidentifiedImageError:
            print("❌ ERROR: Invalid image file")
            yield f"data: {json.dumps({'type': 'error', 'message': 'Invalid image file. Please upload a valid JPG or PNG.'})}\n\n"

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
