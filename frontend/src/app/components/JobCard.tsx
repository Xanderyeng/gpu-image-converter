'use client';

import { Download, X, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import type { ConversionJob } from '@/lib/types';

interface JobCardProps {
  job: ConversionJob;
  onRemove: () => void;
}

export function JobCard({ job, onRemove }: JobCardProps) {
  const handleDownload = () => {
    if (!job.downloadUrl) return;

    const url = `${process.env.NEXT_PUBLIC_API_URL}${job.downloadUrl}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = job.downloadUrl.split('/').pop() || 'download';
    link.click();
  };

  return (
    <Card className="p-4">
      <div className="flex items-start gap-4">
        {/* Status Icon */}
        <div className="flex-shrink-0 mt-1">
          {job.status === 'pending' && (
            <Loader2 className="h-5 w-5 text-gray-400 animate-spin" />
          )}
          {job.status === 'processing' && (
            <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
          )}
          {job.status === 'completed' && (
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          )}
          {job.status === 'failed' && (
            <XCircle className="h-5 w-5 text-red-500" />
          )}
        </div>

        {/* Job Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-medium truncate">{job.filename}</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={onRemove}
              className="flex-shrink-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Status & Metadata */}
          <div className="flex flex-wrap items-center gap-2 mt-1 text-sm text-gray-500">
            <Badge
              variant={
                job.status === 'completed'
                  ? 'default'
                  : job.status === 'failed'
                  ? 'destructive'
                  : 'secondary'
              }
            >
              {job.status}
            </Badge>

            {job.metadata && (
              <>
                <span>•</span>
                <span>{job.metadata.duration.toFixed(2)}s</span>
                <span>•</span>
                <span>
                  {(job.metadata.outputSize / 1024 / 1024).toFixed(2)} MB
                </span>
                <span>•</span>
                <span className="text-green-600 font-medium">
                  {job.metadata.spaceSavedPercent.toFixed(0)}% smaller
                </span>
                {job.metadata.gpuUsed && (
                  <>
                    <span>•</span>
                    <Badge variant="outline" className="text-blue-600 border-blue-600">
                      GPU
                    </Badge>
                  </>
                )}
              </>
            )}
          </div>

          {/* Progress Bar */}
          {job.status === 'processing' && (
            <Progress value={job.progress} className="mt-2" />
          )}

          {/* Error Message */}
          {job.error && (
            <p className="mt-2 text-sm text-red-600">{job.error}</p>
          )}
        </div>

        {/* Download Button */}
        {job.status === 'completed' && job.downloadUrl && (
          <Button onClick={handleDownload} size="sm" className="flex-shrink-0">
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        )}
      </div>
    </Card>
  );
}
