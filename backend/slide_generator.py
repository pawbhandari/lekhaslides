from PIL import Image, ImageDraw, ImageFont
import os
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
        background: PIL Image
        config: {
            "instructor_name": str, 
            "subtitle": str, 
            "badge_text": str,
            "font_size_heading": int,
            "font_size_body": int,
            "font_text_color": str,
            "pos_x": int,
            "pos_y": int
        }
    
    Returns:
        PIL Image (1920x1080)
    """
    
    # Resize background to 16:9 (1920x1080) with high quality
    bg = background.resize((1920, 1080), Image.Resampling.LANCZOS).convert("RGB")
    
    # Optional: Compress in memory if needed (not strictly necessary for drawing, 
    # but good practice if we were saving repeatedly. For drawing, we keep full quality in memory).
    
    draw = ImageDraw.Draw(bg, "RGBA")
    
    # Configurable Layout Parameters
    FONT_SIZE_HEADING = int(config.get('font_size_heading', 60))
    FONT_SIZE_BODY = int(config.get('font_size_body', 28))
    TEXT_COLOR = config.get('font_text_color', '#F0C83C') # Default Yellow
    POS_OFFSET_X = int(config.get('pos_x', 0))
    POS_OFFSET_Y = int(config.get('pos_y', 0))

    # Load fonts with fallback
    try:
        # PWD should be /Users/rci/Documents/lekhaslides/backend or similar
        # We try to find the font in logical places
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base_dir, "fonts", "PatrickHand-Regular.ttf")
        
        if not os.path.exists(font_path):
             # Fallback to system font if Patrick Hand isn't there
            font_path = "/System/Library/Fonts/Supplemental/Chalkboard.ttc"
            
        font_heading = ImageFont.truetype(font_path, FONT_SIZE_HEADING)
        font_subtitle = ImageFont.truetype(font_path, int(FONT_SIZE_HEADING * 0.5)) # subtitle relative to heading
        font_question = ImageFont.truetype(font_path, int(FONT_SIZE_HEADING * 0.8)) # question slightly smaller
        font_bullet = ImageFont.truetype(font_path, FONT_SIZE_BODY)
        font_label = ImageFont.truetype(font_path, int(FONT_SIZE_BODY * 1.1)) # label slightly larger
        
    except Exception as e:
        print(f"⚠️ Could not load custom/system font: {e}")
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
    
    # Parse custom text color from hex
    try:
        if TEXT_COLOR.startswith('#'):
            # Convert hex to RGB
            custom_color = tuple(int(TEXT_COLOR[i:i+2], 16) for i in (1, 3, 5))
        else:
            custom_color = YELLOW
    except:
        custom_color = YELLOW

    # Margins
    margin_left = 80 + POS_OFFSET_X
    margin_top = 60 + POS_OFFSET_Y
    width_limit = 1920 - 80 # Just a safe right boundary
    
    # Wrap width calculation
    # available width = total width - left margin - right margin
    # We keep right margin static from the edge, but left margin moves with offset
    content_width = width_limit - margin_left
    
    # === HEADER ===
    # Instructor name (top-left)
    draw.text((margin_left, margin_top), config.get('instructor_name', ''), 
              font=font_heading, fill=custom_color)
    
    # Subtitle (below name)
    draw.text((margin_left, margin_top + FONT_SIZE_HEADING + 10), config.get('subtitle', ''),
              font=font_subtitle, fill=MINT_GREEN)
    
    # Badge (top-right) - fixed position usually, but let's move it with Y offset maybe? 
    # Or keep it static. Let's keep badge static X but moving Y to align with header row.
    badge_width = 350
    badge_height = 70
    badge_x = 1920 - 80 - badge_width # Fixed right margin
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
    badge_font = ImageFont.truetype(font_path, 24) if 'font_path' in locals() else font_subtitle
    draw.text((badge_x + badge_width//2, badge_y + badge_height//2),
              config.get('badge_text', ''), font=badge_font, fill=DARK, anchor="mm")
    
    # === QUESTION ===
    # Position question below header (approx 200px gap in original, let's make it relative)
    question_y = margin_top + FONT_SIZE_HEADING + 100 
    question_text = f"Ques {question['number']} => {question['question']}"
    question_lines = wrap_text(question_text, content_width, font_question, draw)
    
    for i, line in enumerate(question_lines):
        draw.text((margin_left, question_y + i * (font_question.size * 1.2)), line,
                  font=font_question, fill=ORANGE)
    
    # === ANSWER LABEL ===
    answer_y = question_y + len(question_lines) * (font_question.size * 1.2) + 40
    draw.text((margin_left, answer_y), "Answer –", font=font_bullet, fill=WHITE)
    
    # === BULLET POINTS ===
    bullet_y = answer_y + (font_bullet.size * 1.5)
    bullet_indent = 40
    line_spacing = font_bullet.size * 1.5
    
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
        available_width = 1920 - 80 - body_x
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

    # === WATERMARK (Bottom Right) ===
    watermark_text = config.get('watermark_text', '')
    if watermark_text:
        # Reuse subtitle font or load new one
        watermark_font = ImageFont.truetype(font_path, 30) if 'font_path' in locals() else font_subtitle
        
        # Calculate size
        bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
        w_width = bbox[2] - bbox[0]
        w_height = bbox[3] - bbox[1]
        
        # Position at bottom right with margins
        # 1920 width, 1080 height
        # Margin right 80, Margin bottom 60
        wx = 1920 - 80 - w_width
        wy = 1080 - 60 - w_height
        
        # Draw watermark
        draw.text((wx, wy), watermark_text, font=watermark_font, fill=custom_color)
    
    return bg
