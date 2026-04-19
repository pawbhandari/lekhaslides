import { useState, useEffect, useCallback } from 'react';
import type { Question, Config } from '../types';
import { generatePreview } from '../services/api';
import { X, Save, Plus, Trash2, RefreshCw, Smile } from 'lucide-react';
import { FileUpload } from './FileUpload';
import EmojiPicker, { Theme } from 'emoji-picker-react';

interface SlideEditorProps {
    question: Question;
    background: File;
    config: Config;
    onSave: (updatedQuestion: Question) => void;
    onClose: () => void;
    onApplyGlobalEmoji?: (emoji: string) => void;
}

export const SlideEditor = ({ question, background, config, onSave, onClose, onApplyGlobalEmoji }: SlideEditorProps) => {
    const [editedQuestion, setEditedQuestion] = useState<Question>(JSON.parse(JSON.stringify(question)));
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);


    const updatePreview = useCallback(async () => {
        setIsLoading(true);
        try {
            // Force NO is_preview here so modal shows EVERYTHING burnt-in
            const url = await generatePreview(background, editedQuestion, { ...config, is_preview: false });
            setPreviewUrl(url);
        } catch (error) {
            console.error("Preview error", error);
        } finally {
            setIsLoading(false);
        }
    }, [background, editedQuestion, config]);

    // Generate preview when question changes (debounced?)
    useEffect(() => {
        updatePreview();
    }, []); // Initial load only — manual refresh or debounces handle the rest

    // Auto-refresh when image is added/removed
    useEffect(() => {
        const timer = setTimeout(() => {
            updatePreview();
        }, 500);
        return () => clearTimeout(timer);
    }, [editedQuestion.image, updatePreview]);

    // Auto-refresh when question text or pointers change (debounced)
    useEffect(() => {
        const timer = setTimeout(() => {
            updatePreview();
        }, 1200);
        return () => clearTimeout(timer);
    }, [editedQuestion.question, JSON.stringify(editedQuestion.pointers), updatePreview]);

    const handlePointerChange = (idx: number, type: 'label' | 'text', value: string) => {
        const newPointers = [...editedQuestion.pointers];
        newPointers[idx] = [...newPointers[idx]]; // Copy inner array
        newPointers[idx][type === 'label' ? 0 : 1] = value;
        setEditedQuestion({ ...editedQuestion, pointers: newPointers });

    };

    const addPointer = () => {
        setEditedQuestion({
            ...editedQuestion,
            pointers: [...editedQuestion.pointers, ["New Label:", "New content..."]]
        });

    };

    const removePointer = (idx: number) => {
        const newPointers = editedQuestion.pointers.filter((_, i) => i !== idx);
        setEditedQuestion({ ...editedQuestion, pointers: newPointers });

    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-8">
            <div className="bg-[#1a1f2e] w-full max-w-6xl h-[85vh] rounded-2xl flex overflow-hidden border border-white/10 shadow-2xl">

                {/* Left: Preview */}
                <div className="w-[60%] bg-[#0f111a] flex flex-col p-6 border-r border-white/5 relative">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-white font-semibold">Live Preview</h3>
                        <button
                            onClick={updatePreview}
                            className="text-accent-mint hover:bg-accent-mint/10 p-2 rounded-lg text-xs flex items-center space-x-2 transition-colors"
                        >
                            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                            <span>Refresh Preview</span>
                        </button>
                    </div>

                    <div className="flex-1 flex items-center justify-center relative bg-[#1a1f2e] rounded-xl border border-white/5 overflow-hidden">
                        {isLoading && (
                            <div className="absolute inset-0 z-20 flex items-center justify-center bg-black/40 backdrop-blur-[1px]">
                                <div className="w-8 h-8 border-2 border-accent-mint border-t-transparent rounded-full animate-spin"></div>
                            </div>
                        )}
                        {previewUrl ? (
                            <img src={previewUrl} className="w-full h-full object-contain" alt="Preview" />
                        ) : (
                            <div className="text-gray-500">Generating preview...</div>
                        )}
                    </div>
                </div>

                {/* Right: Editor */}
                <div className="w-[40%] flex flex-col bg-[#1a1f2e]">
                    <div className="p-6 border-b border-white/5 flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-bold text-white">Edit Slide {question.number}</h2>
                            <p className="text-xs text-gray-500">Changes apply only to this slide.</p>
                        </div>
                        <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">

                        {/* Question Input */}
                        <div className="space-y-2">
                            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Question Text</label>
                            <textarea
                                value={editedQuestion.question}
                                onChange={(e) => {
                                    setEditedQuestion({ ...editedQuestion, question: e.target.value });

                                }}
                                className="w-full h-24 bg-black/20 border border-white/10 rounded-lg p-3 text-sm text-gray-200 focus:outline-none focus:border-accent-mint/50 transition-colors resize-none"
                            />
                        </div>

                        {/* Slide Emoji Override */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Slide Emoji</label>
                                <button
                                    onClick={() => {
                                        const newConfig = { ...(editedQuestion.config_override || {}), render_global_emoji: false };
                                        delete newConfig.global_emoji;
                                        setEditedQuestion({ ...editedQuestion, config_override: newConfig });
                                    }}
                                    className="text-xs text-gray-500 hover:text-red-400 transition-colors"
                                >
                                    Clear Emoji
                                </button>
                            </div>
                            <div className="flex items-center space-x-3">
                                <div className="text-2xl bg-white/5 w-12 h-12 flex items-center justify-center rounded-lg border border-white/10">
                                    {(editedQuestion.config_override?.global_emoji) || (config.render_global_emoji && config.global_emoji ? config.global_emoji : '❌')}
                                </div>
                                <div className="flex space-x-2">
                                    <button
                                        onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                                        className="px-3 py-2 bg-white/10 hover:bg-white/20 text-sm font-semibold rounded-lg transition-colors border border-white/10 flex items-center space-x-2"
                                    >
                                        <Smile className="w-4 h-4" />
                                        <span>{showEmojiPicker ? 'Close Picker' : 'Change Emoji'}</span>
                                    </button>
                                    {(editedQuestion.config_override?.global_emoji && onApplyGlobalEmoji) && (
                                        <button
                                            onClick={() => {
                                                onApplyGlobalEmoji(editedQuestion.config_override!.global_emoji!);
                                            }}
                                            className="px-3 py-2 bg-accent-yellow/10 hover:bg-accent-yellow/20 text-accent-yellow text-sm font-semibold rounded-lg transition-colors border border-accent-yellow/30"
                                        >
                                            Apply to Global
                                        </button>
                                    )}
                                </div>
                            </div>
                            
                            {showEmojiPicker && (
                                <div className="mt-2 h-[300px]">
                                    <EmojiPicker 
                                        onEmojiClick={(emojiData) => {
                                            const newConfig = { 
                                                ...(editedQuestion.config_override || {}), 
                                                global_emoji: emojiData.emoji,
                                                render_global_emoji: true
                                            };
                                            setEditedQuestion({ ...editedQuestion, config_override: newConfig });
                                            setShowEmojiPicker(false);
                                        }}
                                        theme={Theme.DARK}
                                        width="100%"
                                        height="300px"
                                    />
                                </div>
                            )}
                        </div>

                        {/* Question Image */}
                        <div className="space-y-2">
                            <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Question Image (Diagram/Reference)</label>
                            {editedQuestion.image ? (
                                <div className="relative group rounded-lg overflow-hidden border border-white/10 aspect-video bg-black/40">
                                    <img src={editedQuestion.image} className="w-full h-full object-contain" alt="Question" />
                                    <button
                                        onClick={() => setEditedQuestion({ ...editedQuestion, image: undefined })}
                                        className="absolute top-2 right-2 p-1.5 bg-black/60 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500/80"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            ) : (
                                <FileUpload
                                    label="Upload Image"
                                    accept=".jpg,.jpeg,.png"
                                    onFileSelect={async (file) => {
                                        if (file) {
                                            const reader = new FileReader();
                                            reader.onloadend = () => {
                                                setEditedQuestion({ ...editedQuestion, image: reader.result as string });
                                            };
                                            reader.readAsDataURL(file);
                                        }
                                    }}
                                    file={null}
                                    icon="image"
                                />
                            )}
                        </div>

                        {/* Pointers List */}
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <label className="text-xs text-gray-400 uppercase font-bold tracking-wider">Bullet Points</label>
                                <button
                                    onClick={addPointer}
                                    className="text-xs text-accent-mint flex items-center space-x-1 hover:underline"
                                >
                                    <Plus className="w-3 h-3" /> <span>Add Point</span>
                                </button>
                            </div>

                            {editedQuestion.pointers.map((pointer, idx) => (
                                <div key={idx} className="bg-black/20 p-3 rounded-lg border border-white/5 space-y-2 group">
                                    <div className="flex items-center space-x-2">
                                        <input
                                            value={pointer[0]}
                                            onChange={(e) => handlePointerChange(idx, 'label', e.target.value)}
                                            className="flex-1 bg-transparent border-b border-white/10 px-1 py-1 text-sm font-semibold text-accent-yellow focus:outline-none focus:border-accent-yellow/50"
                                            placeholder="Label"
                                        />
                                        <button onClick={() => removePointer(idx)} className="text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                    <textarea
                                        value={pointer[1]}
                                        onChange={(e) => handlePointerChange(idx, 'text', e.target.value)}
                                        className="w-full bg-transparent text-sm text-gray-300 focus:outline-none resize-none h-16"
                                        placeholder="Detail text..."
                                    />
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="p-6 border-t border-white/5 flex justify-end space-x-3 bg-[#151926]">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors text-sm font-medium"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={() => {
                                onSave(editedQuestion);
                                onClose();
                            }}
                            className="px-6 py-2 rounded-lg bg-accent-mint text-[#1a1f2e] font-bold shadow-lg hover:shadow-accent-mint/20 hover:bg-accent-mint/90 transition-all flex items-center space-x-2"
                        >
                            <Save className="w-4 h-4" />
                            <span>Save Changes</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
