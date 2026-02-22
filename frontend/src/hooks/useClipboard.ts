import { useEffect, useCallback } from "react";

const URL_REGEX = /https?:\/\/[^\s"'<>]+/i;

export function useClipboardPaste(onUrl: (url: string) => void) {
  const handleFocus = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text && URL_REGEX.test(text.trim())) {
        onUrl(text.trim());
      }
    } catch {
      // Permission denied or not supported — silently ignore
    }
  }, [onUrl]);

  useEffect(() => {
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [handleFocus]);
}
