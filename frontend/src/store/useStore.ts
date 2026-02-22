import { create } from "zustand";
import type { VideoMetadata, HistoryEntry, SSEEvent } from "@/lib/api";

export interface DownloadJob {
  id: string;
  url: string;
  title: string;
  format: string;
  quality: string;
  status: string;
  progress: number;
  speed?: string;
  eta?: string;
  filename?: string;
  file_size?: number;
  error?: string;
  thumbnail?: string;
}

interface AppState {
  // Theme
  theme: "dark" | "light";
  toggleTheme: () => void;

  // URL input
  urls: string[];
  setUrls: (urls: string[]) => void;
  addUrl: (url: string) => void;
  removeUrl: (index: number) => void;

  // Metadata
  metadataMap: Record<string, VideoMetadata>;
  setMetadata: (url: string, meta: VideoMetadata) => void;

  // Jobs
  jobs: DownloadJob[];
  addJob: (job: DownloadJob) => void;
  updateJob: (id: string, update: Partial<DownloadJob>) => void;
  removeJob: (id: string) => void;

  // History
  history: HistoryEntry[];
  setHistory: (h: HistoryEntry[]) => void;
  addHistory: (h: HistoryEntry) => void;

  // UI
  activeTab: "download" | "history" | "cookies";
  setActiveTab: (tab: "download" | "history" | "cookies") => void;
}

export const useStore = create<AppState>((set) => ({
  theme: "dark",
  toggleTheme: () =>
    set((s) => {
      const next = s.theme === "dark" ? "light" : "dark";
      document.documentElement.classList.toggle("dark", next === "dark");
      document.documentElement.classList.toggle("light", next === "light");
      return { theme: next };
    }),

  urls: [""],
  setUrls: (urls) => set({ urls }),
  addUrl: (url) => set((s) => ({ urls: [...s.urls, url] })),
  removeUrl: (i) => set((s) => ({ urls: s.urls.filter((_, idx) => idx !== i) })),

  metadataMap: {},
  setMetadata: (url, meta) =>
    set((s) => ({ metadataMap: { ...s.metadataMap, [url]: meta } })),

  jobs: [],
  addJob: (job) => set((s) => ({ jobs: [job, ...s.jobs] })),
  updateJob: (id, update) =>
    set((s) => ({
      jobs: s.jobs.map((j) => (j.id === id ? { ...j, ...update } : j)),
    })),
  removeJob: (id) => set((s) => ({ jobs: s.jobs.filter((j) => j.id !== id) })),

  history: [],
  setHistory: (history) => set({ history }),
  addHistory: (h) => set((s) => ({ history: [h, ...s.history].slice(0, 50) })),

  activeTab: "download",
  setActiveTab: (activeTab) => set({ activeTab }),
}));
