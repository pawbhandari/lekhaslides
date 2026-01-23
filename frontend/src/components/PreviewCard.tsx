import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle } from 'lucide-react';
import type { Question } from '../types';

interface PreviewCardProps {
    previewUrl: string | null;
    questions: Question[];
    onApprove: () => void;
    isGenerating: boolean;
}

export const PreviewCard: React.FC<PreviewCardProps> = ({
    previewUrl,
    questions,
    onApprove,
    isGenerating
}) => {
    const [showQuestions, setShowQuestions] = useState(false);

    return (
        <div className="card">
            <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-accent-yellow flex items-center">
                        <CheckCircle className="w-6 h-6 mr-2 text-accent-mint" />
                        Found {questions.length} Questions
                    </h2>
                    <button
                        onClick={() => setShowQuestions(!showQuestions)}
                        className="flex items-center space-x-2 text-accent-orange hover:text-accent-yellow transition-colors"
                    >
                        <span className="text-sm font-medium">
                            {showQuestions ? 'Hide' : 'View'} All Questions
                        </span>
                        {showQuestions ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                </div>

                {showQuestions && (
                    <div className="bg-chalkboard-dark rounded-lg p-4 max-h-64 overflow-y-auto space-y-2">
                        {questions.map((q) => (
                            <div
                                key={q.number}
                                className="p-3 bg-chalkboard-light rounded border border-gray-700 hover:border-accent-orange/50 transition-colors"
                            >
                                <span className="text-accent-orange font-semibold mr-2">Q{q.number}.</span>
                                <span className="text-gray-300">{q.question}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {previewUrl && (
                <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-300 mb-3">
                        Preview (First Slide)
                    </h3>
                    <div className="bg-chalkboard-dark p-4 rounded-lg">
                        <img
                            src={previewUrl}
                            alt="Slide Preview"
                            className="w-full h-auto rounded shadow-2xl border-2 border-accent-orange/30"
                        />
                    </div>
                </div>
            )}

            <button
                onClick={onApprove}
                disabled={isGenerating || !previewUrl}
                className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
                {isGenerating ? (
                    <>
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <span>Generating Slides...</span>
                    </>
                ) : (
                    <>
                        <CheckCircle className="w-5 h-5" />
                        <span>✅ Approve & Generate All Slides</span>
                    </>
                )}
            </button>
        </div>
    );
};
