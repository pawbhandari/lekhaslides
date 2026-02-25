from PIL import Image, ImageDraw, ImageFont, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import os
from typing import Dict, List, Tuple
from functools import lru_cache
import io as _io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import threading
import datetime

# Global locks
_font_lock = threading.Lock()
_bg_lock = threading.Lock()

# Global font cache
_font_cache: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}

def get_cached_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """Get font from cache or load it"""
    key = (font_path, size)
    with _font_lock:
        if key not in _font_cache:
            _font_cache[key] = ImageFont.truetype(font_path, size)
        return _font_cache[key]

# Cache for resized backgrounds
_bg_cache: Dict[Tuple[int, int, int], Image.Image] = {}

def get_resized_background(background: Image.Image, width: int, height: int, bg_id: int, use_cache: bool = True, fast: bool = False) -> Image.Image:
    """Cache resized backgrounds to avoid re-resizing for every slide"""
    if not use_cache:
        resample = Image.Resampling.BILINEAR if fast else Image.Resampling.LANCZOS
        return background.resize((width, height), resample).convert("RGB")

    key = (bg_id, width, height)
    with _bg_lock:
        if key not in _bg_cache:
            # For the first resize, we can use BILINEAR if requested, but LANCZOS is okay for cache since it happens once
            resample = Image.Resampling.BILINEAR if fast else Image.Resampling.LANCZOS
            _bg_cache[key] = background.resize((width, height), resample).convert("RGB")
        return _bg_cache[key].copy()

def compress_image(image: Image.Image, max_dimension: int = 1920) -> Image.Image:
    """
    Aggressively compress/resize large images to save memory before processing.
    Also ensures the image is not excessively large in memory.
    """
    # 1. Dimension Check
    if max(image.size) > max_dimension:
        ratio = max_dimension / max(image.size)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        print(f"📉 Downscaling background from {image.size} to {new_size} for memory optimization")
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    return image.convert("RGB")

def clear_caches():
    """Clear all caches - call this between different generation sessions"""
    global _font_cache, _bg_cache
    with _font_lock:
        _font_cache.clear()
    with _bg_lock:
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

def normalize_latex(formula: str) -> str:
    """
    Normalize LaTeX commands that matplotlib mathtext doesn't support to equivalents it does.
    Matplotlib mathtext is a SUBSET of LaTeX - it doesn't support all commands.
    """
    # Map unsupported short-forms to supported equivalents
    replacements = [
        (r'\leq', r'\leq'),   # Keep as-is (supported)
        (r'\geq', r'\geq'),   # Keep as-is (supported)
        (r'\le ', r'\leq '),  # \le with trailing space
        (r'\ge ', r'\geq '),
        (r'\le$', r'\leq$'),  # \le at end of formula
        (r'\ge$', r'\geq$'),
        (r'\ne ', r'\neq '),
        (r'\ne$', r'\neq$'),
    ]
    for old, new in replacements:
        formula = formula.replace(old, new)
    
    # Handle \le and \ge followed by anything (word boundary replacement)
    import re
    formula = re.sub(r'\\le(?=[^a-zA-Z]|$)', r'\\leq', formula)
    formula = re.sub(r'\\ge(?=[^a-zA-Z]|$)', r'\\geq', formula)
    formula = re.sub(r'\\ne(?=[^a-zA-Z]|$)', r'\\neq', formula)
    
    # \left and \right are supported in matplotlib, but ONLY with paired delimiters
    # Keep them as-is: matplotlib supports \left( \right) \left[ \right] etc.
    
    return formula

_math_render_lock = threading.Lock()

def render_math_to_image(formula: str, fontsize: int, color) -> Tuple[Image.Image, int]:
    """
    Render a LaTeX formula to a transparent PIL RGBA image using full Matplotlib.
    Returns (Image, depth_in_pixels) for precise baseline alignment.
    """
    try:
        # Normalize color
        if isinstance(color, str) and color.startswith('#'):
            mpl_color = tuple(int(color[i:i+2], 16) / 255.0 for i in (1, 3, 5))
        elif isinstance(color, tuple):
            mpl_color = tuple(v / 255.0 if (isinstance(v, int) and v > 1) else v for v in color)
        else:
            mpl_color = color

        # Normalize the LaTeX to remove unsupported commands
        formula = normalize_latex(formula)

        math_str = formula.strip()
        if not math_str.startswith('$'):
            math_str = f'${math_str}$'

        with _math_render_lock:
            dpi = 100
            # PIL fontsize is in pixels. Matplotlib fontsize is in points (1/72 inch).
            # At `dpi` DPI: 1 inch = dpi pixels, so 1 point = dpi/72 pixels.
            # To get the same visual size: mpl_fontsize_pt = pil_pixels * 72 / dpi
            mpl_fontsize = fontsize * 72.0 / dpi
            
            fig = plt.figure(figsize=(10, 2), dpi=dpi)
            fig.patch.set_alpha(0.0)
            
            t = fig.text(0, 0.5, math_str, fontsize=mpl_fontsize, color=mpl_color, va='baseline')
            
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            
            bbox = t.get_window_extent(renderer=renderer)
            
            if bbox.width <= 0 or bbox.height <= 0:
                plt.close(fig)
                return None, 0

            baseline_y = fig.get_figheight() * dpi * 0.5
            depth = baseline_y - bbox.y0
            
            buf = _io.BytesIO()
            fig.savefig(buf, format='png', transparent=True, dpi=dpi, bbox_inches='tight', pad_inches=0)
            plt.close(fig)

            buf.seek(0)
            img = Image.open(buf).convert('RGBA')
            
            return img, int(depth)

    except Exception as e:
        print(f"⚠️ Math render failed for '{formula}': {e}")
        return None, 0

def draw_text_with_math(draw: ImageDraw.Draw, bg: Image.Image, text: str, 
                       x: int, y: int, font: ImageFont.FreeTypeFont, 
                       fill_color, max_width: int, line_spacing_factor: float = 1.1):
    """
    Draws text that may contain inline $...$ or block $$...$$ LaTeX math.
    fill_color can be a PIL int-tuple, a float-tuple (from mpl), or a hex string.
    """
    # --- Normalize colors ---
    # PIL needs integer tuples; matplotlib needs float tuples or hex strings.
    def to_pil_color(c):
        if isinstance(c, tuple):
            if any(isinstance(v, float) for v in c):
                return tuple(int(v * 255) for v in c)
            return c
        return c  # hex string is fine for PIL too

    def to_mpl_color(c):
        if isinstance(c, tuple):
            if any(isinstance(v, int) and v > 1 for v in c):
                return tuple(v / 255.0 for v in c)
            return c
        return c  # hex string is fine for matplotlib too

    pil_color = to_pil_color(fill_color)
    mpl_color = to_mpl_color(fill_color)

    import re

    # 1. First Pass: Auto-wrap naked LaTeX (text containing \ and no $)
    # This catches cases like "A) \frac{1}{2}" -> "A) $\frac{1}{2}$"
    if '\\' in text and '$' not in text:
        # Simple heuristic: wrap the whole thing if it contains common math commands
        if any(cmd in text for cmd in ['\\frac', '\\le', '\\ge', '\\ne', '\\alpha', '\\beta', '\\gamma', '\\infty', '\\infty', '-\\infty']):
             text = f"${text}$"

    # Fast path: no math markers and no obvious math symbols
    if '$' not in text and '\\' not in text:
        lines = wrap_text(text, max_width, font, draw)
        for i, line in enumerate(lines):
            draw.text((int(x), int(y + i * (font.size * 1.2))), line, font=font, fill=pil_color)
        return len(lines) * (font.size * 1.2)

    # Split by $$...$$ and $...$
    parts = re.split(r'(\$\$[\s\S]+?\$\$|\$[\s\S]+?\$)', text)
    parts = [p for p in parts if p]

    current_x = float(x)
    current_y = float(y)
    
    # Track the height of the current line
    line_max_height = font.size * line_spacing_factor

    for part in parts:
        if not part:
            continue

        if part.startswith('$$') and part.endswith('$$'):
            # Display math — treat exactly like inline math (left-aligned).
            # We NEVER center-align in this context because these are option bodies
            # where the label "A)" is to the left. Centering creates a huge gap.
            formula = part[2:-2].strip()
            math_img, _ = render_math_to_image(formula, font.size, mpl_color)
            if math_img:
                if current_x + math_img.width > x + max_width:
                    current_y += line_max_height
                    current_x = float(x)
                    line_max_height = font.size * line_spacing_factor

                paste_y = current_y
                bg.paste(math_img, (int(current_x), int(paste_y)), math_img)
                current_x += math_img.width + 4
                line_max_height = max(line_max_height, math_img.height + 4)
            else:
                draw.text((int(current_x), int(current_y)), formula, font=font, fill=pil_color)
                current_x += draw.textlength(formula, font=font)


        elif part.startswith('$') and part.endswith('$'):
            # Inline math
            formula = part[1:-1].strip()
            math_img, _ = render_math_to_image(formula, font.size, mpl_color)
            if math_img:
                # Wrap to next line if the formula won't fit
                if current_x + math_img.width > x + max_width:
                    current_y += line_max_height
                    current_x = float(x)
                    line_max_height = font.size * line_spacing_factor

                # Vertical alignment:
                # PIL text renders from the top of the em-square.
                # For a handwriting/chalk font, the cap-height is roughly 70% of font.size.
                # We want the math to sit "on the same line" as the text.
                # Strategy: align the TOP of the math image with the top of plain text.
                # This means paste_y = current_y (top-aligned).
                # Adjust slightly upward so tall fractions don't push down.
                paste_y = current_y

                bg.paste(math_img, (int(current_x), int(paste_y)), math_img)

                current_x += math_img.width + 4

                # Ensure line is tall enough to contain the math
                line_max_height = max(line_max_height, math_img.height + 4)
            else:
                # Fallback: draw formula as raw text
                txt = f"${formula}$"
                draw.text((int(current_x), int(current_y)), txt, font=font, fill=pil_color)
                current_x += draw.textlength(txt, font=font)

        else:
            # Plain text - handle newlines explicitly
            text_lines = part.split('\n')
            for line_idx, text_line in enumerate(text_lines):
                if line_idx > 0:
                    current_y += line_max_height
                    current_x = float(x)
                    line_max_height = font.size * line_spacing_factor
                
                words = text_line.split(' ')
                for i, word in enumerate(words):
                    actual_word = word + (" " if i < len(words) - 1 else "")
                    if not actual_word.strip() and not actual_word:
                        continue
                    w_len = draw.textlength(actual_word, font=font)
                    
                    if current_x + w_len > x + max_width:
                        current_y += line_max_height
                        current_x = float(x)
                        line_max_height = font.size * line_spacing_factor
                    
                    draw.text((int(current_x), int(current_y)), actual_word, font=font, fill=pil_color)
                    current_x += w_len

    return (current_y - y) + line_max_height


import base64
from io import BytesIO

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
    bg = get_resized_background(background, TARGET_WIDTH, TARGET_HEIGHT, bg_id, use_cache=use_cache, fast=preview_mode)
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
    WHITE = (240, 245, 250)
    ORANGE = (255, 180, 80)
    DARK = (30, 40, 50)
    MINT_GREEN = (100, 220, 180)
    
    # Parse separate colors
    def parse_hex(hex_str, default):
        if not hex_str or not hex_str.startswith('#'):
            return default
        try:
            return tuple(int(hex_str[i:i+2], 16) for i in (1, 3, 5))
        except:
            return default

    # Question color (fallback to font_text_color then yellow)
    q_color_hex = config.get('font_question_color', config.get('font_text_color', '#F0C83C'))
    question_color = parse_hex(q_color_hex, YELLOW)
    
    # Options color (fallback to font_text_color then off-white)
    o_color_hex = config.get('font_options_color', config.get('font_text_color', '#F0E6D2'))
    options_color = parse_hex(o_color_hex, WHITE)

    def to_mpl_color(c):
        """Convert PIL color to matplotlib color"""
        if isinstance(c, tuple):
            return tuple(v/255.0 for v in c)
        return c

    mpl_question = to_mpl_color(question_color)
    mpl_options = to_mpl_color(options_color)
        
    # Content Scale (relative font sizing)
    content_scale_factor = float(config.get('content_scale', 1.0))
    FONT_SIZE_HEADING = int(FONT_SIZE_HEADING * content_scale_factor)
    FONT_SIZE_BODY = int(FONT_SIZE_BODY * content_scale_factor)
    
    # Re-compute scaled fonts with content_scale
    if font_path:
        font_heading = get_cached_font(font_path, FONT_SIZE_HEADING)
        font_subtitle = get_cached_font(font_path, int(FONT_SIZE_HEADING * 0.5))
        font_question = get_cached_font(font_path, int(FONT_SIZE_HEADING * 0.8))
        font_bullet = get_cached_font(font_path, FONT_SIZE_BODY)
        font_label = get_cached_font(font_path, int(FONT_SIZE_BODY * 1.1))

    # Standard margins (scaled)
    BASE_MARGIN_LEFT = 80 * scale
    BASE_MARGIN_TOP = 60 * scale
    SAFE_MARGIN_RIGHT = 80 * scale

    # Content Region - determines the area where question content is rendered
    content_region = config.get('content_region', 'full')
    
    # Calculate region bounds (affects margin_left and width_limit)
    if content_region == 'left-half':
        region_left = BASE_MARGIN_LEFT
        region_right = TARGET_WIDTH * 0.5
    elif content_region == 'right-half':
        region_left = TARGET_WIDTH * 0.5 + BASE_MARGIN_LEFT * 0.5
        region_right = TARGET_WIDTH - SAFE_MARGIN_RIGHT
    elif content_region == 'left-third':
        region_left = BASE_MARGIN_LEFT
        region_right = TARGET_WIDTH * 0.333
    elif content_region == 'center-third':
        region_left = TARGET_WIDTH * 0.333 + BASE_MARGIN_LEFT * 0.3
        region_right = TARGET_WIDTH * 0.666
    elif content_region == 'right-third':
        region_left = TARGET_WIDTH * 0.666 + BASE_MARGIN_LEFT * 0.3
        region_right = TARGET_WIDTH - SAFE_MARGIN_RIGHT
    else:  # 'full'
        region_left = BASE_MARGIN_LEFT
        region_right = TARGET_WIDTH - SAFE_MARGIN_RIGHT

    # Margins adjusted by region
    margin_left = region_left + POS_OFFSET_X
    margin_top = BASE_MARGIN_TOP + POS_OFFSET_Y
    width_limit = region_right
    
    # Wrap width calculation
    content_width = width_limit - margin_left

    # === QUESTION IMAGE (OPTIONAL) ===
    q_image = None
    if "image" in question and question["image"]:
        try:
            img_data = question["image"]
            if "base64," in img_data:
                img_data = img_data.split("base64,")[1]
            
            q_image_bytes = base64.b64decode(img_data)
            q_image = Image.open(BytesIO(q_image_bytes))
            
            # Resize image to fit a portion of the slide
            # Max dimensions: 40% width, 40% height
            max_w = int(TARGET_WIDTH * 0.45)
            max_h = int(TARGET_HEIGHT * 0.45)
            
            q_image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            
            # Reduce content width if image is present
            content_width = int(content_width * 0.55)
        except Exception as e:
            print(f"⚠️ Failed to load question image: {e}")
            q_image = None
    
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
             fill = question_color
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
             
        sub_color = config.get('subtitle_color', o_color_hex) # Use options hex or similar
        
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
    question_text = f"→ {question['question']}"
    
    # Use the new rich text drawer with question color
    # Increased line_spacing_factor to 1.3 to give more space between question lines
    q_height = draw_text_with_math(draw, bg, question_text, margin_left, question_y, 
                                  font_question, mpl_question, content_width, line_spacing_factor=1.3)
    
    # Update question_y for image and answer label
    next_y = question_y + q_height
    
    # Draw question image if present (on the right)
    if q_image:
        img_x = TARGET_WIDTH - SAFE_MARGIN_RIGHT - q_image.width
        img_y = question_y
        bg.paste(q_image, (int(img_x), int(img_y)))
    
    # === ANSWER LABEL ===
    # Use options color for answer label - Reduced gap from 40 to 10
    answer_y = next_y + 10 * scale
    draw.text((margin_left, answer_y), "Answer –", font=font_bullet, fill=options_color)
    
    # === BULLET POINTS ===
    bullet_y = answer_y + (font_bullet.size * 1.5)
    bullet_indent = 40 * scale
    line_spacing = font_bullet.size * 1.3
    
    # Extra spacing between pointers (configurable)
    # Default 0, allow 0-100 pixels extra (scaled)
    pointer_spacing = int(int(config.get('pointer_spacing', 0)) * scale)

    for label, text in question['pointers']:
        # First, figure out math content height to center labels vertically
        # We render a "probe" to get height - but that's slow, so we do a cheap estimate:
        # For single-line with fraction: ~1.44 * font_bullet.size
        # For plain text: ~1.0 * font_bullet.size
        # We'll just draw and then compute advance after
        
        # Bullet marker and label — drawn at bullet_y
        row_y = bullet_y
        
        draw.text((margin_left, row_y), "•", font=font_bullet, fill=options_color)
        
        # Label using options color
        label_x = margin_left + bullet_indent
        draw.text((label_x, row_y), label, font=font_label, fill=options_color)
        
        # Get label width
        label_bbox = draw.textbbox((0, 0), label, font=font_label)
        label_width = label_bbox[2] - label_bbox[0]
        
        # Body text using options color
        # Strip leading whitespace so tabs/spaces from AI don't push text far right
        clean_text = text.strip()
        body_x = label_x + label_width + 10 * scale
        available_width = TARGET_WIDTH - SAFE_MARGIN_RIGHT - body_x
        
        # Use rich text drawer for pointers
        p_height = draw_text_with_math(draw, bg, clean_text, body_x, row_y,
                                     font_bullet, mpl_options, available_width)
        
        # Advance: tightly pack options
        # For single-line content (with or without a fraction), advance = content height + small gap
        # For multi-line content, use full height
        row_height = max(p_height, font_bullet.size)
        gap = font_bullet.size * 1.1  # comfortable gap between options
        bullet_y += row_height + gap + pointer_spacing

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
        draw.text((wx, wy), watermark_text, font=watermark_font, fill=question_color)
    
    return bg
