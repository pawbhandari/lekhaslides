import { useState, useEffect } from 'react';
import { Trash2, Plus, Edit3, Check, ChevronDown, ChevronUp, ImagePlus, GripVertical } from 'lucide-react';
import type { Question } from '../types';
import { MathText } from './MathText';

interface Props {
  questions: Question[];
  onConfirm: (questions: Question[]) => void;
  onAddMoreImages?: () => void;
  isParsingMore: boolean;
}

export function ParsedContentReview({ questions, onConfirm, onAddMoreImages, isParsingMore }: Props) {
  const [editableQuestions, setEditableQuestions] = useState<Question[]>(
    questions.map(q => ({ ...q }))
  );
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  // Sync local state when parent questions change (e.g., after "Add More Images")
  useEffect(() => {
    console.log(`📥 [ParsedContentReview] Received ${questions.length} questions from parent`);
    if (questions.length !== editableQuestions.length) {
      setEditableQuestions(questions.map(q => ({ ...q })));
    }
  }, [questions]);

  const updateQuestion = (idx: number, field: string, value: string) => {
    setEditableQuestions(prev => {
      const updated = [...prev];
      updated[idx] = { ...updated[idx], [field]: value };
      return updated;
    });
  };

  const updatePointer = (qIdx: number, pIdx: number, col: number, value: string) => {
    setEditableQuestions(prev => {
      const updated = [...prev];
      const pointers = [...updated[qIdx].pointers];
      const pointer: [string, string] = [...pointers[pIdx]];
      pointer[col] = value;
      pointers[pIdx] = pointer;
      updated[qIdx] = { ...updated[qIdx], pointers };
      return updated;
    });
  };

  const removeQuestion = (idx: number) => {
    setEditableQuestions(prev => {
      const updated = prev.filter((_, i) => i !== idx);
      // Renumber
      return updated.map((q, i) => ({ ...q, number: i + 1 }));
    });
  };

  const removePointer = (qIdx: number, pIdx: number) => {
    setEditableQuestions(prev => {
      const updated = [...prev];
      const pointers = updated[qIdx].pointers.filter((_, i) => i !== pIdx);
      updated[qIdx] = { ...updated[qIdx], pointers };
      return updated;
    });
  };

  const addPointer = (qIdx: number) => {
    setEditableQuestions(prev => {
      const updated = [...prev];
      const nextLabel = String.fromCharCode(65 + updated[qIdx].pointers.length) + ')';
      updated[qIdx] = {
        ...updated[qIdx],
        pointers: [...updated[qIdx].pointers, [nextLabel, ''] as [string, string]]
      };
      return updated;
    });
  };

  const addQuestion = () => {
    const newNum = editableQuestions.length + 1;
    setEditableQuestions(prev => [...prev, {
      number: newNum,
      question: '',
      pointers: [['A)', ''] as [string, string]]
    }]);
    setExpandedIndex(editableQuestions.length);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/10 bg-gradient-to-r from-accent-mint/10 to-transparent">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Edit3 className="w-5 h-5 text-accent-mint" />
              Review Parsed Content
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              {editableQuestions.length} question{editableQuestions.length !== 1 ? 's' : ''} extracted • Edit before generating slides
            </p>
          </div>
        </div>
      </div>

      {/* Question List - Scrollable */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2" style={{ maxHeight: 'calc(100vh - 320px)' }}>
        {editableQuestions.map((q, qIdx) => (
          <div
            key={qIdx}
            className={`rounded-xl border transition-all duration-200 ${expandedIndex === qIdx
              ? 'border-accent-mint/30 bg-white/5 shadow-lg shadow-accent-mint/5'
              : 'border-white/5 bg-white/[0.02] hover:bg-white/[0.04]'
              }`}
          >
            {/* Question Header */}
            <div
              className="flex items-center gap-2 px-4 py-3 cursor-pointer select-none"
              onClick={() => setExpandedIndex(expandedIndex === qIdx ? null : qIdx)}
            >
              <GripVertical className="w-4 h-4 text-gray-600 flex-shrink-0" />
              <span className="w-7 h-7 rounded-full bg-accent-mint/20 text-accent-mint text-xs font-bold flex items-center justify-center flex-shrink-0">
                {q.number}
              </span>
              <p className="text-sm text-gray-200 flex-1 line-clamp-1 font-medium">
                {q.question ? <MathText text={q.question} /> : <span className="text-gray-500 italic">Empty question</span>}
              </p>
              <span className="text-xs text-gray-500 mr-2">{(q.pointers || []).length} opt</span>
              {expandedIndex === qIdx ? (
                <ChevronUp className="w-4 h-4 text-gray-500" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-500" />
              )}
            </div>

            {/* Expanded Content */}
            {expandedIndex === qIdx && (
              <div className="px-4 pb-4 space-y-3 border-t border-white/5 pt-3">
                {/* Question Text */}
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wider mb-1 block">Question</label>
                  <textarea
                    value={q.question}
                    onChange={(e) => updateQuestion(qIdx, 'question', e.target.value)}
                    className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white 
                             focus:outline-none focus:border-accent-mint/50 focus:ring-1 focus:ring-accent-mint/20
                             resize-none transition-all"
                    rows={3}
                    placeholder="Enter question text..."
                  />
                </div>

                {/* Options */}
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wider mb-2 block">Options</label>
                  <div className="space-y-2">
                    {(q.pointers || []).map((pointer, pIdx) => (
                      <div key={pIdx} className="flex items-center gap-2 group">
                        <input
                          value={pointer[0]}
                          onChange={(e) => updatePointer(qIdx, pIdx, 0, e.target.value)}
                          className="w-14 bg-black/30 border border-white/10 rounded-lg px-2 py-1.5 text-sm text-accent-mint
                                   font-bold text-center focus:outline-none focus:border-accent-mint/50 transition-all"
                          placeholder="A)"
                        />
                        <div className="flex-1 space-y-1">
                          <input
                            value={pointer[1]}
                            onChange={(e) => updatePointer(qIdx, pIdx, 1, e.target.value)}
                            className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white
                                     focus:outline-none focus:border-accent-mint/50 focus:ring-1 focus:ring-accent-mint/20 transition-all"
                            placeholder="Option text..."
                          />
                          {pointer[1].includes('$') && (
                            <div className="px-1 py-0.5 bg-black/20 rounded text-xs text-accent-mint/60">
                              <MathText text={pointer[1]} />
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => removePointer(qIdx, pIdx)}
                          className="w-7 h-7 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 flex items-center justify-center
                                   opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => addPointer(qIdx)}
                    className="mt-2 text-xs text-accent-mint/70 hover:text-accent-mint flex items-center gap-1 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Option
                  </button>
                </div>

                {/* Delete Question */}
                <div className="flex justify-end pt-1">
                  <button
                    onClick={() => removeQuestion(qIdx)}
                    className="text-xs text-red-400/60 hover:text-red-400 flex items-center gap-1 transition-colors
                             px-2 py-1 rounded hover:bg-red-500/10"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Remove Question
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Add Question Button */}
        <button
          onClick={addQuestion}
          className="w-full py-3 rounded-xl border border-dashed border-white/10 hover:border-accent-mint/30 
                   text-gray-400 hover:text-accent-mint text-sm flex items-center justify-center gap-2
                   transition-all hover:bg-white/[0.02]"
        >
          <Plus className="w-4 h-4" /> Add Question Manually
        </button>
      </div>

      {/* Footer Actions */}
      <div className="px-4 py-4 border-t border-white/10 space-y-2 bg-[#151926]">
        {onAddMoreImages && (
          <button
            onClick={onAddMoreImages}
            disabled={isParsingMore}
            className="w-full py-2.5 rounded-xl border border-white/10 hover:border-accent-mint/30 
                     text-gray-300 hover:text-accent-mint text-sm flex items-center justify-center gap-2
                     transition-all hover:bg-white/[0.02] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isParsingMore ? (
              <>
                <div className="w-4 h-4 border-2 border-accent-mint/30 border-t-accent-mint rounded-full animate-spin" />
                Parsing Images...
              </>
            ) : (
              <>
                <ImagePlus className="w-4 h-4" /> Add More Question Images
              </>
            )}
          </button>
        )}

        <button
          onClick={() => onConfirm(editableQuestions.filter(q => q.question?.trim()))}
          disabled={editableQuestions.filter(q => q.question?.trim()).length === 0}
          className="w-full py-3 rounded-xl bg-gradient-to-r from-accent-mint to-emerald-500 text-black font-bold text-sm
                   flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-accent-mint/20
                   transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]"
        >
          <Check className="w-4 h-4" /> Confirm & Generate Slides ({editableQuestions.filter(q => q.question?.trim()).length})
        </button>
      </div>
    </div>
  );
}
