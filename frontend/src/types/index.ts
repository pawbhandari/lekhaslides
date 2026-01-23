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
