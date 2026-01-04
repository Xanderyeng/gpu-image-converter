# Component Reference

> **Complete reference for all frontend components**

## Component Library Structure

```
frontend/
├── app/components/           # Main application components
│   ├── ImageConverter.tsx   # Main container component
│   ├── FileUploadZone.tsx   # Drag & drop upload
│   ├── SettingsPanel.tsx    # Conversion settings
│   ├── ConversionQueue.tsx  # Job queue display
│   └── JobCard.tsx          # Individual job card
└── components/ui/           # shadcn/ui components
    ├── button.tsx
    ├── card.tsx
    ├── progress.tsx
    ├── select.tsx
    ├── slider.tsx
    └── ...
```

---

## Main Components

### ImageConverter

**Location:** `app/components/ImageConverter.tsx`

Main container component that orchestrates the entire conversion workflow.

**Props:** None (root component)

**State:**
- `jobs`: Array of conversion jobs
- `outputFormat`: Selected output format
- `quality`: Compression quality (1-100)
- `useGpu`: GPU acceleration toggle
- `sharpen`: Sharpen filter toggle
- `denoise`: Denoise filter toggle
- `isUploading`: Upload status

**Features:**
- File upload handling
- Job queue management
- Real-time status polling
- Settings management
- Toast notifications

**Usage:**
```tsx
import { ImageConverter } from '@/app/components/ImageConverter';

export default function Home() {
  return <ImageConverter />;
}
```

---

### FileUploadZone

**Location:** `app/components/FileUploadZone.tsx`

Drag-and-drop file upload component using react-dropzone.

**Props:**
```typescript
interface FileUploadZoneProps {
  onFilesAdded: (files: File[]) => void;
  isUploading: boolean;
}
```

**Features:**
- Drag and drop support
- Click to browse
- Multiple file selection
- File type validation
- Size limit enforcement (100MB per file)
- Visual feedback for drag state

**Accepted Formats:**
- PNG, JPEG, WebP, GIF, BMP, TIFF, HEIC, AVIF

**Usage:**
```tsx
<FileUploadZone
  onFilesAdded={(files) => handleFiles(files)}
  isUploading={isUploading}
/>
```

**Styling:**
- Dashed border (normal state)
- Solid blue border (drag active)
- Scale animation on drag
- Disabled state when uploading

---

### SettingsPanel

**Location:** `app/components/SettingsPanel.tsx`

Conversion settings configuration panel.

**Props:**
```typescript
interface SettingsPanelProps {
  outputFormat: ImageFormat;
  quality: number;
  useGpu: boolean;
  sharpen: boolean;
  denoise: boolean;
  onOutputFormatChange: (format: ImageFormat) => void;
  onQualityChange: (quality: number) => void;
  onUseGpuChange: (enabled: boolean) => void;
  onSharpenChange: (enabled: boolean) => void;
  onDenoiseChange: (enabled: boolean) => void;
}
```

**Settings:**

1. **Output Format Selector**
   - WebP (default)
   - JPEG
   - PNG
   - AVIF
   - GIF
   - BMP
   - TIFF

2. **Quality Slider**
   - Range: 1-100
   - Default: 90
   - Live preview of value

3. **GPU Acceleration Toggle**
   - Enables hardware acceleration
   - Shows GPU status indicator

4. **Image Enhancement Filters**
   - Sharpen: Edge enhancement
   - Denoise: Noise reduction

**Implementation:**
```tsx
export function SettingsPanel({
  outputFormat,
  quality,
  useGpu,
  sharpen,
  denoise,
  onOutputFormatChange,
  onQualityChange,
  onUseGpuChange,
  onSharpenChange,
  onDenoiseChange,
}: SettingsPanelProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Output Format */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Output Format
          </label>
          <Select value={outputFormat} onValueChange={onOutputFormatChange}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="webp">WebP (Recommended)</SelectItem>
              <SelectItem value="jpg">JPEG</SelectItem>
              <SelectItem value="png">PNG</SelectItem>
              <SelectItem value="avif">AVIF (Next-gen)</SelectItem>
              <SelectItem value="gif">GIF</SelectItem>
              <SelectItem value="bmp">BMP</SelectItem>
              <SelectItem value="tiff">TIFF</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Quality Slider */}
        <div>
          <label className="block text-sm font-medium mb-2">
            Quality: {quality}%
          </label>
          <Slider
            value={[quality]}
            onValueChange={([value]) => onQualityChange(value)}
            min={1}
            max={100}
            step={1}
            className="mt-2"
          />
        </div>

        {/* GPU Toggle */}
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="gpu"
            checked={useGpu}
            onChange={(e) => onUseGpuChange(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300"
          />
          <label htmlFor="gpu" className="text-sm font-medium">
            GPU Acceleration
          </label>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="sharpen"
            checked={sharpen}
            onChange={(e) => onSharpenChange(e.target.checked)}
          />
          <label htmlFor="sharpen" className="text-sm">Sharpen</label>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="denoise"
            checked={denoise}
            onChange={(e) => onDenoiseChange(e.target.checked)}
          />
          <label htmlFor="denoise" className="text-sm">Denoise</label>
        </div>
      </div>
    </div>
  );
}
```

---

### ConversionQueue

**Location:** `app/components/ConversionQueue.tsx`

Displays list of conversion jobs with status and actions.

**Props:**
```typescript
interface ConversionQueueProps {
  jobs: ConversionJob[];
  onRemoveJob: (jobId: string) => void;
  onClearCompleted: () => void;
}
```

**Features:**
- Real-time job status display
- Progress indicators
- Download buttons for completed jobs
- Remove individual jobs
- Clear all completed jobs
- Error display for failed jobs

**Job Statuses:**
- **Pending:** Waiting in queue (gray spinner)
- **Processing:** Currently converting (blue spinner + progress bar)
- **Completed:** Ready to download (green checkmark + download button)
- **Failed:** Error occurred (red X + error message)

**Implementation:**
```tsx
export function ConversionQueue({
  jobs,
  onRemoveJob,
  onClearCompleted,
}: ConversionQueueProps) {
  const completedCount = jobs.filter(j => j.status === 'completed').length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">
          Conversion Queue ({jobs.length})
        </h2>
        {completedCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={onClearCompleted}
          >
            Clear Completed ({completedCount})
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            onRemove={() => onRemoveJob(job.id)}
          />
        ))}
      </div>
    </div>
  );
}
```

---

### JobCard

**Location:** `app/components/JobCard.tsx`

Individual job card showing conversion status and metadata.

**Props:**
```typescript
interface JobCardProps {
  job: ConversionJob;
  onRemove: () => void;
}
```

**Display Elements:**

1. **Status Icon**
   - Pending: Spinner (gray)
   - Processing: Animated spinner (blue)
   - Completed: Checkmark (green)
   - Failed: X mark (red)

2. **Job Information**
   - Original filename
   - Status text
   - Duration (when completed)
   - File size (when completed)
   - Compression stats (when completed)
   - GPU usage indicator

3. **Progress Bar** (processing only)
   - Animated width based on progress
   - Blue color
   - Smooth transitions

4. **Actions**
   - Download button (completed)
   - Remove button (all states)

**Implementation:**
```tsx
import { Download, X, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import type { ConversionJob } from '@/lib/types';

export function JobCard({ job, onRemove }: JobCardProps) {
  const handleDownload = () => {
    const url = `${process.env.NEXT_PUBLIC_API_URL}${job.downloadUrl}`;
    const link = document.createElement('a');
    link.href = url;
    link.download = job.downloadUrl?.split('/').pop() || 'download';
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
            <Badge variant={
              job.status === 'completed' ? 'default' :
              job.status === 'failed' ? 'destructive' :
              'secondary'
            }>
              {job.status}
            </Badge>

            {job.metadata && (
              <>
                <span>•</span>
                <span>{job.metadata.duration}s</span>
                <span>•</span>
                <span>
                  {(job.metadata.outputSize / 1024 / 1024).toFixed(2)} MB
                </span>
                <span>•</span>
                <span>
                  {job.metadata.spaceSavedPercent}% smaller
                </span>
                {job.metadata.gpuUsed && (
                  <>
                    <span>•</span>
                    <Badge variant="outline" className="text-blue-600">
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
```

---

## shadcn/ui Components

### Button

```tsx
import { Button } from '@/components/ui/button';

// Variants
<Button variant="default">Default</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="link">Link</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>
```

### Card

```tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
</Card>
```

### Progress

```tsx
import { Progress } from '@/components/ui/progress';

<Progress value={progress} className="w-full" />
```

### Select

```tsx
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

<Select value={value} onValueChange={onChange}>
  <SelectTrigger>
    <SelectValue placeholder="Select..." />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>
```

### Slider

```tsx
import { Slider } from '@/components/ui/slider';

<Slider
  value={[value]}
  onValueChange={([newValue]) => setValue(newValue)}
  min={0}
  max={100}
  step={1}
/>
```

### Badge

```tsx
import { Badge } from '@/components/ui/badge';

<Badge variant="default">Default</Badge>
<Badge variant="secondary">Secondary</Badge>
<Badge variant="destructive">Error</Badge>
<Badge variant="outline">Outline</Badge>
```

### Toast

```tsx
import { useToast } from '@/components/ui/use-toast';

const { toast } = useToast();

toast({
  title: 'Success',
  description: 'Operation completed',
});

toast({
  title: 'Error',
  description: 'Something went wrong',
  variant: 'destructive',
});
```

---

## Utility Functions

### cn (Class Names)

**Location:** `lib/utils.ts`

Utility for conditional class names with Tailwind.

```tsx
import { cn } from '@/lib/utils';

<div className={cn(
  'base-class',
  isActive && 'active-class',
  isDisabled && 'disabled-class'
)} />
```

### formatBytes

Format file sizes for display.

```typescript
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
```

### formatDuration

Format conversion duration.

```typescript
export function formatDuration(seconds: number): string {
  if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;

  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes}m ${secs}s`;
}
```

---

## Styling Conventions

### Color Palette

```css
/* Status Colors */
.text-status-pending { @apply text-gray-500; }
.text-status-processing { @apply text-blue-500; }
.text-status-completed { @apply text-green-500; }
.text-status-failed { @apply text-red-500; }

/* Background Colors */
.bg-primary { @apply bg-slate-900; }
.bg-secondary { @apply bg-slate-100; }
.bg-success { @apply bg-green-50; }
.bg-error { @apply bg-red-50; }
```

### Spacing

```css
/* Container Spacing */
.container { @apply max-w-7xl mx-auto px-4 py-12; }

/* Card Spacing */
.card-padding { @apply p-4 md:p-6; }

/* Stack Spacing */
.stack-sm { @apply space-y-2; }
.stack { @apply space-y-4; }
.stack-lg { @apply space-y-6; }
```

### Responsive Design

```tsx
// Mobile-first approach
<div className="
  grid
  grid-cols-1
  md:grid-cols-2
  lg:grid-cols-3
  gap-4
" />

// Responsive text sizes
<h1 className="text-3xl md:text-4xl lg:text-5xl" />

// Responsive padding
<div className="p-4 md:p-6 lg:p-8" />
```

---

## Component Best Practices

### 1. Type Safety

Always define TypeScript interfaces for props:

```typescript
interface MyComponentProps {
  required: string;
  optional?: number;
  callback: (value: string) => void;
}

export function MyComponent({ required, optional, callback }: MyComponentProps) {
  // ...
}
```

### 2. State Management

Use appropriate hooks:

```typescript
// Local state
const [value, setValue] = useState<string>('');

// Derived state
const isValid = useMemo(() => value.length > 0, [value]);

// Side effects
useEffect(() => {
  // Cleanup logic
  return () => cleanup();
}, [dependencies]);

// Callbacks
const handleChange = useCallback((newValue: string) => {
  setValue(newValue);
}, []);
```

### 3. Error Handling

Always handle errors gracefully:

```typescript
try {
  const result = await riskyOperation();
  // Handle success
} catch (error) {
  toast({
    title: 'Error',
    description: error instanceof Error ? error.message : 'Unknown error',
    variant: 'destructive',
  });
}
```

### 4. Accessibility

Ensure components are accessible:

```tsx
<button
  aria-label="Remove job"
  aria-pressed={isActive}
  onClick={handleClick}
>
  <X className="h-4 w-4" />
  <span className="sr-only">Remove</span>
</button>
```

---

**For more information:**
- [Frontend Guide](./FRONTEND_GUIDE.md)
- [API Reference](../../backend/docs/API_REFERENCE.md)
- [shadcn/ui Documentation](https://ui.shadcn.com/)
