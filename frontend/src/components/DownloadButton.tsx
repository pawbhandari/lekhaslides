import React from 'react';
import { Download, CheckCircle } from 'lucide-react';

interface DownloadButtonProps {
    onDownload: () => void;
    filename: string;
    isComplete: boolean;
}

export const DownloadButton: React.FC<DownloadButtonProps> = ({
    onDownload,
    filename,
    isComplete
}) => {
    if (!isComplete) return null;

    return (
        <div className="card text-center">
            <div className="mb-6">
                <div className="w-20 h-20 bg-accent-mint/20 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-12 h-12 text-accent-mint" />
                </div>
                <h2 className="text-2xl font-bold text-accent-yellow mb-2">
                    Slides Generated Successfully!
                </h2>
                <p className="text-gray-400">
                    Your presentation is ready to download
                </p>
            </div>

            <button
                onClick={onDownload}
                className="btn-primary w-full md:w-auto mx-auto flex items-center justify-center space-x-2"
            >
                <Download className="w-5 h-5" />
                <span>Download {filename}</span>
            </button>

            <p className="text-sm text-gray-500 mt-4">
                Click to download your PowerPoint presentation
            </p>
        </div>
    );
};
