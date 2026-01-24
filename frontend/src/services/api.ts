import axios from 'axios';
import type { ParsedDocxResponse, Question, Config } from '../types';

const API_BASE = 'http://localhost:8000';

export const parseDocx = async (file: File): Promise<ParsedDocxResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post<ParsedDocxResponse>(`${API_BASE}/api/parse-docx`, formData);
    return response.data;
};

export const parseText = async (text: string): Promise<ParsedDocxResponse> => {
    const formData = new FormData();
    formData.append('text', text);

    const response = await axios.post<ParsedDocxResponse>(`${API_BASE}/api/parse-text`, formData);
    return response.data;
};

export const generatePreview = async (
    background: File,
    questionData: Question,
    config: Config,
    signal?: AbortSignal
): Promise<string> => {
    const formData = new FormData();
    formData.append('background', background);
    formData.append('question_data', JSON.stringify(questionData));
    formData.append('config', JSON.stringify(config));

    const response = await axios.post(`${API_BASE}/api/generate-preview`, formData, {
        responseType: 'blob',
        signal
    });

    return URL.createObjectURL(response.data);
};

export const generatePPTX = async (
    background: File,
    questionsData: Question[],
    config: Config,
    onProgress?: (current: number, total: number) => void
): Promise<Blob> => {
    const formData = new FormData();
    formData.append('background', background);
    formData.append('questions_data', JSON.stringify(questionsData));
    formData.append('config', JSON.stringify(config));

    const response = await fetch(`${API_BASE}/api/generate-pptx`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        throw new Error('Failed to generate PPTX');
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let pptxBase64 = '';
    let buffer = ''; // Buffer for partial lines

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Append new data to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete lines (SSE events end with \n\n)
        const events = buffer.split('\n\n');

        // Keep the last part as it might be incomplete
        buffer = events.pop() || '';

        for (const event of events) {
            const lines = event.split('\n');
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const jsonStr = line.slice(6);
                        const data = JSON.parse(jsonStr);

                        if (data.type === 'progress' && onProgress) {
                            onProgress(data.current, data.total);
                        } else if (data.type === 'complete') {
                            pptxBase64 = data.file;
                        } else if (data.type === 'error') {
                            throw new Error(data.message);
                        }
                    } catch (e) {
                        // JSON parse error - might be partial, will try next chunk
                        console.warn('SSE parse warning:', e);
                    }
                }
            }
        }
    }

    // Handle any remaining buffer content
    if (buffer.trim()) {
        const lines = buffer.split('\n');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    if (data.type === 'complete') {
                        pptxBase64 = data.file;
                    }
                } catch (e) {
                    // Ignore parse errors in final buffer
                }
            }
        }
    }

    if (!pptxBase64) {
        throw new Error('No PPTX data received from server');
    }

    // Decode base64 to blob
    const binaryString = atob(pptxBase64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }

    return new Blob([bytes], {
        type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    });
};

export const downloadBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
};
