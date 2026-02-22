# Cookies Folder

Place your **Netscape-format** cookie files here to enable authenticated downloads
from platforms that require login (TikTok, Instagram, Twitter/X, etc.).

## File Naming Convention

Name each file after its platform:

| Platform     | Filename            |
|--------------|---------------------|
| YouTube      | `youtube.txt`       |
| TikTok       | `tiktok.txt`        |
| Instagram    | `instagram.txt`     |
| Twitter / X  | `twitter.txt`       |
| Facebook     | `facebook.txt`      |
| Vimeo        | `vimeo.txt`         |
| Twitch       | `twitch.txt`        |
| SoundCloud   | `soundcloud.txt`    |
| Reddit       | `reddit.txt`        |
| Dailymotion  | `dailymotion.txt`   |
| Bilibili     | `bilibili.txt`      |
| NicoVideo    | `nicovideo.txt`     |
| Generic      | `cookies.txt`       |

## How to Export Cookies

### Chrome / Edge / Brave
1. Install the extension **"Get cookies.txt LOCALLY"**
   (https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Log in to the platform in your browser
3. Click the extension icon → **Export** → save as `tiktok.txt` (or the relevant name)
4. Copy the file into this `cookies/` folder

### Firefox
1. Install **"cookies.txt"** add-on
2. Log in to the platform
3. Click the add-on → **Export current site cookies**
4. Save into this folder

## Format

The file must be in **Netscape HTTP Cookie File** format:
```
# Netscape HTTP Cookie File
.tiktok.com	TRUE	/	TRUE	1999999999	sessionid	abc123...
```

## Security Notes

- **Never share your cookie files** — they contain session tokens that grant full account access.
- Cookie files are only read server-side and never exposed to the browser.
- Cookies expire when you log out or after the session timeout.
- This folder is listed in `.gitignore` — do not commit cookie files.
