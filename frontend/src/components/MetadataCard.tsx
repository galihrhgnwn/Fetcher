import { Clock, Eye, User, HardDrive } from "lucide-react";
import type { VideoMetadata } from "@/lib/api";
import { formatBytes, formatDuration } from "@/lib/api";

interface Props {
  meta: VideoMetadata;
  urlType?: string;
}

export function MetadataCard({ meta, urlType }: Props) {
  return (
    <div className="card p-4 animate-slide-up">
      <div className="flex gap-4">
        {/* Thumbnail */}
        {meta.thumbnail && (
          <div className="flex-shrink-0">
            <img
              src={meta.thumbnail}
              alt={meta.title}
              className="w-32 h-20 object-cover rounded-lg border border-[var(--border)]"
              onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
            />
          </div>
        )}

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-[var(--text-primary)] text-sm leading-snug line-clamp-2 mb-2">
            {meta.title}
          </h3>

          <div className="flex flex-wrap gap-3 text-xs text-[var(--text-muted)]">
            {meta.duration && (
              <span className="flex items-center gap-1">
                <Clock size={11} />
                {formatDuration(meta.duration)}
              </span>
            )}
            {meta.uploader && (
              <span className="flex items-center gap-1">
                <User size={11} />
                <span className="truncate max-w-[120px]">{meta.uploader}</span>
              </span>
            )}
            {meta.view_count && (
              <span className="flex items-center gap-1">
                <Eye size={11} />
                {meta.view_count.toLocaleString()} views
              </span>
            )}
            {meta.estimated_size && (
              <span className="flex items-center gap-1">
                <HardDrive size={11} />
                ~{formatBytes(meta.estimated_size)}
              </span>
            )}
          </div>

          <div className="flex flex-wrap gap-1.5 mt-2">
            {meta.is_audio_only && (
              <span className="badge-purple text-xs">Audio Only</span>
            )}
            {meta.extractor && (
              <span className="badge-gray text-xs">{meta.extractor}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
