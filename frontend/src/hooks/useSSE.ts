import { useEffect, useRef } from "react";
import { getProgressUrl, type SSEEvent } from "@/lib/api";

export function useSSE(
  jobId: string | null,
  onEvent: (event: SSEEvent) => void,
  onClose?: () => void
) {
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const es = new EventSource(getProgressUrl(jobId));
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const data: SSEEvent = JSON.parse(e.data);
        onEvent(data);
        if (data.status === "done" || data.status === "error" || data.status === "cancelled") {
          es.close();
          onClose?.();
        }
      } catch {
        // ignore parse errors
      }
    };

    es.addEventListener("close", () => {
      es.close();
      onClose?.();
    });

    es.onerror = () => {
      es.close();
    };

    return () => {
      es.close();
    };
  }, [jobId]);
}
