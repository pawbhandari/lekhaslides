from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image
import io
from typing import List
import json

from slide_generator import generate_slide_image
from docx_parser import parse_questions_from_docx, parse_questions_from_md
from pptx_builder import create_pptx_from_images

app = FastAPI(title="Lekhaslides API")

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
    try:
        print(f"\n{'='*60}")
        print("📸 GENERATING PREVIEW")
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
        slide_img = generate_slide_image(question, bg_image, cfg)
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
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")


@app.post("/api/generate-pptx")
async def generate_pptx(
    background: UploadFile = File(...),
    questions_data: str = Form(...),  # JSON array
    config: str = Form(...)
):
    """
    Generate complete PPTX with all slides
    
    Returns: PPTX file for download
    """
    try:
        print(f"\n{'='*60}")
        print("📊 GENERATING COMPLETE PRESENTATION")
        print(f"{'='*60}")
        
        # Load background
        print("📁 Loading background image...")
        bg_bytes = await background.read()
        bg_image = Image.open(io.BytesIO(bg_bytes))
        print(f"✓ Background loaded: {bg_image.size}")
        
        # Parse data
        print("📋 Parsing questions...")
        questions = json.loads(questions_data)
        cfg = json.loads(config)
        print(f"✓ Found {len(questions)} questions to process")
        
        # Generate all slide images
        print("\n🎨 Generating slides:")
        slide_images = []
        for i, question in enumerate(questions, 1):
            print(f"  [{i}/{len(questions)}] Generating slide {question.get('number')}...", end=" ")
            img = generate_slide_image(question, bg_image, cfg)
            slide_images.append(img)
            print("✓")
        
        print(f"✓ All {len(slide_images)} slides generated!")
        
        # Build PPTX
        print("\n📦 Building PowerPoint file...")
        pptx_bytes = create_pptx_from_images(slide_images)
        print("✓ PPTX file created!")
        
        print("\n✅ PRESENTATION COMPLETE!")
        print(f"{'='*60}\n")
        
        return StreamingResponse(
            pptx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": "attachment; filename=Lekhaslides_Presentation.pptx"}
        )
        
    except Exception as e:
        print(f"❌ ERROR generating PPTX: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating PPTX: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
