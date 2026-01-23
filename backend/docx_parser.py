from docx import Document
import re
import io
import time
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict

def parse_questions_from_docx(file_content: bytes) -> List[Dict]:
    """
    Parse questions from .docx bytes.
    Tries fast XML parsing first, falls back to python-docx if that fails.
    """
    start_time = time.time()
    try:
        print(f"\n{'='*60}")
        print("🚀 STARTING FAST PARSE")
        questions = fast_parse_xml(file_content)
        print(f"✅ Fast XML parsing completed in {time.time() - start_time:.4f}s")
        print(f"Found {len(questions)} questions")
        print(f"{'='*60}\n")
        return questions
    except Exception as e:
        print(f"⚠️ Fast parsing failed: {e}")
        print("Falling back to python-docx (slower)...")
        return slow_parse_fallback(file_content)

def parse_lines(lines_iterator) -> List[Dict]:
    """
    Shared logic to parse lines of text into questions.
    """
    questions = []
    current_q = None
    
    for text in lines_iterator:
        text = text.strip()
        if not text:
            continue
            
        clean_text = text.replace('**', '').replace('*', '').strip()
        
        # Check for Question
        match = re.match(r'^(\d+)\.?\s*(.+)', clean_text)
        if match:
            if current_q:
                questions.append(current_q)
            
            num = int(match.group(1))
            q_text = match.group(2).strip()
            
            current_q = {
                "number": num,
                "question": q_text,
                "pointers": []
            }
            continue
        
        # Check for pointers
        if current_q:
            bullet_text = text.lstrip('-•*').strip()
            if bullet_text:
                if ':' in bullet_text and not bullet_text.startswith('http'):
                     # Simple heuristic: colon separates label from body
                     # Avoid http: links being treated as labels
                    parts = bullet_text.split(':', 1)
                    label = parts[0].strip() + ':'
                    body = parts[1].strip()
                    current_q["pointers"].append([label, body])
                else:
                    current_q["pointers"].append(['', bullet_text])
    
    if current_q:
        questions.append(current_q)
        
    return questions

def parse_questions_from_md(md_content: str) -> List[Dict]:
    """Parse questions from markdown text string"""
    return parse_lines(md_content.splitlines())

def fast_parse_xml(file_content: bytes) -> List[Dict]:
    # Open docx as zip
    with zipfile.ZipFile(io.BytesIO(file_content)) as z:
        xml_content = z.read('word/document.xml')
    
    # Parse XML
    root = ET.fromstring(xml_content)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    body = root.find('w:body', ns)
    if body is None:
        return []

    paragraphs = body.findall('w:p', ns)
    print(f"Processing {len(paragraphs)} paragraphs via XML...")

    def xml_lines_generator():
        for p in paragraphs:
            texts = [t.text for t in p.iterfind('.//w:t', ns) if t.text]
            yield ''.join(texts)

    return parse_lines(xml_lines_generator())

def slow_parse_fallback(file_content: bytes) -> List[Dict]:
    """
    Original parsing logic using python-docx
    """
    doc = Document(io.BytesIO(file_content))
    print(f"📄 FALLBACK PARSING DOCX - Found {len(doc.paragraphs)} paragraphs")
    
    return parse_lines((p.text for p in doc.paragraphs))

