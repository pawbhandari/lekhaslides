from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple

def wrap_text(text: str, max_width: int, font: ImageFont.FreeTypeFont, 
              draw: ImageDraw.ImageDraw) -> List[str]:
    """Wrap text to fit within max_width pixels"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def generate_slide_image(question: Dict, background: Image.Image, 
                         config: Dict) -> Image.Image:
    """
    Generate slide with text overlay on background
    
    Args:
        question: {"number": 1, "question": "...", "pointers": [["Label:", "text"], ...]}
        background: PIL Image (will be resized to 1920x1080)
        config: {"instructor_name": "...", "subtitle": "...", "badge_text": "..."}
    
    Returns:
        PIL Image (1920x1080)
    """
    
    # Resize background to 16:9
    bg = background.resize((1920, 1080), Image.Resampling.LANCZOS).convert("RGB")
    draw = ImageDraw.Draw(bg, "RGBA")
    
    # Load fonts with fallback
    try:
        # Use macOS system font "Chalkboard"
        font_path = "/System/Library/Fonts/Supplemental/Chalkboard.ttc"
        font_heading = ImageFont.truetype(font_path, 60)
        font_subtitle = ImageFont.truetype(font_path, 28)
        font_question = ImageFont.truetype(font_path, 48)
        font_bullet = ImageFont.truetype(font_path, 28)
        font_label = ImageFont.truetype(font_path, 30)
    except Exception as e:
        print(f"⚠️ Could not load system font: {e}")
        font_heading = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_question = ImageFont.load_default()
        font_bullet = ImageFont.load_default()
        font_label = ImageFont.load_default()
    
    # Colors
    YELLOW = (240, 200, 60)
    MINT_GREEN = (100, 220, 180)
    ORANGE = (255, 180, 80)
    WHITE = (240, 245, 250)
    DARK = (30, 40, 50)
    
    # Margins
    margin_left = 80
    margin_right = 80
    margin_top = 60
    content_width = 1920 - margin_left - margin_right
    
    # === HEADER ===
    # Instructor name (top-left)
    draw.text((margin_left, margin_top), config['instructor_name'], 
              font=font_heading, fill=YELLOW)
    
    # Subtitle (below name)
    draw.text((margin_left, margin_top + 70), config['subtitle'],
              font=font_subtitle, fill=MINT_GREEN)
    
    # Badge (top-right)
    badge_width = 350
    badge_height = 70
    badge_x = 1920 - margin_right - badge_width
    badge_y = margin_top
    
    # Draw rounded rectangle for badge
    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + badge_width, badge_y + badge_height)],
        radius=10,
        fill=ORANGE,
        outline=DARK,
        width=3
    )
    
    # Badge text (centered)
    badge_font = ImageFont.truetype(font_path, 24) if font_heading else font_subtitle
    draw.text((badge_x + badge_width//2, badge_y + badge_height//2),
              config['badge_text'], font=badge_font, fill=DARK, anchor="mm")
    
    # === QUESTION ===
    question_y = margin_top + 200
    question_text = f"Ques {question['number']} => {question['question']}"
    question_lines = wrap_text(question_text, content_width, font_question, draw)
    
    for i, line in enumerate(question_lines):
        draw.text((margin_left, question_y + i * 60), line,
                  font=font_question, fill=ORANGE)
    
    # === ANSWER LABEL ===
    answer_y = question_y + len(question_lines) * 60 + 40
    draw.text((margin_left, answer_y), "Answer –", font=font_bullet, fill=WHITE)
    
    # === BULLET POINTS ===
    bullet_y = answer_y + 60
    bullet_indent = 40
    line_spacing = 50
    
    for label, text in question['pointers']:
        # Bullet marker
        draw.text((margin_left, bullet_y), "•", font=font_bullet, fill=WHITE)
        
        # Label (highlighted in orange)
        label_x = margin_left + bullet_indent
        draw.text((label_x, bullet_y), label, font=font_label, fill=ORANGE)
        
        # Get label width
        label_bbox = draw.textbbox((0, 0), label, font=font_label)
        label_width = label_bbox[2] - label_bbox[0]
        
        # Body text (wrapped)
        body_x = label_x + label_width + 10
        available_width = 1920 - margin_right - body_x
        body_lines = wrap_text(text, available_width, font_bullet, draw)
        
        # First line on same line as label
        if body_lines:
            draw.text((body_x, bullet_y), body_lines[0], font=font_bullet, fill=WHITE)
        
        # Remaining lines below
        for j, body_line in enumerate(body_lines[1:], 1):
            draw.text((body_x, bullet_y + j * line_spacing), body_line,
                      font=font_bullet, fill=WHITE)
        
        # Next bullet
        bullet_y += (len(body_lines) + 1) * line_spacing
    
    return bg
