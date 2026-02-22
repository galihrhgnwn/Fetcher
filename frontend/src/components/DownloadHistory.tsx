import { useEffect } from "react";
import { History, ExternalLink, HardDrive, Clock } from "lucide-react";
import { getHistory, formatBytes } from "@/lib/api";
import { useStore } from "@/store/useStore";

export function DownloadHistory() {
  const { history, setHistory } = useStore();

  useEffect(() => {
    getHistory().then(setHistory).catch(() => {});
  }, []);

  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-[var(--text-subtle)]">
        <History size={40} className="mb-3 opacity-30" />
        <p className="text-sm">No downloads yet</p>
        <p className="text-xs mt-1 opacity-70">Completed downloads will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {history.map((h) => (
        <div key={h.id} className="card p-3 flex items-center gap-3 hover:border-[var(--border-light)] transition-colors">
          {h.thumbnail ? (
            <img
              src={h.thumbnail}
              alt={h.title}
              className="w-12 h-8 object-cover rounded flex-shrink-0"
              onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
            />
          ) : (
            <div className="w-12 h-8 rounded bg-[var(--bg-elevated)] flex items-center justify-center flex-shrink-0">
              <HardDrive size={14} className="text-[var(--text-subtle)]" />
            </div>
          )}

          <div className="flex-1 min-w-0">
            <p className="text-sm text-[var(--text-primary)] truncate">{h.title}</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="badge-gray text-[10px]">{h.format.toUpperCase()}</span>
              {h.file_size && (
                <span className="text-[11px] text-[var(--text-subtle)] flex items-center gap-1">
                  <HardDrive size={9} /> {formatBytes(h.file_size)}
                </span>
              )}
              <span className="text-[11px] text-[var(--text-subtle)] flex items-center gap-1">
                <Clock size={9} />
                {new Date(h.downloaded_at * 1000).toLocaleTimeString()}
              </span>
            </div>
          </div>

          <a
            href={h.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-ghost p-1.5 flex-shrink-0"
            title="Open original URL"
          >
            <ExternalLink size={13} />
          </a>
        </div>
      ))}
    </div>
  );
}
