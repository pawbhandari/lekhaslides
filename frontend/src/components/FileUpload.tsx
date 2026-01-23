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
            <label className="block text-sm font-medium text-gray-300 mb-2">
                {label}
            </label>

            {!file ? (
                <div
                    onDragEnter={handleDragIn}
                    onDragLeave={handleDragOut}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
            transition-all duration-200
            ${isDragging
                            ? 'border-accent-orange bg-accent-orange/10'
                            : 'border-gray-600 hover:border-accent-orange/50 hover:bg-chalkboard-light'
                        }
          `}
                >
                    <input
                        type="file"
                        accept={accept}
                        onChange={handleFileInput}
                        className="hidden"
                        id={`file-input-${label}`}
                    />
                    <label htmlFor={`file-input-${label}`} className="cursor-pointer">
                        <Upload className="w-12 h-12 mx-auto mb-4 text-accent-orange" />
                        <p className="text-gray-300 mb-2">
                            Drag & drop your file here, or <span className="text-accent-orange font-semibold">browse</span>
                        </p>
                        <p className="text-sm text-gray-500">
                            {accept === '.docx' ? 'Word Document (.docx)' : 'Image (JPG, PNG)'}
                        </p>
                    </label>
                </div>
            ) : (
                <div className="card flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <div className="p-3 bg-accent-orange/20 rounded-lg">
                            <Icon className="w-6 h-6 text-accent-orange" />
                        </div>
                        <div>
                            <p className="font-medium text-gray-100">{file.name}</p>
                            <p className="text-sm text-gray-400">{formatFileSize(file.size)}</p>
                        </div>
                    </div>
                    <button
                        onClick={removeFile}
                        className="p-2 hover:bg-chalkboard-light rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-400 hover:text-red-400" />
                    </button>
                </div>
            )}
        </div>
    );
};
