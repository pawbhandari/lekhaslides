from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import os
import logging
import asyncio
import datetime
import traceback
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image, ImageFile, UnidentifiedImageError
ImageFile.LOAD_TRUNCATED_IMAGES = True
import io
import json
import base64
import google.generativeai as genai
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from slide_generator import generate_slide_image, compress_image
from docx_parser import parse_questions_from_docx, parse_questions_from_md
from pptx_builder import create_pptx_from_images

# Configure logging
logger = logging.getLogger("lekhaslides")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="Lekhaslides API")

try:
    with open("startup_log.txt", "w") as f:
        f.write("Backend main.py loaded\n")
except Exception:
    pass

# Configure AI Studio (Google Generative AI)
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

def init_genai():
    try:
        # Priority 1: Service Account JSON
        if CREDENTIALS_PATH and os.path.exists(CREDENTIALS_PATH):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
            # Debug: verify which account is in the file
            try:
                with open(CREDENTIALS_PATH, 'r') as f:
                    creds_data = json.load(f)
                    email = creds_data.get('client_email', 'unknown')
                    logger.info(f"AI Studio (Gemini) initialized with Service Account: {email}")
            except Exception:
                logger.info(f"AI Studio (Gemini) initialized with Service Account from path: {CREDENTIALS_PATH}")
            return True
        
        # Priority 2: API Key string (Common for Render/Simple Deployments)
        elif GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            logger.info(f"AI Studio (Gemini) initialized with API Key")
            return True
            
        elif CREDENTIALS_PATH:
            logger.warning(f"Credentials file not found at path from GOOGLE_APPLICATION_CREDENTIALS")
            return False
        else:
            logger.warning("Neither GOOGLE_APPLICATION_CREDENTIALS nor GOOGLE_API_KEY set. AI features disabled.")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize AI Studio: {e}")
        return False

HAS_GENAI = init_genai()

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# CORS for React frontend
ALLOWED_ORIGINS = ["https://lekhaslides-frontend.onrender.com", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
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

# Allowed file extensions for document parsing
ALLOWED_DOC_EXTENSIONS = {'.docx', '.md', '.txt'}
MAX_IMAGE_UPLOAD_COUNT = 20

def extract_text_from_file(content: bytes, filename: str) -> str:
    """
    Extract raw text from a file (docx, md, txt).
    For docx: extracts all paragraph text with line breaks preserved.
    For md/txt: decodes bytes to string.
    """
    filename = filename.lower()
    
    if filename.endswith('.md') or filename.endswith('.txt'):
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return content.decode('latin-1')
    
    # For docx: extract text using python-docx, preserving paragraph structure
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        lines = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                lines.append(text)
        return '\n'.join(lines)
    except Exception as e:
        logger.warning(f"Failed to extract text from docx: {e}")
        # Fallback: try as raw text
        try:
            return content.decode('utf-8')
        except Exception:
            return content.decode('latin-1')


async def ai_parse_text(raw_text: str) -> List[Dict]:
    """
    Use Gemini to parse raw text into structured questions.
    Returns a list of question dicts with {number, question, pointers}.
    """
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={"response_mime_type": "application/json"}
    )
    
    prompt = """You are an expert educational content parser. Parse the following raw text into structured JSON questions.

OUTPUT FORMAT: Return a JSON object with a "questions" array. Each question must have:
- "number": integer (question number, starting from 1)
- "question": string (the full question text, including any inline math)
- "pointers": array of [label, text] pairs

CRITICAL RULES FOR MCQ OPTIONS:
- The "label" (first element) must ONLY be the option letter+bracket, e.g.: "A)", "B)", "C)", "D)"
- The "text" (second element) is the full option content
- NEVER put the option content in the label field
- NEVER put the option letter in the text field with empty label

CORRECT example:
  {"number": 1, "question": "What is 2+2?", "pointers": [["A)", "3"], ["B)", "4"], ["C)", "5"], ["D)", "6"]]}

FOR NON-MCQ QUESTIONS (with bullet points or definitions):
- Use the label for the category/key (e.g. "Definition:", "Key Point:")
- Use the text for the explanation/value
- If there's no label, use an empty string as label

MATH FORMATTING:
- Use $...$ for ALL inline math expressions (fractions, inequalities, etc.)
- Ensure \\frac, \\leq, \\geq, \\infty, \\left, \\right etc. are correctly formatted

QUESTION TEXT:
- Always extract the complete question text into the "question" field
- The "question" field must NEVER be empty
- For MCQs, the question field is the stem (everything before A/B/C/D options)
- Do NOT include options (A, B, C, D) in the question text

IMPORTANT:
- Extract EVERY question from the text, do not skip any
- Maintain the original question numbering if present
- If options are on the same line as the question, split them correctly

Here is the text to parse:

"""
    
    logger.info(f"Sending {len(raw_text)} chars to Gemini for AI parsing...")
    
    # Use asyncio-friendly timeout to avoid blocking the event loop
    import functools
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, functools.partial(model.generate_content, prompt + raw_text)),
            timeout=60
        )
    except asyncio.TimeoutError:
        raise Exception("AI parsing timed out after 60 seconds")
    
    # Safely parse AI response
    try:
        result = json.loads(response.text)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Gemini returned invalid JSON: {e}. Response text: {response.text[:200]}")
        raise Exception("AI returned invalid response format. Please try again.")
    
    if isinstance(result, list):
        questions = result
    elif isinstance(result, dict):
        questions = result.get("questions", [])
    else:
        questions = []
    
    # Post-process: fix common AI output mistakes
    questions = sanitize_questions(questions)
    
    logger.info(f"AI parsed {len(questions)} questions successfully")
    return questions


@app.post("/api/parse-docx")
async def parse_docx(file: UploadFile = File(...)):
    logger.info(f"Parse request received: {file.filename}")
    """
    Parse .docx or .md/.txt file and return structured questions.
    Uses AI (Gemini) for parsing with regex fallback.
    """
    try:
        filename = file.filename.lower() if file.filename else ""
        if filename.endswith('.gdoc'):
             raise HTTPException(status_code=400, detail="Google Docs shortcut files (.gdoc) cannot be processed directly. Please open the document in Google Docs, go to File > Download > Microsoft Word (.docx), and upload that file.")

        # Validate file extension
        ext = os.path.splitext(filename)[1]
        if ext and ext not in ALLOWED_DOC_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_DOC_EXTENSIONS)}")

        content = await file.read()
        
        # Primary: regex-based parsing (fast and reliable with br-aware XML parser)
        logger.info("Using regex-based parsing (primary)")
        if filename.endswith('.md') or filename.endswith('.txt'):
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                text_content = content.decode('latin-1')
            questions = parse_questions_from_md(text_content)
        else:
            questions = parse_questions_from_docx(content)
        
        if questions:
            logger.info(f"Regex parsed {len(questions)} questions")
            return {
                "questions": questions,
                "total": len(questions)
            }
        
        # Fallback: AI-powered parsing (if regex found nothing)
        logger.info("Regex found 0 questions, trying AI parsing...")
        if HAS_GENAI:
            try:
                raw_text = extract_text_from_file(content, filename)
                logger.info(f"Extracted {len(raw_text)} chars from {filename}")
                questions = await ai_parse_text(raw_text)
                if questions:
                    return {
                        "questions": questions,
                        "total": len(questions)
                    }
            except Exception as e:
                logger.warning(f"AI parsing also failed: {e}")
        
        return {
            "questions": [],
            "total": 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing docx: {e}")
        raise HTTPException(status_code=400, detail=f"Error parsing document: {str(e)}")


@app.post("/api/parse-text")
async def parse_text(text: str = Form(...)):
    """
    Parse raw text input directly. Uses AI parsing with regex fallback.
    """
    try:
        logger.info(f"Parsing raw text input: {len(text)} chars")
        
        # Try AI parsing first
        if HAS_GENAI:
            try:
                questions = await ai_parse_text(text)
                if questions:
                    return {
                        "questions": questions,
                        "total": len(questions)
                    }
            except Exception as e:
                logger.warning(f"AI text parsing failed, falling back to regex: {e}")
        
        # Fallback: regex
        questions = parse_questions_from_md(text)
        return {
            "questions": questions,
            "total": len(questions)
        }
    except Exception as e:
        logger.error(f"Error parsing text: {e}")
        raise HTTPException(status_code=400, detail=f"Error parsing text: {str(e)}")


def sanitize_questions(questions: list) -> list:
    """
    Post-process AI output to fix common structural mistakes:
    - LaTeX in the label field (should only be option letter like 'A)')
    - Empty question text (extract from first option if possible)
    - Entire option text in label with empty body
    - Malformed pointers
    """
    import re

    # Regex to detect if a string looks like a pure option label: A), B), (A), (a), A., a)
    LABEL_RE = re.compile(r'^[\(\[]?[A-Ea-e][\)\]\.:]?\)?$')
    # Detect if something looks like raw LaTeX (starts with $, \\, or contains \frac etc.)
    LATEX_OR_CONTENT_RE = re.compile(r'(\$|\\frac|\\infty|\\left|\\right|\\alpha|\\leq|\\geq)')

    sanitized = []
    for q in questions:
        if not isinstance(q, dict):
            continue

        number = q.get('number', len(sanitized) + 1)
        question_text = str(q.get('question', '')).strip()
        pointers = q.get('pointers', [])

        # Ensure pointers is a list of [label, text] pairs
        clean_pointers = []
        for p in pointers:
            if not isinstance(p, (list, tuple)) or len(p) < 2:
                continue
            label = str(p[0]).strip()
            body  = str(p[1]).strip()

            # Case 1: label looks like LaTeX/content, body is empty
            # → The AI put the whole option in the label. Move it to body.
            if LATEX_OR_CONTENT_RE.search(label) and not body:
                # Try to extract a real label from the start of what's in label
                m = re.match(r'^([\(\[]?[A-Ea-e][\)\]\.:]\)?)\s*(.*)', label, re.DOTALL)
                if m:
                    label = m.group(1).strip()
                    body = m.group(2).strip()
                else:
                    body = label
                    label = ''

            # Case 2: body contains the label prefix (e.g. body="A) some text", label="")
            if not label and body:
                m = re.match(r'^([\(\[]?[A-Ea-e][\)\]\.:]\)?)\s+(.*)', body, re.DOTALL)
                if m:
                    label = m.group(1).strip()
                    body = m.group(2).strip()

            # Case 3: body is empty but label is a valid option letter — skip empty option
            if label and not body and LABEL_RE.match(label):
                continue  # skip genuinely empty options

            clean_pointers.append([label, body])

        # If question text is empty, try to infer it from context
        if not question_text and clean_pointers:
            # Sometimes the AI puts the question in the first "pointer" with an empty label
            first_label, first_body = clean_pointers[0]
            if not first_label and not LABEL_RE.match(first_label):
                question_text = first_body
                clean_pointers = clean_pointers[1:]

        sanitized.append({
            'number': number,
            'question': question_text,
            'pointers': clean_pointers,
        })

    return sanitized


@app.post("/api/parse-images")
async def parse_images(files: List[UploadFile] = File(...)):
    """
    Parse multiple images using Gemini API and return structured questions
    """
    if not HAS_GENAI:
        raise HTTPException(status_code=500, detail="Gemini API not configured on server (Missing credentials).")

    if len(files) > MAX_IMAGE_UPLOAD_COUNT:
        raise HTTPException(status_code=400, detail=f"Too many images. Maximum {MAX_IMAGE_UPLOAD_COUNT} images allowed per request.")

    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={"response_mime_type": "application/json"}
        )
            
        logger.info(f"Using {model_name} with structured JSON output for {len(files)} images")
        
        prompt = """You are an expert OCR and educational content extraction AI. Extract ALL questions from the provided images into structured JSON.

OUTPUT FORMAT: Return a JSON object with a "questions" array. Each question must have:
- "number": integer (question number)
- "question": string (the full question text, including any inline math)
- "pointers": array of [label, text] pairs

CRITICAL RULES FOR MCQ OPTIONS:
- The "label" (first element) must ONLY be the option letter+bracket, e.g.: "A)", "B)", "C)", "D)"
- The "text" (second element) is the option content (may contain LaTeX)

CORRECT example:
  ["A)", "$(-\\infty, -\\frac{10}{3}]$"]
  ["B)", "$(-\\infty, -\\frac{10}{3})$"]

WRONG (never do this):
  ["$$(-\\infty, -\\frac{10}{3})$$", ""]   ← LaTeX must NEVER be in the label
  ["", "A) some text"]                      ← label must not be empty

MATH FORMATTING:
- Use $...$ for ALL inline math expressions (fractions, inequalities, etc.)
- Use $$...$$ ONLY for standalone display equations on their own line
- Ensure \\frac, \\leq, \\geq, \\infty, \\left, \\right etc. are correctly formatted

QUESTION TEXT:
- Always extract the complete question text into the "question" field
- The "question" field must NEVER be empty if there is a question present
- For MCQs, the question field is the stem (everything before A/B/C/D options)
"""
        
        contents = [prompt]
        
        for file in files:
            img_bytes = await file.read()
            img_io = io.BytesIO(img_bytes)
            img = Image.open(img_io)
            contents.append(img)
            
        logger.info(f"Sending workflow to Gemini ({model_name})...")
        
        # Wrap blocking call in a thread to keep the event loop alive
        import functools
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, functools.partial(model.generate_content, contents)),
            timeout=90
        )
        
        try:
            result = json.loads(response.text)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Gemini returned invalid JSON for images: {e}")
            raise Exception("AI returned invalid response format. Please try again.")
        
        if isinstance(result, list):
            questions = result
        elif isinstance(result, dict):
            questions = result.get("questions", [])
        else:
            questions = []
        
        # Post-process: fix common AI output mistakes
        questions = sanitize_questions(questions)
        
        return {
            "questions": questions,
            "total": len(questions)
        }
        
    except Exception as e:
        logger.error(f"Error in parse-images: {str(e)}", exc_info=True)
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
    logger.info("Generating preview")
    try:
        # Load background image
        bg_bytes = await background.read()
        
        # Use simple hash for caching
        bg_id = hash(bg_bytes[:4096]) & 0xFFFFFFFF
        
        bg_image = Image.open(io.BytesIO(bg_bytes))
        bg_image.load()  # Ensure image data is in memory
        
        # Parse JSON data
        question = json.loads(question_data)
        cfg = json.loads(config)
        logger.info(f"Preview for Q{question.get('number')}: {question.get('question', '')[:50]}")
        
        # Generate slide
        # Check for per-slide config override
        if "config_override" in question:
            cfg.update(question["config_override"])
            
        slide_img = generate_slide_image(question, bg_image, cfg, preview_mode=True, bg_id=bg_id, use_cache=True)
        
        # Convert to bytes - Use JPEG for previews (much faster than PNG)
        img_byte_arr = io.BytesIO()
        slide_img.convert("RGB").save(img_byte_arr, format='JPEG', quality=85, optimize=False)
        img_byte_arr.seek(0)
        logger.info("Preview ready")
        
        return StreamingResponse(img_byte_arr, media_type="image/jpeg")
    
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file. Please upload a valid JPG or PNG.")
        
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}", exc_info=True)
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
        logger.error(f"Error generating batch previews: {str(e)}", exc_info=True)
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
            yield f"data: {json.dumps({'type': 'error', 'message': 'Invalid image file. Please upload a valid JPG or PNG.'})}\n\n"

        except Exception as e:
            logger.error(f"Error generating PPTX: {str(e)}", exc_info=True)
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
