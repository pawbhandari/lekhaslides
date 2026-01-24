import { useState } from 'react';
import type { BatchPreviewResponse } from '../types';

import { ChevronLeft, ChevronRight, Edit2, Download, AlertTriangle, X, Plus } from 'lucide-react';

interface SlideGridProps {
    previews: BatchPreviewResponse | null;
    isLoading: boolean;
    onPageChange: (page: number) => void;
    onEditSlide: (index: number) => void;
    onGeneratePPTX: () => void;
    onClose: () => void;
    onInsertSlide: (index: number) => void;
}

export const SlideGrid = ({
    previews,
    isLoading,
    onPageChange,
    onEditSlide,
    onGeneratePPTX,
    onClose,
    onInsertSlide
}: SlideGridProps) => {
    const [showQualityWarning, setShowQualityWarning] = useState(true);

    if (isLoading && !previews) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-gray-400">
                <div className="w-12 h-12 border-4 border-accent-mint border-t-transparent rounded-full animate-spin mb-4"></div>
                <p>Generating previews for review...</p>
            </div>
        );
    }

    if (!previews) return null;

    return (
        <div className="flex flex-col h-full bg-[#0f111a] p-6 relative">

            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <button
                        onClick={onClose}
                        className="flex items-center space-x-2 text-gray-400 hover:text-white mb-2 transition-colors text-sm font-medium"
                    >
                        <ChevronLeft className="w-4 h-4" />
                        <span>Back to Editor</span>
                    </button>
                    <h2 className="text-2xl font-bold text-white">Review Slides</h2>
                    <p className="text-gray-400 text-sm">Review and edit your slides before final generation.</p>
                </div>

                <div className="flex items-center space-x-4">
                    {/* Pagination Controls */}
                    <div className="flex items-center space-x-2 bg-white/5 rounded-lg p-1">
                        <button
                            onClick={() => onPageChange(previews.current_page - 1)}
                            disabled={previews.current_page === 1 || isLoading}
                            className="p-2 hover:bg-white/10 rounded-md disabled:opacity-30 transition-colors"
                        >
                            <ChevronLeft className="w-5 h-5 text-gray-300" />
                        </button>
                        <span className="text-sm font-medium text-gray-300 px-2">
                            Page {previews.current_page} of {previews.total_pages}
                        </span>
                        <button
                            onClick={() => onPageChange(previews.current_page + 1)}
                            disabled={previews.current_page === previews.total_pages || isLoading}
                            className="p-2 hover:bg-white/10 rounded-md disabled:opacity-30 transition-colors"
                        >
                            <ChevronRight className="w-5 h-5 text-gray-300" />
                        </button>
                    </div>

                    <button
                        onClick={onGeneratePPTX}
                        className="flex items-center space-x-2 bg-accent-mint hover:bg-accent-mint/90 text-[#1a1f2e] px-6 py-2.5 rounded-xl font-bold transition-all shadow-lg hover:shadow-accent-mint/20"
                    >
                        <Download className="w-5 h-5" />
                        <span>Generate PPTX</span>
                    </button>
                </div>
            </div>

            {/* Quality Warning */}
            {showQualityWarning && (
                <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-3 mb-6 flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                        <AlertTriangle className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
                        <div>
                            <p className="text-orange-200 text-sm font-medium">Low Quality Previews</p>
                            <p className="text-orange-200/70 text-xs">These previews are highly compressed for speed. The final downloaded PPTX will use high-quality images.</p>
                        </div>
                    </div>
                    <button onClick={() => setShowQualityWarning(false)} className="text-orange-400 hover:text-orange-200">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            {/* Grid */}
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-20">
                    {previews.slides.map((slide, i) => (
                        <div key={slide.index} className="relative group/slide-wrapper">
                            {/* Insert Button (Before first slide or between slides) */}
                            <div
                                className="absolute -left-3 top-1/2 -translate-y-1/2 z-10 opacity-0 group-hover/slide-wrapper:opacity-100 transition-opacity"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onInsertSlide(slide.index);
                                }}
                            >
                                <button className="bg-accent-mint hover:bg-accent-mint/80 text-black p-1.5 rounded-full shadow-lg transform hover:scale-110 transition-all" title="Insert Slide Before">
                                    <Plus className="w-4 h-4" />
                                </button>
                            </div>

                            {/* Special case: Add button after the very last slide of the whole deck if we are on the last page and this is the last item */}
                            {i === previews.slides.length - 1 && (
                                <div
                                    className="absolute -right-3 top-1/2 -translate-y-1/2 z-10 opacity-0 group-hover/slide-wrapper:opacity-100 transition-opacity"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onInsertSlide(slide.index + 1);
                                    }}
                                >
                                    <button className="bg-accent-mint hover:bg-accent-mint/80 text-black p-1.5 rounded-full shadow-lg transform hover:scale-110 transition-all" title="Insert Slide After">
                                        <Plus className="w-4 h-4" />
                                    </button>
                                </div>
                            )}

                            <div
                                onClick={() => onEditSlide(slide.index)}
                                className="group relative aspect-video bg-[#1a1f2e] rounded-xl overflow-hidden border border-white/5 hover:border-accent-mint/50 transition-all cursor-pointer hover:shadow-2xl hover:scale-[1.02]"
                            >
                                <img
                                    src={slide.image}
                                    alt={`Slide ${slide.number}`}
                                    className="w-full h-full object-cover"
                                    loading="lazy"
                                />

                                {/* Overlay on hover */}
                                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                    <div className="bg-white/10 backdrop-blur-md p-3 rounded-full">
                                        <Edit2 className="w-6 h-6 text-white" />
                                    </div>
                                </div>

                                {/* Label */}
                                <div className="absolute bottom-2 left-2 bg-black/60 backdrop-blur-sm px-2 py-1 rounded text-xs font-mono text-white/80">
                                    Slide {slide.number || slide.index + 1}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {isLoading && (
                <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="flex flex-col items-center">
                        <div className="w-10 h-10 border-4 border-white/20 border-t-white rounded-full animate-spin mb-3"></div>
                        <span className="text-white font-medium">Loading page...</span>
                    </div>
                </div>
            )}
        </div>
    );
};
