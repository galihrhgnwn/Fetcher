import { useEffect, useState } from "react";
import { Cookie, CheckCircle, Info } from "lucide-react";
import { formatBytes } from "@/lib/api";

interface CookieFile {
  file: string;
  platform: string;
  size: number;
}

export function CookiesPanel() {
  const [cookies, setCookies] = useState<CookieFile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/cookies")
      .then((r) => r.json())
      .then(setCookies)
      .catch(() => setCookies([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      {/* Info box */}
      <div className="card p-4 border-blue-900/40 bg-blue-950/20">
        <div className="flex gap-3">
          <Info size={16} className="text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-[var(--text-muted)]">
            <p className="font-medium text-blue-300 mb-1">How to add cookies</p>
            <p className="text-xs leading-relaxed">
              Place Netscape-format cookie files in the <code className="bg-[var(--bg-elevated)] px-1 rounded font-mono text-xs">cookies/</code> folder.
              Name them after the platform: <code className="bg-[var(--bg-elevated)] px-1 rounded font-mono text-xs">tiktok.txt</code>,{" "}
              <code className="bg-[var(--bg-elevated)] px-1 rounded font-mono text-xs">instagram.txt</code>,{" "}
              <code className="bg-[var(--bg-elevated)] px-1 rounded font-mono text-xs">youtube.txt</code>, etc.
            </p>
            <p className="text-xs mt-2 opacity-70">
              Export cookies using browser extensions like "Get cookies.txt LOCALLY" (Chrome/Firefox).
            </p>
          </div>
        </div>
      </div>

      {/* Cookie list */}
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-12 rounded-xl" />
          ))}
        </div>
      ) : cookies.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-[var(--text-subtle)]">
          <Cookie size={36} className="mb-3 opacity-30" />
          <p className="text-sm">No cookie files found</p>
          <p className="text-xs mt-1 opacity-70">Add .txt files to the cookies/ folder</p>
        </div>
      ) : (
        <div className="space-y-2">
          {cookies.map((c) => (
            <div key={c.file} className="card p-3 flex items-center gap-3">
              <CheckCircle size={16} className="text-emerald-400 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-[var(--text-primary)] capitalize">{c.platform}</p>
                <p className="text-xs text-[var(--text-muted)]">{c.file} · {formatBytes(c.size)}</p>
              </div>
              <span className="badge-green text-[10px]">Active</span>
            </div>
          ))}
        </div>
      )}

      {/* Supported platforms */}
      <div>
        <p className="text-xs text-[var(--text-subtle)] mb-2">Supported platforms</p>
        <div className="flex flex-wrap gap-1.5">
          {["youtube", "tiktok", "instagram", "twitter", "facebook", "vimeo", "twitch",
            "soundcloud", "reddit", "dailymotion", "bilibili", "nicovideo"].map((p) => (
            <span key={p} className={`badge text-[10px] ${
              cookies.some((c) => c.platform === p) ? "badge-green" : "badge-gray"
            }`}>
              {p}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
