import axios from 'axios';
import type { ParsedDocxResponse, Question, Config } from '../types';

const API_BASE = 'http://localhost:8000';

export const parseDocx = async (file: File): Promise<ParsedDocxResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post<ParsedDocxResponse>(`${API_BASE}/api/parse-docx`, formData);
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
    config: Config
): Promise<Blob> => {
    const formData = new FormData();
    formData.append('background', background);
    formData.append('questions_data', JSON.stringify(questionsData));
    formData.append('config', JSON.stringify(config));

    const response = await axios.post(`${API_BASE}/api/generate-pptx`, formData, {
        responseType: 'blob'
    });

    return response.data;
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
