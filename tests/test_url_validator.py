"""Tests for URL validator."""
import pytest
from backend.url_validator import validate_url, _classify


class TestValidateUrl:
    def test_valid_youtube(self):
        r = validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert r.valid is True
        assert r.url_type == "youtube"

    def test_valid_tiktok(self):
        r = validate_url("https://www.tiktok.com/@user/video/123456")
        assert r.valid is True
        assert r.url_type == "tiktok"

    def test_valid_instagram(self):
        r = validate_url("https://www.instagram.com/p/ABC123/")
        assert r.valid is True
        assert r.url_type == "instagram"

    def test_valid_twitter(self):
        r = validate_url("https://twitter.com/user/status/123")
        assert r.valid is True
        assert r.url_type == "twitter"

    def test_valid_x_com(self):
        r = validate_url("https://x.com/user/status/123")
        assert r.valid is True
        assert r.url_type == "twitter"

    def test_valid_direct_mp4(self):
        r = validate_url("https://example.com/video.mp4")
        assert r.valid is True
        assert r.url_type == "direct_file"

    def test_valid_direct_mp3(self):
        r = validate_url("https://example.com/audio.mp3")
        assert r.valid is True
        assert r.url_type == "direct_file"

    def test_valid_direct_zip(self):
        r = validate_url("https://example.com/archive.zip")
        assert r.valid is True
        assert r.url_type == "direct_file"

    def test_auto_prepend_https(self):
        r = validate_url("youtube.com/watch?v=abc")
        assert r.valid is True
        assert r.normalised.startswith("https://")

    def test_empty_url(self):
        r = validate_url("")
        assert r.valid is False
        assert r.error is not None

    def test_ftp_rejected(self):
        r = validate_url("ftp://example.com/file.mp4")
        assert r.valid is False

    def test_localhost_rejected(self):
        r = validate_url("http://localhost/admin")
        assert r.valid is False

    def test_private_ip_rejected(self):
        r = validate_url("http://192.168.1.1/file.mp4")
        assert r.valid is False

    def test_127_rejected(self):
        r = validate_url("http://127.0.0.1:8080/secret")
        assert r.valid is False

    def test_soundcloud(self):
        r = validate_url("https://soundcloud.com/artist/track")
        assert r.valid is True
        assert r.url_type == "soundcloud"

    def test_vimeo(self):
        r = validate_url("https://vimeo.com/123456789")
        assert r.valid is True
        assert r.url_type == "vimeo"

    def test_youtube_shorts(self):
        r = validate_url("https://youtube.com/shorts/abc123")
        assert r.valid is True
        assert r.url_type == "youtube"

    def test_normalised_strips_whitespace(self):
        r = validate_url("  https://youtube.com/watch?v=abc  ")
        assert r.valid is True
        assert r.normalised == "https://youtube.com/watch?v=abc"

    def test_generic_web(self):
        r = validate_url("https://example.com/some-video-page")
        assert r.valid is True
        assert r.url_type == "generic_web"

    def test_bilibili(self):
        r = validate_url("https://www.bilibili.com/video/BV1xx411c7mD")
        assert r.valid is True
        assert r.url_type == "bilibili"
