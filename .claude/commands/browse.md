# /browse - Headless Browser Automation

Persistent headless Chromium via Chrome DevTools Protocol (CDP). ~100ms per command, stateful sessions.

## Prerequisites

```powershell
# Install playwright chromium (one-time)
npm install playwright
npx playwright install chromium

# Build browse binary (one-time)
cd D:\Downloads\gstack-main
& "C:\Users\Hakan\.bun\bin\bun.exe" build --compile browse/src/cli.ts --outfile browse/dist/browse
```

## Start CDP daemon

```powershell
# Launch headless Chromium on default port 9222
& 'D:\Hank\.claude\hooks\chrome-cdp.ps1'

# Or specify a port
& 'D:\Hank\.claude\hooks\chrome-cdp.ps1' -Port 9223
```

The script outputs the port number and exits. Chromium continues running in the background.

## Environment

```powershell
$env:GSTACK_PORT = "9222"          # CDP port (default: 9222)
$env:GSTACK_SKILL_TOKEN = "..."    # Auth token (set by browse daemon at startup)
```

## Browse binary

```
D:\Downloads\gstack-main\browse\dist\browse.exe
```

## Core patterns

### Navigate
```
browse goto https://example.com
browse back
browse forward
browse reload
```

### Click and fill
```
browse click "button[type=submit]"
browse click "#login-btn"
browse fill "#email" "user@example.com"
browse fill "#password" "secret"
```

### Keyboard
```
browse press "Enter"
browse type "search text"
```

### Read content
```
browse text              # full page text
browse text "h1"         # selector
browse html ".main"      # raw HTML
browse links             # all links
browse forms             # form structure
```

### Wait
```
browse wait ".loaded"
browse wait --networkidle
browse wait --load
```

### Inspect
```
browse js "document.title"
browse cookies
browse console
browse network
browse accessibility
```

## Session persistence

Chromium keeps the same session across commands (cookies, localStorage, auth state). To reset:
```powershell
# Kill Chromium and clear profile
Stop-Process -Name "chrome" -ErrorAction SilentlyContinue
Remove-Item "$env:TEMP\gstack-cdp-profile" -Recurse -Force -ErrorAction SilentlyContinue
```

## CAPTCHA handoff

If a page presents a CAPTCHA, browse will report it and pause. Complete the CAPTCHA manually in a visible browser window, then resume the session.

## Windows notes

- `chrome-cdp.ps1` locates the newest playwright-managed Chromium automatically.
- If multiple Chromium versions are installed, the most recently written one is used.
- CDP port 9222 is the default; set `$env:GSTACK_PORT` to change it.
