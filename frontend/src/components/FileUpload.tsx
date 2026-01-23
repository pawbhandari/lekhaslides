import React, { useCallback, useState } from 'react';
import { Upload, X, FileText, Image as ImageIcon } from 'lucide-react';

interface FileUploadProps {
    label: string;
    accept: string;
    onFileSelect: (file: File | null) => void;
    file: File | null;
    icon?: 'document' | 'image';
}

export const FileUpload: React.FC<FileUploadProps> = ({
    label,
    accept,
    onFileSelect,
    file,
    icon = 'document'
}) => {
    const [isDragging, setIsDragging] = useState(false);

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDragIn = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragOut = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            onFileSelect(files[0]);
        }
    }, [onFileSelect]);

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            onFileSelect(files[0]);
        }
    };

    const removeFile = () => {
        onFileSelect(null);
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    };

    const Icon = icon === 'document' ? FileText : ImageIcon;

    return (
        <div className="w-full">
            <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-300">
                    {label}
                </label>
                {file && (
                    <button
                        onClick={() => document.getElementById(`file-input-${label}`)?.click()}
                        className="text-xs text-accent-orange hover:text-accent-yellow transition-colors font-medium"
                    >
                        Replace
                    </button>
                )}
            </div>

            <input
                type="file"
                accept={accept}
                onChange={handleFileInput}
                className="hidden"
                id={`file-input-${label}`}
            />

            {!file ? (
                <div
                    onDragEnter={handleDragIn}
                    onDragLeave={handleDragOut}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    className={`
            border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
            transition-all duration-200
            ${isDragging
                            ? 'border-accent-orange bg-accent-orange/10'
                            : 'border-gray-600 hover:border-accent-orange/50 hover:bg-chalkboard-light'
                        }
          `}
                >
                    <label htmlFor={`file-input-${label}`} className="cursor-pointer block">
                        <Upload className="w-8 h-8 mx-auto mb-2 text-accent-orange" />
                        <p className="text-gray-300 text-sm mb-1">
                            <span className="text-accent-orange font-semibold">Click to upload</span> or drag and drop
                        </p>
                        <p className="text-xs text-gray-500">
                            {accept === '.docx' ? 'Word Document (.docx)' : 'Image (JPG, PNG)'}
                        </p>
                    </label>
                </div>
            ) : (
                <div className="bg-chalkboard-light border border-gray-600 rounded-lg p-3 flex items-center justify-between group">
                    <div className="flex items-center space-x-3 overflow-hidden">
                        <div className="p-2 bg-accent-orange/20 rounded-lg flex-shrink-0">
                            <Icon className="w-5 h-5 text-accent-orange" />
                        </div>
                        <div className="min-w-0">
                            <p className="font-medium text-gray-200 text-sm truncate" title={file.name}>{file.name}</p>
                            <p className="text-xs text-gray-400">{formatFileSize(file.size)}</p>
                        </div>
                    </div>
                    <button
                        onClick={removeFile}
                        className="p-1.5 hover:bg-gray-700 rounded-md transition-colors opacity-0 group-hover:opacity-100"
                        title="Remove file"
                    >
                        <X className="w-4 h-4 text-gray-400 hover:text-red-400" />
                    </button>
                </div>
            )}
        </div>
    );
};
