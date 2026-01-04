'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileImage } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface FileUploadZoneProps {
  onFilesAdded: (files: File[]) => void;
  isUploading: boolean;
}

export function FileUploadZone({ onFilesAdded, isUploading }: FileUploadZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      onFilesAdded(acceptedFiles);
    },
    [onFilesAdded]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff', '.heic', '.avif'],
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: true,
    disabled: isUploading,
  });

  return (
    <Card
      {...getRootProps()}
      className={`
        relative overflow-hidden cursor-pointer transition-all duration-200
        ${isDragActive
          ? 'border-2 border-blue-500 bg-blue-50 dark:bg-blue-950 scale-[1.02]'
          : 'border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600'
        }
        ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />

      <div className="p-16 text-center">
        <div className="flex justify-center mb-6">
          {isDragActive ? (
            <FileImage className="h-16 w-16 text-blue-500 animate-bounce" />
          ) : (
            <Upload className="h-16 w-16 text-slate-400 dark:text-slate-600" />
          )}
        </div>

        <h3 className="text-2xl font-semibold mb-2">
          {isDragActive
            ? 'Drop images here...'
            : isUploading
            ? 'Uploading...'
            : 'Drag & drop images here'}
        </h3>

        <p className="text-slate-500 dark:text-slate-400 mb-4">
          or click to browse your files
        </p>

        <div className="flex flex-wrap justify-center gap-2 text-xs text-slate-400">
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">PNG</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">JPEG</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">WebP</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">GIF</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">BMP</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">TIFF</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">HEIC</span>
          <span className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800">AVIF</span>
        </div>

        <p className="mt-4 text-sm text-slate-400">
          Maximum file size: 100MB per image
        </p>
      </div>
    </Card>
  );
}