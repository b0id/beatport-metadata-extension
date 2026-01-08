# BeatportDJ Metadata Tracker

**Version 1.0** - Functional baseline  
Extracts track metadata from BeatportDJ web app and outputs to text file for streaming software integration.

## What It Does

Monitors the BeatportDJ web player at `https://dj.beatport.com`, detects when you load tracks on either deck, and writes the artist and track name to a text file that butt (broadcast using this tool) can read for Icecast stream metadata.

## Current Setup

### Components

1. **Chrome Extension** (`/mnt/aux/beatport-metadata-extension/`)
   - `manifest.json` - Chrome extension configuration
   - `tracker.js` - DOM monitoring script that watches for track changes
   - Detects track loads on Deck A (#song1/#tag1) and Deck B (#song2/#tag2)
   - Sends updates via HTTP POST to local server

2. **Node.js Server** (`/mnt/aux/beatport-metadata-extension/`)
   - `server.js` - Express server listening on port 3000
   - `package.json` - Node dependencies (express, cors)
   - Receives track updates and writes to `/home/b0id/beatport-nowplaying.txt`

3. **Output File**
   - Location: `/home/b0id/beatport-nowplaying.txt`
   - Format: Single line, overwritten on each track change
   - Example: `Artist Name, Another Artist - Track Title - Mix Version`

### How It Works

1. Extension monitors BeatportDJ DOM for changes to deck elements
2. When either deck loads a new track, extracts:
   - Artist names from `.tag_artist_link` elements in `#tag1` or `#tag2`
   - Track title from `.song_link1` or `.song_link2` in `#song1` or `#song2`
3. Combines as `Artist(s) - Track Title`
4. POSTs to `http://localhost:3000/update`
5. Server writes to text file
6. butt reads file and updates Icecast stream metadata

### Current Behavior

- **Most Recently Loaded Track**: Whichever deck you most recently loaded a track on becomes the active metadata
- **Single Line Output**: File contains only the current track (no history)
- **3-Second Polling**: Backup check every 3 seconds in case MutationObserver misses changes

## Usage

### Daily Streaming Workflow

1. **Start the metadata server:**
   ```bash
   cd /mnt/aux/beatport-metadata-extension
   node server.js
   ```
   Server will show: `Metadata server running on http://localhost:3000`

2. **Open BeatportDJ in Chrome:**
   - Navigate to `https://dj.beatport.com`
   - Extension auto-loads (you'll see "BeatportDJ Metadata Tracker loaded" in console)

3. **Configure butt:**
   - Settings → Stream tab
   - Update song name from: **file**
   - File path: `/home/b0id/beatport-nowplaying.txt`

4. **Start streaming and DJ!**
   - Load tracks on either deck
   - Metadata updates automatically
   - Check console (F12) to see "Deck A changed:" or "Deck B changed:" messages

### Debugging

**Check if extension is loaded:**
```bash
# In Chrome, go to chrome://extensions
# Look for "BeatportDJ Metadata Tracker" - should be enabled
```

**Check server is running:**
```bash
curl -X POST http://localhost:3000/update \
  -H "Content-Type: application/json" \
  -d '{"track":"Test Artist - Test Track"}'

cat ~/beatport-nowplaying.txt
# Should show: Test Artist - Test Track
```

**Watch file updates in real-time:**
```bash
watch -n 1 cat ~/beatport-nowplaying.txt
```

**Check browser console:**
- Press F12 on dj.beatport.com
- Console tab should show:
  - "BeatportDJ Metadata Tracker loaded"
  - "Player found, starting observer"
  - "Deck A changed: Artist - Track" (when you load tracks)

## Installation from Scratch

### Prerequisites
```bash
# Install Node.js and npm (Arch/EndeavourOS)
sudo pacman -S nodejs npm

# Or update package database if mirrors are stale
sudo pacman -Syy
sudo pacman -S nodejs npm
```

### Setup

1. **Create project directory:**
   ```bash
   mkdir -p /mnt/aux/beatport-metadata-extension
   cd /mnt/aux/beatport-metadata-extension
   ```

2. **Install dependencies:**
   ```bash
   npm init -y
   npm install express cors
   ```

3. **Create files:**
   - Copy `manifest.json`, `tracker.js`, and `server.js` to this directory
   - Update `OUTPUT_FILE` path in `server.js` if needed

4. **Load Chrome extension:**
   - Open Chrome → `chrome://extensions`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select `/mnt/aux/beatport-metadata-extension`

## Automatic Startup (Optional)

### Systemd Service

To auto-start the server on boot:

```bash
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/beatport-metadata.service
```

Paste:
```ini
[Unit]
Description=Beatport Metadata Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/mnt/aux/beatport-metadata-extension
ExecStart=/usr/bin/node /mnt/aux/beatport-metadata-extension/server.js
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Enable and start:
```bash
systemctl --user enable beatport-metadata.service
systemctl --user start beatport-metadata.service
systemctl --user status beatport-metadata.service
```

To stop:
```bash
systemctl --user stop beatport-metadata.service
```

## Future Enhancement Ideas

### Phase 2: Playlist History

**Goal:** Keep a running log of all tracks played during a set

**Implementation:**
- Append to file instead of overwriting
- Add timestamps
- Optional: Separate history file vs. current track file

**Changes needed:**
```javascript
// In server.js
const CURRENT_FILE = '/home/b0id/beatport-nowplaying.txt';
const HISTORY_FILE = '/home/b0id/beatport-history.log';

app.post('/update', (req, res) => {
  const { track } = req.body;
  if (track) {
    // Current track (overwrite)
    fs.writeFileSync(CURRENT_FILE, track + '\n');
    
    // History (append with timestamp)
    const timestamp = new Date().toISOString();
    fs.appendFileSync(HISTORY_FILE, `${timestamp} | ${track}\n`);
    
    console.log('Updated:', track);
  }
  res.send('OK');
});
```

### Phase 3: Enhanced Metadata

**Goal:** Include additional info like BPM, key, genre, label

**Currently available in DOM:**
- `.tag_genre_link` - Genre
- `.tag_label_link` - Record label
- BPM and key might be in other elements

**Changes needed:**
- Update `extractTrackInfo()` to grab additional elements
- Format output: `Artist - Title [Genre] (Label) 128 BPM / Key: 5A`
- Might need multiple output files or JSON format

### Phase 4: Crate Integration

**Goal:** Auto-add played tracks to a Beatport "Streamed Tracks" crate

**Research needed:**
- Does Beatport have an API for crate management?
- Can we use `window.DJAPPMM.goLink()` functions?
- Might need to reverse-engineer Beatport's internal API calls

**Potential approach:**
- Monitor network requests when manually adding to crate
- Replicate those API calls from extension
- Authenticate with Beatport session

### Phase 5: KADO Integration

**KADO:** AI music discovery tool for Beatport

**Integration ideas:**
- Send played tracks to KADO for recommendations
- Auto-queue KADO suggestions to deck
- Would need KADO API access or web scraping

### Phase 6: Advanced DJ Features

**Intelligent deck switching:**
- Monitor crossfader position
- Only update when crossfader > 50% to new deck
- Requires accessing mixer state from DOM

**Transition detection:**
- Show "Artist A → Artist B" during mixes
- Detect when both decks playing simultaneously
- Clear transition marker after crossfade complete

**Manual override:**
- Hotkey to manually select which deck shows
- Button in extension popup

### Phase 7: Analytics & Stats

**Post-session analysis:**
- Total tracks played
- Average BPM/energy
- Genre breakdown
- Most played artists/labels
- Set duration

**Export formats:**
- CSV for spreadsheet analysis
- JSON for web apps
- Markdown formatted setlist

### Phase 8: Social Integration

**Auto-posting:**
- Tweet "Now Playing: Artist - Track #djset"
- Update Discord bot
- Post to Instagram story
- Requires OAuth integrations

## Technical Architecture

### Data Flow
```
BeatportDJ Web App (DOM)
    ↓
Chrome Extension (tracker.js)
    ↓ [HTTP POST]
Node.js Server (server.js)
    ↓ [File Write]
beatport-nowplaying.txt
    ↓ [File Read]
butt (BUTT)
    ↓ [Metadata Update]
Icecast Server
    ↓ [Stream]
Listeners
```

### DOM Structure (as of v1.0)

```
#player
  #player1a (Deck A)
    #song1 (track title)
      .song_link1
    #tag1 (metadata)
      .tag_artist_link (multiple for collabs)
      .tag_genre_link
      .tag_label_link
      
  #player2a (Deck B)
    #song2 (track title)
      .song_link2
    #tag2 (metadata)
      .tag_artist_link
      .tag_genre_link
      .tag_label_link
```

### Extension Permissions

Current manifest requires:
- `activeTab` - Access active tab
- `https://dj.beatport.com/*` - Run on BeatportDJ only

Future additions might need:
- `storage` - For settings/history in extension
- `notifications` - For track change alerts
- Additional host permissions for API integrations

## Troubleshooting

### Server won't start
```bash
# Check if port 3000 is already in use
lsof -i :3000
# Kill existing process if needed
kill -9 <PID>
```

### Extension not detecting tracks
1. Check console for "BeatportDJ Metadata Tracker loaded"
2. Reload extension at `chrome://extensions`
3. Hard refresh BeatportDJ: Ctrl+Shift+R
4. Check if DOM structure changed (F12 → Elements → Inspect deck elements)

### File not updating
1. Verify server is running and showing "Updated: ..." messages
2. Check file permissions: `ls -la ~/beatport-nowplaying.txt`
3. Manually test: `curl -X POST http://localhost:3000/update -H "Content-Type: application/json" -d '{"track":"Test"}'`

### butt not showing updates
1. Verify file path is correct in butt settings
2. Check "Read from last line" option in butt
3. Try manually editing the file to confirm butt is monitoring it

## Version History

### v1.0 (Current)
- Initial release
- Basic track detection on both decks
- Single file output
- Most-recently-loaded-track priority
- Manual server start

### Planned
- v1.1: Playlist history logging
- v1.2: Additional metadata (BPM, key, genre)
- v2.0: Auto-start server, crate integration

## Dependencies

### Node.js Packages
- `express` (^5.2.1) - Web server framework
- `cors` (^2.8.5) - Cross-origin resource sharing

### System
- Node.js >= 18
- Chrome/Chromium (for extension)
- butt (for Icecast streaming)

## License

Personal project - use freely

## Credits

- Built for streaming DJ sets with BeatportDJ + Icecast
- Developed on EndeavourOS Linux
- Chrome Extension Manifest V3

---

**Last Updated:** December 2024  
**Maintainer:** b0id  
**Status:** ✅ Production Ready (v1.0)
