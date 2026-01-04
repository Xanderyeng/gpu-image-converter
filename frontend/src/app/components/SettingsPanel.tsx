'use client';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import type { ImageFormat } from '@/lib/types';

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