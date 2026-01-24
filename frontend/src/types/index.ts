export interface Question {
    number: number;
    question: string;
    pointers: [string, string][];
}

export interface Config {
    instructor_name: string;
    subtitle: string;
    badge_text: string;
    font_size_heading?: number;
    font_size_body?: number;
    font_text_color?: string;
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
