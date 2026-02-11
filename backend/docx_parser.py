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

def clean_markdown_artifacts(text: str) -> str:
    """
    Remove common markdown artifacts and clean text.
    Removes: **, *, __, _, and trims whitespace.
    """
    # Replace markdown symbols with empty or space if needed
    # We want to remove the symbols but keep the text
    text = text.replace('**', '').replace('__', '') # Bold
    text = text.replace('*', '').replace('_', '')   # Italic/Bullet
    return text.strip()

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
        # Clean artifacts for question detection
        clean_text = clean_markdown_artifacts(text)
        
        # Check for Question (Flexible regex: 1., 1), 1:, Question 1:, etc.)
        match = re.match(r'^(?:Question\s*)?(\d+)\s*[:.\)]\s*(.+)', clean_text, re.IGNORECASE)
        # Fallback for just digit at start if it's short or follows a pattern
        if not match:
            match = re.match(r'^(\d+)\.?\s+(.+)', clean_text)
            
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
            # First clean line start bullets for detection
            bullet_text = text.lstrip('-•*').strip()
            
            if bullet_text:
                # Then clean artifacts from the content
                clean_body_text = clean_markdown_artifacts(bullet_text)
                
                if ':' in clean_body_text and not clean_body_text.startswith('http'):
                     # Simple heuristic: colon separates label from body
                    parts = clean_body_text.split(':', 1)
                    
                    label = parts[0].strip() + ':'
                    body = parts[1].strip()
                    
                    current_q["pointers"].append([label, body])
                else:
                    current_q["pointers"].append(['', clean_body_text])
    
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
        auto_num_counter = 1
        for p in paragraphs:
            # Check for numbering properties (auto-numbering)
            num_pr = p.find('w:pPr/w:numPr', ns)
            is_auto_numbered = num_pr is not None
            ilvl = "0"
            if is_auto_numbered:
                ilvl_node = num_pr.find('w:ilvl', ns)
                if ilvl_node is not None:
                    ilvl = ilvl_node.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', "0")

            texts = [t.text for t in p.iterfind('.//w:t', ns) if t.text]
            full_text = ''.join(texts).strip()
            
            if not full_text:
                continue
                
            # If it's auto-numbered at level 0 and doesn't already start with a number
            # prepend a number so the parser identifies it as a question
            if is_auto_numbered and ilvl == "0" and not re.match(r'^\d+', full_text):
                full_text = f"{auto_num_counter}. {full_text}"
                auto_num_counter += 1
            
            yield full_text

    return parse_lines(xml_lines_generator())

def slow_parse_fallback(file_content: bytes) -> List[Dict]:
    """
    Original parsing logic using python-docx
    """
    import zipfile
    try:
        doc = Document(io.BytesIO(file_content))
        print(f"📄 FALLBACK PARSING DOCX - Found {len(doc.paragraphs)} paragraphs")
        
        def slow_lines_generator():
            auto_num_counter = 1
            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue
                
                # Detect auto-numbering in python-docx
                is_auto_numbered = False
                ilvl = 0
                try:
                    if p._element.pPr is not None and p._element.pPr.numPr is not None:
                        is_auto_numbered = True
                        if p._element.pPr.numPr.ilvl is not None:
                            ilvl = p._element.pPr.numPr.ilvl.val
                except AttributeError:
                    pass
                
                if is_auto_numbered and ilvl == 0 and not re.match(r'^\d+', text):
                    text = f"{auto_num_counter}. {text}"
                    auto_num_counter += 1
                
                yield text

        return parse_lines(slow_lines_generator())
    except (zipfile.BadZipFile, Exception) as e:
        print(f"❌ Docx parsing failed completely: {e}")
        # Final attempt: Treat as raw text if it's not a zip, BUT with safety check
        try:
            # Check if it's binary data (like an image) - check for null bytes
            if b'\x00' in file_content[:1024]:
                raise Exception("Binary data detected (might be an image). Please upload images in the 'Images' tab.")

            try:
                text_content = file_content.decode('utf-8')
            except:
                text_content = file_content.decode('latin-1')
            
            # Additional safety: check ratio of printable characters
            printable = sum(1 for c in text_content[:500] if c.isprintable() or c.isspace())
            if printable / min(len(text_content), 500) < 0.8:
                raise Exception("Content does not appear to be text. If this is a question sheet image, use the 'Images' tab.")

            print("💡 Treating failing docx as raw text")
            return parse_questions_from_md(text_content)
        except Exception as inner_e:
            raise Exception(f"File is not a valid document. {str(inner_e)}")

