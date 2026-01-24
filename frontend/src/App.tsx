import { useState, useEffect, useRef, useCallback } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import { FileUpload } from './components/FileUpload';
import { ConfigPanel } from './components/ConfigPanel';

import { ProgressBar } from './components/ProgressBar';
import { DownloadButton } from './components/DownloadButton';
import { DraggableResizableCard } from './components/DraggableResizableCard';

import { parseDocx, parseText, generatePreview, generatePPTX, downloadBlob } from './services/api';

// Imports cleaned
import type { Config, Question } from './types';
import { Sparkles, RefreshCw, FileText, Upload } from 'lucide-react';

type AppState = 'upload' | 'preview' | 'generating' | 'complete';
type InputMode = 'file' | 'text';

function App() {
  // File states
  const [backgroundFile, setBackgroundFile] = useState<File | null>(null);
  const [docxFile, setDocxFile] = useState<File | null>(null);

  // Text Input State
  const [inputMode, setInputMode] = useState<InputMode>('file');
  const [inputText, setInputText] = useState('');

  // Configuration
  const [config, setConfig] = useState<Config>(() => {
    let savedConfig = {};
    const saved = localStorage.getItem('lekha_config');
    if (saved) {
      try {
        savedConfig = JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse saved config:', e);
      }
    }

    // Default config
    const defaults: Config = {
      instructor_name: 'Mayank Agarwal',
      subtitle: '{ Basics with Knowledge }',
      badge_text: 'Make Your own Concept',
      font_size_heading: 60,
      font_size_body: 60 * 0.46, // Calculated
      font_text_color: '#F0C83C',
      pos_x: 0,
      pos_y: -25,
      watermark_text: '',
      pointer_spacing: -28,

      // Card defaults
      instructor_size: 60,
      instructor_color: '#F0C83C',
      subtitle_size: 30, // 60 * 0.5
      subtitle_color: '#64DCB4',
      badge_size: 24,
      badge_color: '#1E293B',
      badge_bg_color: '#FFB450',

      // Rotation defaults
      instructor_rotation: 0,
      subtitle_rotation: 0,
      badge_rotation: -2
    };

    return { ...defaults, ...savedConfig };
  });

  const [selectedCard, setSelectedCard] = useState<'instructor' | 'subtitle' | 'badge' | null>(null);

  // Save config to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('lekha_config', JSON.stringify(config));
  }, [config]);

  // Questions and preview
  const [questions, setQuestions] = useState<Question[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Generation state
  const [appState, setAppState] = useState<AppState>('upload');
  const [generatedBlob, setGeneratedBlob] = useState<Blob | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  // Container Scale for responsiveness (Preview is scaling down 1920p layout)
  const [containerScale, setContainerScale] = useState(0.5);
  const previewElementRef = useRef<HTMLDivElement>(null);

  // Manual Preview Trigger
  const [triggerPreview, setTriggerPreview] = useState(0);
  const handleManualRefresh = () => setTriggerPreview(prev => prev + 1);

  // Sync container scale
  useEffect(() => {
    const updateScale = () => {
      if (previewElementRef.current) {
        const rect = previewElementRef.current.getBoundingClientRect();
        // Scale = current / original
        setContainerScale(rect.width / 1920);
      }
    };

    // Initial update
    updateScale();

    // Listen for resize
    window.addEventListener('resize', updateScale);

    // Also update when preview updates (layout might shift)
    return () => window.removeEventListener('resize', updateScale);
  }, [previewElementRef.current, previewUrl]);

  // Update config from card interactions (Memoized to prevent drag interruptions)
  const handleCardUpdate = useCallback((id: string, attrs: { x: number; y: number; fontSize: number; rotation: number }) => {
    setConfig(prev => {
      if (id === 'instructor') {
        return { ...prev, instructor_x: attrs.x, instructor_y: attrs.y, instructor_size: attrs.fontSize, instructor_rotation: attrs.rotation };
      }
      if (id === 'subtitle') {
        return { ...prev, subtitle_x: attrs.x, subtitle_y: attrs.y, subtitle_size: attrs.fontSize, subtitle_rotation: attrs.rotation };
      }
      if (id === 'badge') {
        return { ...prev, badge_x: attrs.x, badge_y: attrs.y, badge_size: attrs.fontSize, badge_rotation: attrs.rotation };
      }
      return prev;
    });
  }, []);

  // Handle file uploads and generate preview
  const handleProcessContent = async () => {
    if (!backgroundFile) return;
    if (inputMode === 'file' && !docxFile) return;
    if (inputMode === 'text' && !inputText.trim()) return;

    try {
      setAppState('preview');
      toast.loading('Parsing content...', { id: 'parse' });

      let parsed;
      if (inputMode === 'file' && docxFile) {
        parsed = await parseDocx(docxFile);
      } else {
        parsed = await parseText(inputText);
      }

      console.log('Parsed response:', parsed);
      console.log('Questions array:', parsed.questions);
      console.log('First question:', parsed.questions[0]);

      setQuestions(parsed.questions);
      toast.success(`Found ${parsed.total} questions!`, { id: 'parse' });

      // Generate preview for first question
      if (!parsed.questions || parsed.questions.length === 0) {
        throw new Error('No questions found in content');
      }

      toast.loading('Generating preview...', { id: 'preview' });
      const previewImageUrl = await generatePreview(
        backgroundFile,
        parsed.questions[0],
        { ...config, render_badge: false, render_instructor: false, render_subtitle: false }
      );
      setPreviewUrl(previewImageUrl);
      toast.success('Preview ready!', { id: 'preview' });

    } catch (error: any) {
      console.error('Error processing content:', error);
      const msg = error.response?.data?.detail || 'Failed to process content. Please try again.';
      toast.error(msg, { id: 'parse', duration: 5000 });
      setAppState('upload');
    }
  };

  // Generation progress state
  const [generationProgress, setGenerationProgress] = useState({ current: 0, total: 0 });

  // Generate all slides
  const handleGenerateAll = async () => {
    if (!backgroundFile || questions.length === 0) return;

    try {
      setAppState('generating');
      setGenerationProgress({ current: 0, total: questions.length });
      toast.loading('Generating all slides...', { id: 'generate' });

      const blob = await generatePPTX(
        backgroundFile,
        questions,
        config,
        (current, total) => {
          setGenerationProgress({ current, total });
        }
      );
      setGeneratedBlob(blob);

      setAppState('complete');
      toast.success('Slides generated successfully!', { id: 'generate' });

    } catch (error) {
      console.error('Error generating PPTX:', error);
      toast.error('Failed to generate slides. Please try again.', { id: 'generate' });
      setAppState('preview');
    }
  };

  // Download PPTX
  const handleDownload = () => {
    if (generatedBlob) {
      downloadBlob(generatedBlob, 'Lekhaslides_Presentation.pptx');
      toast.success('Download started!');
    }
  };

  // Reset to start over
  const handleReset = () => {
    // Keep background file
    setDocxFile(null);
    setQuestions([]);
    setPreviewUrl(null);
    setGeneratedBlob(null);
    setAppState('upload');
    toast.success('Ready to create new slides! Background kept.');
  };

  // Real-time preview update (Manual trigger only)
  useEffect(() => {
    if (triggerPreview === 0) return;

    const controller = new AbortController();

    const updatePreview = async () => {
      if (!backgroundFile || (!docxFile && !inputText) || questions.length === 0) return;

      console.log('Fetching new preview...');
      setIsPreviewLoading(true);
      try {
        const previewImageUrl = await generatePreview(
          backgroundFile,
          questions[0],
          { ...config, render_badge: false, render_instructor: false, render_subtitle: false },
          controller.signal
        );
        console.log('Preview updated');
        setPreviewUrl(previewImageUrl);
      } catch (error: any) {
        if (error.name === 'CanceledError' || error.name === 'AbortError') return;
        console.error('Error updating preview:', error);
      } finally {
        if (!controller.signal.aborted) {
          setIsPreviewLoading(false);
        }
      }
    };

    updatePreview();

    return () => controller.abort();
  }, [triggerPreview]); // Run ONLY on manual trigger // eslint-disable-line react-hooks/exhaustive-deps

  // Check if ready to generate preview
  const canGeneratePreview = backgroundFile && ((inputMode === 'file' && docxFile) || (inputMode === 'text' && inputText.trim().length > 0)) && appState === 'upload';

  return (
    <div className="h-screen flex bg-chalkboard-dark overflow-hidden font-sans selection:bg-accent-orange/30">
      <Toaster position="top-center" toastOptions={{
        style: { background: 'rgba(30, 41, 59, 0.9)', color: '#f8fafc', border: '1px solid rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' },
        success: { iconTheme: { primary: '#4ade80', secondary: '#1e293b' } },
        error: { iconTheme: { primary: '#f87171', secondary: '#1e293b' } },
      }} />

      {/* LEFT SIDEBAR - CONTROLS */}
      <div className="w-[420px] flex-shrink-0 border-r border-white/5 bg-[#1a1f2e] flex flex-col h-full z-20 shadow-[4px_0_24px_rgba(0,0,0,0.4)]">
        {/* Sidebar Header */}
        <div className="p-8 border-b border-white/5 bg-gradient-to-b from-white/5 to-transparent backdrop-blur-md text-center">
          <div className="inline-flex p-3 bg-white/5 rounded-2xl mb-4 shadow-inner border border-white/5 animate-pulse-slow">
            <Sparkles className="w-8 h-8 text-accent-yellow" />
          </div>
          <h1 className="text-3xl font-extrabold bg-gradient-to-r from-accent-yellow via-accent-orange to-accent-mint bg-clip-text text-transparent tracking-tight mb-1">
            Lekhaslides
          </h1>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-[0.2em]">Studio Edition</p>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">

          {/* Project Setup Group */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2 mb-4">
              <div className="h-px bg-white/10 flex-1"></div>
              <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">Project Files</span>
              <div className="h-px bg-white/10 flex-1"></div>
            </div>

            <div className="bg-black/20 rounded-2xl p-2 space-y-2 border border-white/5">
              <FileUpload
                label="Background (16:9)"
                accept=".jpg,.jpeg,.png"
                onFileSelect={setBackgroundFile}
                file={backgroundFile}
                icon="image"
              />
              <div className="w-full h-px bg-white/5"></div>

              {/* Tabs for Input Mode */}
              <div className="grid grid-cols-2 gap-1 p-1 bg-black/40 rounded-lg mx-1 mt-2">
                <button
                  onClick={() => setInputMode('file')}
                  className={`py-2 px-3 rounded-md text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${inputMode === 'file' ? 'bg-white/10 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'}`}
                >
                  <Upload className="w-3 h-3" />
                  <span>Upload File</span>
                </button>
                <button
                  onClick={() => setInputMode('text')}
                  className={`py-2 px-3 rounded-md text-xs font-semibold flex items-center justify-center space-x-2 transition-all ${inputMode === 'text' ? 'bg-white/10 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'}`}
                >
                  <FileText className="w-3 h-3" />
                  <span>Paste Text</span>
                </button>
              </div>

              {inputMode === 'file' ? (
                <FileUpload
                  label="Questions (.docx, .md, .txt)"
                  accept=".docx,.md,.txt,.gdoc"
                  onFileSelect={setDocxFile}
                  file={docxFile}
                  icon="document"
                />
              ) : (
                <div className="p-2">
                  <label className="text-xs text-gray-400 uppercase font-semibold block mb-2 px-1">Raw Content</label>
                  <textarea
                    className="w-full h-40 bg-white/5 border border-white/10 rounded-xl p-3 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-accent-mint/50 resize-none font-mono"
                    placeholder={`1. What is SCM?\n- Definition: It is...\n\n2. Explain...`}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                  />
                </div>
              )}

            </div>

            {canGeneratePreview && (
              <button
                onClick={handleProcessContent}
                className="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-accent-mint font-semibold 
                      transition-all duration-200 flex items-center justify-center space-x-2 group hover:shadow-[0_0_15px_rgba(100,220,180,0.2)]"
              >
                <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
                <span>Process & Preview</span>
              </button>
            )}
          </div>

          <div>
            <ConfigPanel config={config} onChange={setConfig} />
          </div>
        </div>

        {/* Sidebar Footer - Actions */}
        <div className="p-6 border-t border-white/5 bg-[#151926]">
          {appState === 'preview' || appState === 'upload' ? (
            <button
              onClick={handleGenerateAll}
              disabled={!previewUrl}
              className={`btn-primary w-full ${!previewUrl && 'opacity-50 cursor-not-allowed grayscale'}`}
            >
              <span className="text-lg">Export Slides</span>
              {previewUrl && <Sparkles className="w-5 h-5 animate-pulse" />}
            </button>
          ) : appState === 'generating' ? (
            <div className="space-y-3 bg-white/5 p-4 rounded-xl border border-white/10">
              <div className="flex justify-between text-sm text-gray-300 font-medium">
                <span className="flex items-center"><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Generating slide {generationProgress.current} of {generationProgress.total}...</span>
                <span className="text-accent-mint">{generationProgress.total > 0 ? Math.round((generationProgress.current / generationProgress.total) * 100) : 0}%</span>
              </div>
              <ProgressBar current={generationProgress.current} total={generationProgress.total} label="" />
            </div>
          ) : (
            <div className="space-y-4">
              <DownloadButton
                onDownload={handleDownload}
                filename="Lekhaslides.pptx"
                isComplete={true}
              />
              <button onClick={handleReset} className="w-full text-gray-500 hover:text-gray-300 text-sm py-2 transition-colors">
                Start New Project
              </button>
            </div>
          )}
        </div>
      </div>

      {/* RIGHT MAIN AREA - PREVIEW */}
      <div className="flex-1 bg-[#0f111a] relative overflow-hidden flex flex-col items-center justify-center p-12">
        {/* Ambient Background Glows */}
        <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] bg-accent-orange/5 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-[-20%] left-[-10%] w-[600px] h-[600px] bg-accent-mint/5 rounded-full blur-[120px] pointer-events-none"></div>

        <div className="absolute inset-0 opacity-[0.03]"
          style={{ backgroundImage: 'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
        </div>

        <div className="relative z-10 w-full max-w-[1400px] flex flex-col h-full">
          {previewUrl ? (
            <div className="flex-1 flex flex-col justify-center space-y-6 animate-in fade-in duration-700 slide-in-from-bottom-4">
              <div className="flex items-center space-x-3">
                <div className="h-2 w-2 rounded-full bg-accent-orange animate-pulse"></div>
                <h2 className="text-gray-400 font-medium text-sm tracking-wide">LIVE PREVIEW</h2>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleManualRefresh}
                  className="bg-accent-mint/10 hover:bg-accent-mint/20 text-accent-mint text-xs px-3 py-1.5 rounded-full border border-accent-mint/30 transition-all flex items-center space-x-1 font-bold"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Update Preview</span>
                </button>
                <div className="bg-white/5 px-3 py-1 rounded-full border border-white/10 text-xs text-gray-400 font-mono">
                  1920 x 1080
                </div>
              </div>

              <div className="relative group rounded-2xl p-1 bg-gradient-to-b from-white/10 to-transparent shadow-2xl">
                <div className="rounded-xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/5 relative z-10 bg-[#1a1f2e]">
                  {/* Aspect Ratio Box 16:9 */}
                  <div
                    className="aspect-video relative select-none"
                    onClick={() => setSelectedCard(null)} // Click background to deselect
                    ref={previewElementRef}
                  >
                    {isPreviewLoading && (
                      <div className="absolute inset-0 z-20 flex items-center justify-center bg-black/40 backdrop-blur-[2px] transition-all duration-200">
                        <RefreshCw className="w-8 h-8 text-accent-yellow animate-spin" />
                      </div>
                    )}
                    <img
                      src={previewUrl}
                      alt="Slide Preview"
                      className="absolute inset-0 w-full h-full object-contain pointer-events-none"
                    />

                    {/* Instructor Card */}
                    {config.instructor_name && (
                      <DraggableResizableCard
                        id="instructor"
                        text={config.instructor_name}
                        x={config.instructor_x !== undefined ? config.instructor_x : 80}
                        y={config.instructor_y !== undefined ? config.instructor_y : 60}
                        fontSize={config.instructor_size || 60}
                        color={config.instructor_color || '#F0C83C'}
                        rotation={config.instructor_rotation || 0}
                        fontFamily={config.font_family || 'Chalk'}
                        isBadge={false}
                        containerScale={containerScale}
                        isSelected={selectedCard === 'instructor'}
                        onSelect={() => setSelectedCard('instructor')}
                        onChange={(attrs) => handleCardUpdate('instructor', attrs)}
                        onColorChange={(c) => setConfig(prev => ({ ...prev, instructor_color: c }))}
                      />
                    )}

                    {/* Subtitle Card */}
                    {config.subtitle && (
                      <DraggableResizableCard
                        id="subtitle"
                        text={config.subtitle}
                        x={config.subtitle_x !== undefined ? config.subtitle_x : 80}
                        y={config.subtitle_y !== undefined ? config.subtitle_y : 110}
                        fontSize={config.subtitle_size || 30}
                        color={config.subtitle_color || '#64DCB4'}
                        rotation={config.subtitle_rotation || 0}
                        fontFamily={config.font_family || 'Chalk'}
                        isBadge={false}
                        containerScale={containerScale}
                        isSelected={selectedCard === 'subtitle'}
                        onSelect={() => setSelectedCard('subtitle')}
                        onChange={(attrs) => handleCardUpdate('subtitle', attrs)}
                        onColorChange={(c) => setConfig(prev => ({ ...prev, subtitle_color: c }))}
                      />
                    )}

                    {/* Badge Card */}
                    {config.badge_text && (
                      <DraggableResizableCard
                        id="badge"
                        text={config.badge_text}
                        x={config.badge_x !== undefined ? config.badge_x : 1490}
                        y={config.badge_y !== undefined ? config.badge_y : 60}
                        fontSize={config.badge_size || 24}
                        color={config.badge_color || '#1E293B'}
                        rotation={config.badge_rotation !== undefined ? config.badge_rotation : -2}
                        fontFamily={config.font_family || 'Chalk'}
                        backgroundColor={config.badge_bg_color || '#FFB450'}
                        isBadge={true}
                        containerScale={containerScale}
                        isSelected={selectedCard === 'badge'}
                        onSelect={() => setSelectedCard('badge')}
                        onChange={(attrs) => handleCardUpdate('badge', attrs)}
                        onColorChange={(c) => setConfig(prev => ({ ...prev, badge_color: c }))}
                      />
                    )}


                  </div>
                </div>
                {/* Reflection Effect */}
                <div className="absolute -bottom-[20px] left-4 right-4 h-[20px] bg-black/40 blur-xl rounded-[100%]"></div>
              </div>

              <p className="text-center text-gray-500 text-sm font-medium">
                Adjustments update in real-time
              </p>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center space-y-8">
              <div className="relative">
                <div className="absolute inset-0 bg-accent-orange/20 blur-3xl rounded-full"></div>
                <div className="w-40 h-40 border border-white/10 bg-white/5 backdrop-blur-sm rounded-[2rem] flex items-center justify-center animate-float relative z-10 shadow-2xl">
                  <Sparkles className="w-16 h-16 text-white/20" />
                </div>
              </div>
              <div className="space-y-2 max-w-lg">
                <h3 className="text-3xl font-bold text-gray-200">Ready to Design</h3>
                <p className="text-gray-500 text-lg leading-relaxed">
                  Upload your content on the left sidebar to generate high-quality presentation slides instantly.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
