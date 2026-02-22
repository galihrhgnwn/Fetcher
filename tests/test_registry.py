"""Tests for extractor registry."""
import pytest
from backend.extractors.registry import ExtractorRegistry
from backend.extractors.ytdlp_extractor import YtDlpExtractor
from backend.extractors.direct_file_extractor import DirectFileExtractor


class TestExtractorRegistry:
    def setup_method(self):
        self.registry = ExtractorRegistry()
        self.registry.register(DirectFileExtractor())
        self.registry.register(YtDlpExtractor())

    def test_resolves_youtube(self):
        e = self.registry.resolve("https://www.youtube.com/watch?v=abc")
        assert e.name == "yt-dlp"

    def test_resolves_tiktok(self):
        e = self.registry.resolve("https://www.tiktok.com/@user/video/123")
        assert e.name == "yt-dlp"

    def test_resolves_direct_mp4(self):
        e = self.registry.resolve("https://cdn.example.com/video.mp4")
        assert e.name == "direct-file"

    def test_resolves_direct_mp3(self):
        e = self.registry.resolve("https://cdn.example.com/audio.mp3")
        assert e.name == "direct-file"

    def test_resolves_direct_zip(self):
        e = self.registry.resolve("https://cdn.example.com/archive.zip")
        assert e.name == "direct-file"

    def test_resolves_soundcloud(self):
        e = self.registry.resolve("https://soundcloud.com/artist/track")
        assert e.name == "yt-dlp"

    def test_resolves_instagram(self):
        e = self.registry.resolve("https://www.instagram.com/p/ABC/")
        assert e.name == "yt-dlp"

    def test_priority_order(self):
        """Higher priority extractor should win when both can handle."""
        extractors = self.registry.list_extractors()
        priorities = [e["priority"] for e in extractors]
        assert priorities == sorted(priorities, reverse=True)

    def test_raises_for_unknown(self):
        """Registry should raise when no extractor matches."""
        # Create a registry with no extractors
        empty = ExtractorRegistry()
        with pytest.raises(RuntimeError, match="No extractor"):
            empty.resolve("https://example.com/page")

    def test_list_extractors(self):
        result = self.registry.list_extractors()
        assert len(result) == 2
        names = {e["name"] for e in result}
        assert "yt-dlp" in names
        assert "direct-file" in names

    def test_len(self):
        assert len(self.registry) == 2

    def test_can_register_custom(self):
        from backend.extractors.base import IExtractor, DownloadResult
        from backend.models import VideoMetadata

        class MyExtractor(IExtractor):
            name = "my-extractor"
            priority = 20

            def can_handle(self, url):
                return "mysite.com" in url

            async def get_metadata(self, url, cookie_file=None):
                return VideoMetadata(title="test", formats=[])

            async def download(self, url, format, quality, output_dir, job_id, progress_cb, cookie_file=None):
                return DownloadResult(file_path="/tmp/test.mp4", filename="test.mp4")

        self.registry.register(MyExtractor())
        e = self.registry.resolve("https://mysite.com/video")
        assert e.name == "my-extractor"
