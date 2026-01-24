from PIL import Image, ImageDraw, ImageFont, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import os
from typing import Dict, List, Tuple
from functools import lru_cache

# Global font cache
_font_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}

def get_cached_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """Get font from cache or load it"""
    key = (font_path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(font_path, size)
    return _font_cache[key]

# Cache for resized backgrounds
_bg_cache: Dict[Tuple[int, int, int], Image.Image] = {}

def get_resized_background(background: Image.Image, width: int, height: int, bg_id: int, use_cache: bool = True) -> Image.Image:
    """Cache resized backgrounds to avoid re-resizing for every slide"""
    if not use_cache:
        resample = Image.Resampling.BILINEAR if width < 1920 else Image.Resampling.LANCZOS
        return background.resize((width, height), resample).convert("RGB")

    key = (bg_id, width, height)
    if key not in _bg_cache:
        resample = Image.Resampling.BILINEAR if width < 1920 else Image.Resampling.LANCZOS
        _bg_cache[key] = background.resize((width, height), resample).convert("RGB")
    return _bg_cache[key].copy()

def clear_caches():
    """Clear all caches - call this between different generation sessions"""
    global _font_cache, _bg_cache
    _font_cache.clear()
    _bg_cache.clear()

def draw_rotated_text(img, text, font, fill_color, x, y, angle):
    """Draw text rotated around its center (CSS-style CW rotation match)"""
    if angle == 0:
        draw = ImageDraw.Draw(img)
        draw.text((x, y), text, font=font, fill=fill_color)
        return

    try:
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except AttributeError:
        # Fallback for old Pillow/DefaultFont
        w, h = font.getsize(text)
    
    # Create temp image large enough
    diag = int((w**2 + h**2)**0.5)
    temp_img = Image.new('RGBA', (diag + 50, diag + 50), (0,0,0,0))
    temp_draw = ImageDraw.Draw(temp_img)
    
    # Draw centered in temp
    cx, cy = temp_img.width // 2, temp_img.height // 2
    temp_draw.text((cx - w/2, cy - h/2), text, font=font, fill=fill_color)
    
    # Rotate (PIL is CCW, CSS is CW, so negate)
    rotated = temp_img.rotate(-angle, expand=True, resample=Image.BICUBIC)
    
    # Paste centered at original rect center
    # Original rect (x,y) is top-left
    orig_center_x = x + w / 2
    orig_center_y = y + h / 2
    
    paste_x = int(orig_center_x - rotated.width / 2)
    paste_y = int(orig_center_y - rotated.height / 2)
    
    img.paste(rotated, (paste_x, paste_y), rotated)

def draw_rotated_badge(img, text, font, bg_color, fg_color, x, y, width, height, angle):
    """Draw badge box rotated"""
    # Create temp image
    diag = int((width**2 + height**2)**0.5)
    temp_img = Image.new('RGBA', (diag + 50, diag + 50), (0,0,0,0))
    temp_draw = ImageDraw.Draw(temp_img)
    
    cx, cy = temp_img.width // 2, temp_img.height // 2
    
    # Draw Rect centered
    # Outline color hardcoded to DARK (#1E2832) as per previous constant
    temp_draw.rounded_rectangle(
        [(cx - width/2, cy - height/2), (cx + width/2, cy + height/2)],
        radius=height * 0.15,
        fill=bg_color,
        outline="#1E2832",
        width=3
    )
    
    # Draw text centered
    try:
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = font.getsize(text)
        
    # Centering text
    temp_draw.text((cx - text_w/2, cy - text_h/2), text, font=font, fill=fg_color)
    
    # Rotate
    rotated = temp_img.rotate(-angle, expand=True, resample=Image.BICUBIC)
    
    # Paste
    orig_center_x = x + width / 2
    orig_center_y = y + height / 2
    
    paste_x = int(orig_center_x - rotated.width / 2)
    paste_y = int(orig_center_y - rotated.height / 2)
    
    img.paste(rotated, (paste_x, paste_y), rotated)

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
                         config: Dict, preview_mode: bool = False,
                         bg_id: int = 0, use_cache: bool = True) -> Image.Image:
    """
    Generate slide with text overlay on background
    
    Args:
        question: {"number": 1, "question": "...", "pointers": [["Label:", "text"], ...]}
        background: PIL Image
        config: {...}
        preview_mode: If True, generates a lower resolution image for faster feedback.
        bg_id: Unique ID for background caching (use id(background) or hash)
    
    Returns:
        PIL Image (1920x1080 or 960x540)
    """
    
    # Resolution settings
    TARGET_WIDTH = 960 if preview_mode else 1920
    TARGET_HEIGHT = 540 if preview_mode else 1080
    
    # Scale factor for coordinates and fonts
    scale = 0.5 if preview_mode else 1.0

    # Use cached resized background
    bg = get_resized_background(background, TARGET_WIDTH, TARGET_HEIGHT, bg_id, use_cache=use_cache)
    draw = ImageDraw.Draw(bg, "RGBA")
    
    # Configurable Layout Parameters (scaled)
    FONT_SIZE_HEADING = int(int(config.get('font_size_heading', 60)) * scale)
    FONT_SIZE_BODY = int(int(config.get('font_size_body', 28)) * scale)
    TEXT_COLOR = config.get('font_text_color', '#F0C83C') 
    POS_OFFSET_X = int(int(config.get('pos_x', 0)) * scale)
    POS_OFFSET_Y = int(int(config.get('pos_y', 0)) * scale)

    # Font mapping - All handwriting fonts for chalkboard style
    FONTS = {
        'Chalk': 'PatrickHand-Regular.ttf',      # Original chalk-style
        'Casual': 'Caveat-Regular.ttf',          # Casual flowing handwriting
        'Playful': 'IndieFlower-Regular.ttf',    # Fun playful handwriting
        'Natural': 'Kalam-Regular.ttf'           # Natural pen-style handwriting
    }
    
    selected_font = config.get('font_family', 'Chalk')
    font_filename = FONTS.get(selected_font, 'PatrickHand-Regular.ttf')

    # Load fonts with caching
    font_path = None
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base_dir, "fonts", font_filename)
        
        if not os.path.exists(font_path):
             # Fallback to system font if file isn't there
            font_path = "/System/Library/Fonts/Supplemental/Chalkboard.ttc"
            
        # Use cached fonts - much faster than loading each time
        font_heading = get_cached_font(font_path, FONT_SIZE_HEADING)
        font_subtitle = get_cached_font(font_path, int(FONT_SIZE_HEADING * 0.5))
        font_question = get_cached_font(font_path, int(FONT_SIZE_HEADING * 0.8))
        font_bullet = get_cached_font(font_path, FONT_SIZE_BODY)
        font_label = get_cached_font(font_path, int(FONT_SIZE_BODY * 1.1))
        
    except Exception as e:
        print(f"⚠️ Could not load custom/system font: {e}")
        font_path = None
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
        
    # Standard margins (scaled)
    BASE_MARGIN_LEFT = 80 * scale
    BASE_MARGIN_TOP = 60 * scale
    SAFE_MARGIN_RIGHT = 80 * scale

    # Margins
    margin_left = BASE_MARGIN_LEFT + POS_OFFSET_X
    margin_top = BASE_MARGIN_TOP + POS_OFFSET_Y
    width_limit = TARGET_WIDTH - SAFE_MARGIN_RIGHT
    
    # Wrap width calculation
    # available width = total width - left margin - right margin
    # We keep right margin static from the edge, but left margin moves with offset
    content_width = width_limit - margin_left
    
    # === HEADER ===
    # Instructor name (top-left)
    should_render_instructor = config.get('render_instructor', True)
    if config.get('instructor_name') and should_render_instructor:
        ins_x = int(config['instructor_x']) * scale if 'instructor_x' in config else margin_left
        ins_y = int(config['instructor_y']) * scale if 'instructor_y' in config else margin_top
        
        # Dynamic Size/Color
        ins_size_raw = config.get('instructor_size')
        if ins_size_raw and font_path:
             ins_font = get_cached_font(font_path, int(int(ins_size_raw) * scale))
        else:
             ins_font = font_heading

        ins_color = config.get('instructor_color')
        if not ins_color:
             fill = custom_color
        else:
             fill = ins_color # Hex or name

        r_val = config.get('instructor_rotation')
        ins_rotation = float(r_val) if r_val is not None else 0.0
        draw_rotated_text(bg, config['instructor_name'], ins_font, fill, ins_x, ins_y, ins_rotation)
    
    # Subtitle (below name)
    should_render_subtitle = config.get('render_subtitle', True)
    if config.get('subtitle') and should_render_subtitle:
        sub_x = int(config['subtitle_x']) * scale if 'subtitle_x' in config else margin_left
        sub_y = int(config['subtitle_y']) * scale if 'subtitle_y' in config else (margin_top + FONT_SIZE_HEADING + 10 * scale)
        
        sub_size_raw = config.get('subtitle_size')
        if sub_size_raw and font_path:
             sub_font = get_cached_font(font_path, int(int(sub_size_raw) * scale))
        else:
             sub_font = font_subtitle
             
        sub_color = config.get('subtitle_color', MINT_GREEN)
        
        r_val = config.get('subtitle_rotation')
        sub_rotation = float(r_val) if r_val is not None else 0.0
        draw_rotated_text(bg, config['subtitle'], sub_font, sub_color, sub_x, sub_y, sub_rotation)

    
    # Badge (Positioned)
    should_render_badge = config.get('render_badge', True)
    
    if config.get('badge_text') and should_render_badge:
        # Badge Size logic
        raw_badge_size = int(config.get('badge_size', 24))
        badge_font_size = int(raw_badge_size * scale)
        
        # Ratio relative to base 24
        size_ratio = raw_badge_size / 24.0
        
        badge_width = int(350 * scale * size_ratio)
        badge_height = int(70 * scale * size_ratio)
        
        default_badge_x = TARGET_WIDTH - SAFE_MARGIN_RIGHT - badge_width
        default_badge_y = margin_top
        
        badge_x = int(config['badge_x']) * scale if 'badge_x' in config else default_badge_x
        badge_y = int(config['badge_y']) * scale if 'badge_y' in config else default_badge_y
        
        badge_bg = config.get('badge_bg_color', ORANGE)
        badge_fg = config.get('badge_color', DARK)
        
        r_val = config.get('badge_rotation')
        badge_rotation = float(r_val) if r_val is not None else -2.0
        if font_path:
            badge_font = get_cached_font(font_path, badge_font_size)
        else:
            badge_font = font_subtitle

        draw_rotated_badge(bg, config['badge_text'], badge_font, badge_bg, badge_fg, badge_x, badge_y, badge_width, badge_height, badge_rotation)
    
    # === QUESTION ===

    # Position question below header (approx 200px gap in original, let's make it relative)
    question_y = margin_top + FONT_SIZE_HEADING + 100 * scale
    question_text = f"Ques {question['number']} => {question['question']}"
    question_lines = wrap_text(question_text, content_width, font_question, draw)
    
    for i, line in enumerate(question_lines):
        draw.text((margin_left, question_y + i * (font_question.size * 1.2)), line,
                  font=font_question, fill=ORANGE)
    
    # === ANSWER LABEL ===
    answer_y = question_y + len(question_lines) * (font_question.size * 1.2) + 40 * scale
    draw.text((margin_left, answer_y), "Answer –", font=font_bullet, fill=WHITE)
    
    # === BULLET POINTS ===
    bullet_y = answer_y + (font_bullet.size * 1.5)
    bullet_indent = 40 * scale
    line_spacing = font_bullet.size * 1.3
    
    # Extra spacing between pointers (configurable)
    # Default 0, allow 0-100 pixels extra (scaled)
    pointer_spacing = int(int(config.get('pointer_spacing', 0)) * scale)

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
        body_x = label_x + label_width + 10 * scale
        available_width = TARGET_WIDTH - SAFE_MARGIN_RIGHT - body_x
        body_lines = wrap_text(text, available_width, font_bullet, draw)
        
        # First line on same line as label
        if body_lines:
            draw.text((body_x, bullet_y), body_lines[0], font=font_bullet, fill=WHITE)
        
        # Remaining lines below
        for j, body_line in enumerate(body_lines[1:], 1):
            draw.text((body_x, bullet_y + j * line_spacing), body_line,
                      font=font_bullet, fill=WHITE)
        
        # Next bullet
        # Base height is (lines + 1) * single_spacing
        # Add dynamic pointer_spacing
        bullet_y += (len(body_lines) + 1) * line_spacing + pointer_spacing

    # === WATERMARK (Bottom Right) ===
    watermark_text = config.get('watermark_text', '')
    if watermark_text:
        # Reuse subtitle font or load new one
        watermark_font = ImageFont.truetype(font_path, int(30 * scale)) if 'font_path' in locals() else font_subtitle
        
        # Calculate size
        bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
        w_width = bbox[2] - bbox[0]
        w_height = bbox[3] - bbox[1]
        
        # Position at bottom right with margins
        # TARGET_WIDTH width, TARGET_HEIGHT height
        # Margin right 80, Margin bottom 60
        wx = TARGET_WIDTH - SAFE_MARGIN_RIGHT - w_width
        wy = TARGET_HEIGHT - (60 * scale) - w_height
        
        # Draw watermark
        draw.text((wx, wy), watermark_text, font=watermark_font, fill=custom_color)
    
    return bg
