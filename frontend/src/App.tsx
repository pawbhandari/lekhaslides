import { useState } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import { FileUpload } from './components/FileUpload';
import { ConfigPanel } from './components/ConfigPanel';
import { PreviewCard } from './components/PreviewCard';
import { ProgressBar } from './components/ProgressBar';
import { DownloadButton } from './components/DownloadButton';
import { parseDocx, generatePreview, generatePPTX, downloadBlob } from './services/api';
import type { Config, Question } from './types';
import { Sparkles, RefreshCw } from 'lucide-react';

type AppState = 'upload' | 'preview' | 'generating' | 'complete';

function App() {
  // File states
  const [backgroundFile, setBackgroundFile] = useState<File | null>(null);
  const [docxFile, setDocxFile] = useState<File | null>(null);

  // Configuration
  const [config, setConfig] = useState<Config>({
    instructor_name: 'Mayank Agarwal',
    subtitle: '{ Basics with Knowledge }',
    badge_text: 'Make Your own Concept'
  });

  // Questions and preview
  const [questions, setQuestions] = useState<Question[]>([]);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Generation state
  const [appState, setAppState] = useState<AppState>('upload');
  const [generatedBlob, setGeneratedBlob] = useState<Blob | null>(null);

  // Handle file uploads and generate preview
  const handleFilesUploaded = async () => {
    if (!backgroundFile || !docxFile) return;

    try {
      setAppState('preview');
      toast.loading('Parsing questions...', { id: 'parse' });

      // Parse DOCX
      const parsed = await parseDocx(docxFile);
      console.log('Parsed DOCX response:', parsed);
      console.log('Questions array:', parsed.questions);
      console.log('First question:', parsed.questions[0]);

      setQuestions(parsed.questions);
      toast.success(`Found ${parsed.total} questions!`, { id: 'parse' });

      // Generate preview for first question
      if (!parsed.questions || parsed.questions.length === 0) {
        throw new Error('No questions found in document');
      }

      toast.loading('Generating preview...', { id: 'preview' });
      const previewImageUrl = await generatePreview(
        backgroundFile,
        parsed.questions[0],
        config
      );
      setPreviewUrl(previewImageUrl);
      toast.success('Preview ready!', { id: 'preview' });

    } catch (error) {
      console.error('Error processing files:', error);
      toast.error('Failed to process files. Please try again.', { id: 'parse' });
      setAppState('upload');
    }
  };

  // Generate all slides
  const handleGenerateAll = async () => {
    if (!backgroundFile || questions.length === 0) return;

    try {
      setAppState('generating');
      toast.loading('Generating all slides...', { id: 'generate' });

      const blob = await generatePPTX(backgroundFile, questions, config);
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
    setBackgroundFile(null);
    setDocxFile(null);
    setQuestions([]);
    setPreviewUrl(null);
    setGeneratedBlob(null);
    setAppState('upload');
    toast.success('Ready to create new slides!');
  };

  // Check if ready to generate preview
  const canGeneratePreview = backgroundFile && docxFile && appState === 'upload';

  return (
    <div className="min-h-screen bg-gradient-to-br from-chalkboard-dark via-chalkboard to-chalkboard-dark">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#3d4b65',
            color: '#f0f5fa',
            border: '1px solid #64dcb4',
          },
          success: {
            iconTheme: {
              primary: '#64dcb4',
              secondary: '#1a1f2e',
            },
          },
          error: {
            iconTheme: {
              primary: '#ff6b6b',
              secondary: '#1a1f2e',
            },
          },
        }}
      />

      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <Sparkles className="w-10 h-10 text-accent-yellow mr-3" />
            <h1 className="text-5xl font-bold bg-gradient-to-r from-accent-yellow via-accent-orange to-accent-mint bg-clip-text text-transparent">
              Lekhaslides
            </h1>
          </div>
          <p className="text-gray-400 text-lg">
            Transform your questions into beautiful presentation slides
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - File Uploads */}
          <div className="lg:col-span-2 space-y-6">
            {/* File Upload Section */}
            <div className="card">
              <h2 className="text-2xl font-bold text-accent-yellow mb-6">
                📁 Upload Files
              </h2>
              <div className="space-y-6">
                <FileUpload
                  label="Background Image (Chalkboard)"
                  accept=".jpg,.jpeg,.png"
                  onFileSelect={setBackgroundFile}
                  file={backgroundFile}
                  icon="image"
                />
                <FileUpload
                  label="Questions Document (.docx)"
                  accept=".docx"
                  onFileSelect={setDocxFile}
                  file={docxFile}
                  icon="document"
                />
              </div>

              {canGeneratePreview && (
                <button
                  onClick={handleFilesUploaded}
                  className="btn-primary w-full mt-6"
                >
                  🚀 Process Files & Generate Preview
                </button>
              )}
            </div>

            {/* Preview Section */}
            {appState !== 'upload' && questions.length > 0 && (
              <PreviewCard
                previewUrl={previewUrl}
                questions={questions}
                onApprove={handleGenerateAll}
                isGenerating={appState === 'generating'}
              />
            )}

            {/* Generation Progress */}
            {appState === 'generating' && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-300 mb-4">
                  Generating Slides...
                </h3>
                <ProgressBar
                  current={questions.length}
                  total={questions.length}
                  label="Processing all questions"
                />
                <p className="text-sm text-gray-400 mt-4 text-center">
                  Please wait while we create your presentation...
                </p>
              </div>
            )}

            {/* Download Section */}
            {appState === 'complete' && (
              <>
                <DownloadButton
                  onDownload={handleDownload}
                  filename="Lekhaslides_Presentation.pptx"
                  isComplete={true}
                />
                <button
                  onClick={handleReset}
                  className="btn-secondary w-full flex items-center justify-center space-x-2"
                >
                  <RefreshCw className="w-5 h-5" />
                  <span>Create New Presentation</span>
                </button>
              </>
            )}
          </div>

          {/* Right Column - Configuration */}
          <div className="lg:col-span-1">
            <ConfigPanel config={config} onChange={setConfig} />
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>Built with React, FastAPI, and Python PIL</p>
          <p className="mt-1">Transform education with technology ✨</p>
        </div>
      </div>
    </div>
  );
}

export default App;
