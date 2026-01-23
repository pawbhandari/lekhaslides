from docx import Document
import re
import io
from typing import List, Dict

def parse_questions_from_docx(file_content: bytes) -> List[Dict]:
    """
    Parse questions from .docx bytes
    
    Returns list of:
    {
        "number": 1,
        "question": "Define Strategic Cost Management...",
        "pointers": [
            ["Definition:", "SCM is the proactive use..."],
            ["Strategic Focus:", "It shifts the focus..."]
        ]
    }
    """
    doc = Document(io.BytesIO(file_content))
    questions = []
    current_q = None
    
    print(f"\n{'='*60}")
    print(f"📄 PARSING DOCX - Found {len(doc.paragraphs)} paragraphs")
    print(f"{'='*60}")
    
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue
        
        if i < 20:  # Show first 20 paragraphs for debugging
            print(f"Para {i}: {text[:100]}")
        
        # Detect question line: "**1. Question..." or "1. Question..." or "**1 Question..."
        # Remove markdown bold markers first
        clean_text = text.replace('**', '').replace('*', '').strip()
        match = re.match(r'^(\d+)\.?\s*(.+)', clean_text)
        if match:
            if current_q:
                questions.append(current_q)
            
            num = int(match.group(1))
            q_text = match.group(2).strip()
            print(f"✓ Found Question {num}: {q_text[:50]}...")
            current_q = {
                "number": num,
                "question": q_text,
                "pointers": []
            }
            continue
        
        # Bullet point under current question
        if current_q:
            bullet_text = text.lstrip('-•*').strip()
            if bullet_text:
                # Split by first colon to separate label from body
                if ':' in bullet_text:
                    parts = bullet_text.split(':', 1)
                    label = parts[0].strip() + ':'
                    body = parts[1].strip()
                    current_q["pointers"].append([label, body])
                else:
                    # No colon, treat entire text as body with empty label
                    current_q["pointers"].append(['', bullet_text])
    
    # Append last question
    if current_q:
        questions.append(current_q)
    
    print(f"\n✅ Parsing complete: Found {len(questions)} questions")
    print(f"{'='*60}\n")
    
    return questions
