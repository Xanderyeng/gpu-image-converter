'use client';

import { JobCard } from './JobCard';
import { Button } from '@/components/ui/button';
import type { ConversionJob } from '@/lib/types';

interface ConversionQueueProps {
  jobs: ConversionJob[];
  onRemoveJob: (jobId: string) => void;
  onClearCompleted: () => void;
}

export function ConversionQueue({
  jobs,
  onRemoveJob,
  onClearCompleted,
}: ConversionQueueProps) {
  const completedCount = jobs.filter((j) => j.status === 'completed').length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">
          Conversion Queue ({jobs.length})
        </h2>
        {completedCount > 0 && (
          <Button variant="outline" size="sm" onClick={onClearCompleted}>
            Clear Completed ({completedCount})
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {jobs.map((job) => (
          <JobCard key={job.id} job={job} onRemove={() => onRemoveJob(job.id)} />
        ))}
      </div>
    </div>
  );
}
