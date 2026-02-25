export interface Question {
    number: number;
    question: string;
    pointers: [string, string][];
    config_override?: Partial<Config>;
    image?: string; // base64 string
}

export interface Config {
    instructor_name: string;
    subtitle: string;
    badge_text: string;
    font_size_heading?: number;
    font_size_body?: number;
    font_text_color?: string;
    font_question_color?: string;
    font_options_color?: string;
    pos_x?: number;
    pos_y?: number;
    watermark_text?: string;
    pointer_spacing?: number;
    font_family?: 'Chalk' | 'Casual' | 'Playful' | 'Natural';
    badge_x?: number;
    badge_y?: number;
    render_badge?: boolean;
    instructor_x?: number;
    instructor_y?: number;
    render_instructor?: boolean;
    subtitle_x?: number;
    subtitle_y?: number;
    render_subtitle?: boolean;

    // Card Customizations
    instructor_size?: number;
    instructor_color?: string;
    subtitle_size?: number;
    subtitle_color?: string;
    badge_size?: number;
    badge_color?: string; // Text color
    badge_bg_color?: string; // Background color for badge box

    // Rotation properties
    instructor_rotation?: number;
    subtitle_rotation?: number;
    badge_rotation?: number;

    // Content Layout
    content_region?: 'full' | 'left-half' | 'right-half' | 'left-third' | 'center-third' | 'right-third';
    content_scale?: number; // 0.5 to 2.0, default 1.0
}

export interface ParsedDocxResponse {
    questions: Question[];
    total: number;
}

export interface GenerationProgress {
    current: number;
    total: number;
    status: 'idle' | 'parsing' | 'generating-preview' | 'generating-pptx' | 'complete' | 'error';
}

export interface SlidePreview {
    index: number;
    image: string; // base64
    number?: number;
}

export interface BatchPreviewResponse {
    total_pages: number;
    current_page: number;
    slides: SlidePreview[];
}
