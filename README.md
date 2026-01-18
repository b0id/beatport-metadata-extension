# BeatportDJ Metadata Tracker

**Version 1.0** - Functional baseline  
Extracts track metadata from BeatportDJ web app and outputs to text file for streaming software integration.

## What It Does

Monitors the BeatportDJ web player at `https://dj.beatport.com`, detects when you load tracks on either deck, and:

1. **Streaming:** Writes full track metadata to a text file that butt (broadcast using this tool) can read for Icecast stream metadata
2. **Daily Logging:** Maintains daily log files with simplified track format (first artist + clean title) for scrobbling
3. **Scrobbling (Optional):** Python script validates tracks against MusicBrainz/Last.fm and scrobbles to ListenBrainz and Last.fm

**Important:** Logging only happens when you manually publish tracks via **Ctrl+Shift+U** or the "Update overlay" button. See [WORKFLOW.md](WORKFLOW.md) for detailed explanation.

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

3. **Output Files**

   **Streaming file (for butt):**
   - Location: `/home/b0id/beatport-nowplaying.txt`
   - Format: Single line, overwritten on each track change
   - Example: `Artist Name, Another Artist - Track Title - Mix Version`

   **Daily logs (for scrobbling):**
   - Location: `/mnt/aux/beatport-logs/YYYY-MM-DD.log`
   - Format: One line per track with timestamp and simplified metadata
   - Example: `2026-01-18T22:45:12.000Z | Artist Name - Track Title`
   - Simplified: First artist only, no mix version info

4. **Scrobbler (Optional)**
   - `scrobbler.py` - Python script for validation and scrobbling
   - Validates tracks against MusicBrainz and Last.fm APIs
   - Scrobbles to ListenBrainz and Last.fm
   - See `SCROBBLER_SETUP.md` for configuration

### How It Works

1. Extension monitors BeatportDJ DOM for changes to deck elements
2. When either deck loads a new track, extracts:
   - Artist names from `.tag_artist_link` elements in `#tag1` or `#tag2`
   - Track title from `.song_link1` or `.song_link2` in `#song1` or `#song2`
3. Combines as `Artist(s) - Track Title`
4. **Stores as "pending"** until you manually publish it
5. When you press **Ctrl+Shift+U** or click the **"Update overlay"** button:
   - POSTs to `http://localhost:3000/update`
   - Server writes to **BOTH** files simultaneously:
     - `/home/b0id/beatport-nowplaying.txt` (full format for butt)
     - `/mnt/aux/beatport-logs/YYYY-MM-DD.log` (simplified format for scrobbling)
6. butt reads the streaming file and updates Icecast stream metadata

**IMPORTANT:** Nothing is written to any file until you manually trigger the publish. Only tracks you intentionally publish (via Ctrl+Shift+U or the button) appear in your daily logs.

### Current Behavior

- **Manual Publishing**: Tracks are detected automatically but only sent to files when you trigger the update
- **Keyboard Shortcut**: Press **Ctrl+Shift+U** to publish the most recently loaded track
- **On-Screen Button**: Click the **"Update overlay"** button (bottom-right corner) to publish
- **Dual File Writing**: Each publish writes to both:
  - Streaming file: Full track metadata for butt
  - Daily log: Simplified metadata for scrobbling
- **Most Recently Loaded Track**: Whichever deck you most recently loaded a track on becomes the active metadata
- **Daily Log Persistence**: Each day gets a new log file, previous days preserved
- **3-Second Polling**: Backup check every 3 seconds in case MutationObserver misses changes
- **Deduplication**: Won't publish the same track twice in a row

**Key Point:** Your daily log only contains tracks you actively published during your set. If you load a track but don't press Ctrl+Shift+U, it won't appear in any logs.

## Usage

### Daily Streaming Workflow

1. **Start the metadata server:**
   ```bash
   cd /mnt/aux/beatport-metadata-extension
   node server.js
   ```
   Server will show: `Metadata server running on http://localhost:3000`

   **IMPORTANT:** The server must be running for the extension to write to the file!

2. **Open BeatportDJ in Chrome:**
   - Navigate to `https://dj.beatport.com`
   - Extension auto-loads (you'll see "BeatportDJ Metadata Tracker loaded" in console)

3. **Configure butt:**
   - Settings → Stream tab
   - Update song name from: **file**
   - File path: `/home/b0id/beatport-nowplaying.txt`

4. **Start streaming and DJ!**
   - Load tracks on either deck
   - Console will show "Deck A loaded (pending):" or "Deck B loaded (pending):" messages
   - **Press Ctrl+Shift+U** or **click "Update overlay"** button to publish the track
   - When you publish, the server writes to **BOTH files**:
     - Stream overlay file (for butt/OBS)
     - Daily log file (for scrobbling later)
   - Console will show:
     - Browser: "PUBLISH: Artist - Track"
     - Server: "Updated: Artist - Track" and "Logged: Artist - Track"
   - Repeat for each new track you want to announce

   **Tip:** Only publish tracks when you're actually playing them out. Tracks you preview or skip won't appear in your history unless you explicitly publish them.

5. **After your set (Optional scrobbling):**
   ```bash
   cd /mnt/aux/beatport-metadata-extension
   source venv/bin/activate
   python scrobbler.py
   ```
   - Validates and scrobbles all tracks from today's log
   - See `SCROBBLER_SETUP.md` for initial configuration

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
  - "Deck A loaded (pending): Artist - Track" (when you load tracks)
  - "PUBLISH: Artist - Track" (when you press Ctrl+Shift+U or click the button)

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

### Phase 2: ListenBrainz / Last.fm Scrobbling

**Goal:** Auto-scrobble tracks to ListenBrainz and/or Last.fm for listening history

**Complexity:** Medium - requires API integration and proper scrobble timing

**What's needed:**

1. **ListenBrainz** (Simpler option)
   - Get user token from https://listenbrainz.org/profile/
   - Install package: `npm install listenbrainz`
   - Modify `server.js` to POST to ListenBrainz API
   - API endpoint: `https://api.listenbrainz.org/1/submit-listens`
   - Required data: artist, track, timestamp
   - No complicated authentication - just user token

2. **Last.fm** (More complex)
   - Create API account at https://www.last.fm/api/account/create
   - Get API key and shared secret
   - Install package: `npm install lastfm` or use manual HTTP requests
   - Requires MD5 signature for authentication
   - Must follow scrobbling rules:
     - Track must play for at least 30 seconds OR half its duration
     - Scrobble timestamp should be when track started playing
   - API endpoint: `http://ws.audioscrobbler.com/2.0/`

3. **Implementation approach:**
   ```javascript
   // In server.js
   const ListenBrainz = require('listenbrainz');
   const lb = new ListenBrainz({ userToken: 'YOUR_TOKEN' });

   app.post('/update', async (req, res) => {
     const { track } = req.body;
     if (track) {
       // Write to file (existing functionality)
       fs.writeFileSync(OUTPUT_FILE, track + '\n');

       // Parse artist and title
       const [artist, title] = track.split(' - ');

       // Scrobble to ListenBrainz
       await lb.submitSingle({
         artist: artist,
         track: title,
         timestamp: Math.floor(Date.now() / 1000)
       });

       console.log('Updated and scrobbled:', track);
     }
     res.send('OK');
   });
   ```

4. **Considerations:**
   - Should you scrobble immediately on Ctrl+Shift+U, or wait 30 seconds?
   - Parse track string correctly (handle " - " in artist or track names)
   - Handle API failures gracefully (don't break file writing if scrobble fails)
   - Store API tokens securely (environment variables, not in code)
   - Optional: Add toggle to enable/disable scrobbling

**Verdict:** ListenBrainz is much simpler - straightforward REST API with just a user token. Last.fm adds complexity with signatures and session management. If you just want listening history, start with ListenBrainz.

### Phase 3: Playlist History

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

### Phase 4: Enhanced Metadata

**Goal:** Include additional info like BPM, key, genre, label

**Currently available in DOM:**
- `.tag_genre_link` - Genre
- `.tag_label_link` - Record label
- BPM and key might be in other elements

**Changes needed:**
- Update `extractTrackInfo()` to grab additional elements
- Format output: `Artist - Title [Genre] (Label) 128 BPM / Key: 5A`
- Might need multiple output files or JSON format

### Phase 5: Crate Integration

**Goal:** Auto-add played tracks to a Beatport "Streamed Tracks" crate

**Research needed:**
- Does Beatport have an API for crate management?
- Can we use `window.DJAPPMM.goLink()` functions?
- Might need to reverse-engineer Beatport's internal API calls

**Potential approach:**
- Monitor network requests when manually adding to crate
- Replicate those API calls from extension
- Authenticate with Beatport session

### Phase 6: KADO Integration

**KADO:** AI music discovery tool for Beatport

**Integration ideas:**
- Send played tracks to KADO for recommendations
- Auto-queue KADO suggestions to deck
- Would need KADO API access or web scraping

### Phase 7: Advanced DJ Features

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

### Phase 8: Analytics & Stats

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

### Phase 9: Social Integration

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
    ↓ [Detects tracks, stores as "pending"]
    ↓ [User presses Ctrl+Shift+U]
    ↓ [HTTP POST to localhost:3000/update]
Node.js Server (server.js)
    ├─ [File Write] → /home/b0id/beatport-nowplaying.txt (full format)
    │                 └─ butt reads → Icecast → Listeners
    │
    └─ [File Write] → /mnt/aux/beatport-logs/YYYY-MM-DD.log (simplified)
                      └─ scrobbler.py reads → validates → scrobbles
                         ├─ ListenBrainz API
                         └─ Last.fm API
```

### Server Implementation Details

**server.js** handles each publish request:

1. **Receives POST** from extension with full track string
   - Example: `"Sidney Charles, Another Artist - Hyper Rave - Original Mix"`

2. **Writes full format** to streaming file
   - File: `/home/b0id/beatport-nowplaying.txt`
   - Format: `"Sidney Charles, Another Artist - Hyper Rave - Original Mix\n"`
   - Purpose: Stream overlay metadata

3. **Parses and simplifies** track string
   - Splits on `" - "` to get parts
   - Takes first artist: `"Sidney Charles, Another Artist"` → `"Sidney Charles"`
   - Takes track title: `"Hyper Rave"` (ignoring `"Original Mix"`)
   - Result: `"Sidney Charles - Hyper Rave"`

4. **Appends to daily log** with timestamp
   - File: `/mnt/aux/beatport-logs/2026-01-18.log`
   - Format: `"2026-01-18T22:45:12.000Z | Sidney Charles - Hyper Rave\n"`
   - Purpose: Scrobbling history

5. **Returns success** to extension

**Key Implementation Points:**
- Single POST request writes to both files atomically
- Daily log file created automatically if it doesn't exist
- Simplified format reduces scrobbling errors (fewer collaboration artists, no mix versions)
- Timestamps use ISO 8601 format for universal compatibility

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
1. **FIRST: Check if server is running!**
   ```bash
   ps aux | grep "node server.js" | grep -v grep
   # or check if port 3000 is in use:
   lsof -i :3000
   ```
   If not running, start it: `node server.js`

2. Verify you're actually triggering the publish (Ctrl+Shift+U or clicking button)
3. Check server console for "Updated: ..." messages
4. Check file permissions: `ls -la ~/beatport-nowplaying.txt`
5. Manually test: `curl -X POST http://localhost:3000/update -H "Content-Type: application/json" -d '{"track":"Test"}'`

### butt not showing updates
1. Verify file path is correct in butt settings
2. Check "Read from last line" option in butt
3. Try manually editing the file to confirm butt is monitoring it

## Version History

### v1.1 (Current)
- ✅ Daily history logging with simplified track format
- ✅ Python scrobbler with MusicBrainz/Last.fm validation
- ✅ Scrobbling to ListenBrainz and Last.fm
- ✅ Manual scrobbling workflow (run after DJ set)
- ✅ Track parsing (first artist + clean title)

### v1.0
- Initial release
- Basic track detection on both decks
- Manual publish workflow (Ctrl+Shift+U or "Update overlay" button)
- Pending track system - detects automatically, publishes on demand
- Single file output
- Most-recently-loaded-track priority
- Manual server start

### Planned
- v1.2: Additional metadata (BPM, key, genre) in logs
- v1.3: Automatic scrobbling option with confidence threshold
- v2.0: Auto-start server, crate integration

## Dependencies

### Node.js Packages
- `express` (^5.2.1) - Web server framework
- `cors` (^2.8.5) - Cross-origin resource sharing

### Python Packages (Optional, for scrobbling)
- `pylast` - Last.fm scrobbling
- `musicbrainzngs` - MusicBrainz metadata validation
- `requests` - HTTP requests for ListenBrainz
- `python-Levenshtein` - Fuzzy string matching

Install with: `pip install -r requirements.txt` (in venv)

### System
- Node.js >= 18
- Chrome/Chromium (for extension)
- butt (for Icecast streaming)
- Python 3.10+ (optional, for scrobbling)

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
