# Beatport Metadata Tracker - Complete Workflow

## Quick Answer: When Are Tracks Logged?

**Tracks are logged ONLY when you manually publish them using Ctrl+Shift+U or the "Update overlay" button.**

- ✅ Pressing Ctrl+Shift+U → Track is logged
- ✅ Clicking "Update overlay" button → Track is logged
- ❌ Just loading a track on deck → NOT logged
- ❌ Previewing a track → NOT logged
- ❌ Track sitting in deck unplayed → NOT logged

## Complete Workflow

### 1. Extension Detection (Automatic)

```
┌─────────────────────────────────────┐
│ You load track on Deck A or Deck B │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Extension detects track metadata    │
│ - Artist(s): "Sidney Charles"       │
│ - Title: "Hyper Rave - Original Mix"│
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Stored as "PENDING"                 │
│ Console: "Deck A loaded (pending)"  │
│                                     │
│ ⚠️  NOT LOGGED YET                  │
│ ⚠️  NOT WRITTEN TO ANY FILE         │
└─────────────────────────────────────┘
```

### 2. Manual Publication (You Control This)

```
┌─────────────────────────────────────┐
│ You press Ctrl+Shift+U              │
│       OR                            │
│ Click "Update overlay" button       │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ Browser extension calls postTrack() │
│ Console: "PUBLISH: Artist - Track"  │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ HTTP POST to localhost:3000/update  │
│ Body: {"track": "Artist - Track"}   │
└─────────────────────────────────────┘
```

### 3. Server Processing (Automatic)

```
┌─────────────────────────────────────────────────────┐
│ Node.js server receives POST request                │
└─────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌──────────────────┐           ┌───────────────────┐
│ Write File #1    │           │ Write File #2     │
│ (Full Format)    │           │ (Simplified)      │
└──────────────────┘           └───────────────────┘
        ↓                               ↓
┌──────────────────┐           ┌───────────────────┐
│ /home/b0id/      │           │ /mnt/aux/         │
│ beatport-        │           │ beatport-logs/    │
│ nowplaying.txt   │           │ 2026-01-18.log    │
│                  │           │                   │
│ Content:         │           │ Content:          │
│ Sidney Charles,  │           │ 2026-01-18T...Z | │
│ Another Artist - │           │ Sidney Charles -  │
│ Hyper Rave -     │           │ Hyper Rave        │
│ Original Mix     │           │                   │
└──────────────────┘           └───────────────────┘
        ↓                               ↓
┌──────────────────┐           ┌───────────────────┐
│ Used by:         │           │ Used by:          │
│ - butt           │           │ - scrobbler.py    │
│ - OBS            │           │ - Manual review   │
│ - Stream overlay │           │ - Bijou.fm        │
└──────────────────┘           └───────────────────┘
```

### 4. Console Output

When you publish a track, you'll see:

**Browser Console (F12 on dj.beatport.com):**
```
PUBLISH: Sidney Charles, Another Artist - Hyper Rave - Original Mix
```

**Server Console (terminal running node server.js):**
```
Updated: Sidney Charles, Another Artist - Hyper Rave - Original Mix
Logged: Sidney Charles - Hyper Rave
```

## Example Scenarios

### Scenario 1: Normal DJ Set

```
Action                              | Logged? | In Daily Log?
------------------------------------|---------|---------------
Load track on Deck A                | NO      | NO
Press Ctrl+Shift+U                  | YES ✅  | YES ✅
Load another track on Deck B        | NO      | NO
Load third track on Deck A          | NO      | NO
Press Ctrl+Shift+U                  | YES ✅  | YES ✅
```

**Result:** Daily log has 2 entries (the tracks you published)

### Scenario 2: Previewing Tracks

```
Action                              | Logged? | In Daily Log?
------------------------------------|---------|---------------
Load track 1 (preview it)           | NO      | NO
Load track 2 (preview it)           | NO      | NO
Load track 3 (preview it)           | NO      | NO
Load track 4 (play it out)          | NO      | NO
Press Ctrl+Shift+U for track 4      | YES ✅  | YES ✅
```

**Result:** Daily log has 1 entry (only the track you played and published)

### Scenario 3: Two Deck Mixing

```
Action                              | Logged? | In Daily Log?
------------------------------------|---------|---------------
Load track A on Deck A              | NO      | NO
Press Ctrl+Shift+U (publish A)      | YES ✅  | YES ✅
Load track B on Deck B              | NO      | NO
Mix both playing                    | NO      | NO
Press Ctrl+Shift+U (publish B)      | YES ✅  | YES ✅
```

**Result:** Daily log has 2 entries (both tracks you explicitly published)

## Why This Design?

### Benefits of Manual Publishing:

1. **Intentional Scrobbling**
   - Only tracks you actually played get scrobbled
   - No accidental scrobbles from tracks you just previewed

2. **Clean History**
   - Your listening history reflects what you broadcasted
   - Easy to review: every log entry is a track you played

3. **Flexibility**
   - Preview dozens of tracks without polluting your history
   - Decide exactly when to update your stream overlay

4. **Matches DJ Workflow**
   - You're already manually cueing and mixing
   - One hotkey press per track feels natural

5. **Prevents Errors**
   - Won't scrobble a track you loaded by mistake
   - Won't scrobble duplicate entries if you reload a track

## Files Created Per Session

After a 2-hour set where you publish 25 tracks:

```
/mnt/aux/beatport-logs/2026-01-18.log
├─ 25 lines (one per published track)
├─ Format: ISO timestamp | Artist - Title
└─ File size: ~2-3 KB

/home/b0id/beatport-nowplaying.txt
├─ 1 line (most recent track)
├─ Format: Full artist(s) - Title - Mix
└─ Overwritten each time
```

## Implementation Code Reference

### Extension Side (tracker.js)

```javascript
// Hotkey listener
window.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.shiftKey && e.code === 'KeyU') {
    e.preventDefault();
    publishPending();  // ← This triggers the POST
  }
});

function publishPending() {
  const track = /* get pending track */;
  postTrack(track);  // ← Sends to server
}

function postTrack(track) {
  if (!track || track === lastPublished) return;  // Dedup

  fetch('http://localhost:3000/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ track })  // ← Sent here
  });
}
```

### Server Side (server.js)

```javascript
app.post('/update', (req, res) => {
  const { track } = req.body;  // ← Received here

  if (track) {
    // Write #1: Stream file (full format)
    fs.writeFileSync(OUTPUT_FILE, track + '\n');

    // Write #2: Daily log (simplified format)
    const cleanTrack = parseTrack(track);  // Simplify
    const timestamp = new Date().toISOString();
    const logEntry = `${timestamp} | ${cleanTrack}\n`;
    const logFile = getTodayLogFile();  // YYYY-MM-DD.log
    fs.appendFileSync(logFile, logEntry);

    console.log('Updated:', track);
    console.log('Logged:', cleanTrack);
  }

  res.send('OK');
});
```

## Troubleshooting

### "My tracks aren't appearing in the log"

**Check:**
1. Are you pressing Ctrl+Shift+U after loading each track?
2. Is the server running? (`ps aux | grep "node server.js"`)
3. Check browser console for "PUBLISH:" messages
4. Check server console for "Logged:" messages

### "I have too many entries in my log"

**Possible causes:**
- Accidentally pressing Ctrl+Shift+U multiple times
- Publishing preview tracks you didn't mean to

**Solution:**
- Only press Ctrl+Shift+U when you're actually playing a track out
- You can edit the log file manually before scrobbling

### "I want automatic logging"

That would require modifying `tracker.js` to auto-publish, but you'd lose:
- Control over what gets logged
- Ability to preview without logging
- Clean separation between "loaded" and "played"

Not recommended for DJ use case.

## Summary

**The system gives you complete control:**

- ✅ Load as many tracks as you want
- ✅ Preview, cue, and test without logging
- ✅ Explicitly publish only what you actually play
- ✅ Daily logs contain your true DJ set history
- ✅ Scrobbler processes your intentional selections

**One hotkey press (Ctrl+Shift+U) does everything:**
1. Updates stream overlay
2. Logs to daily file
3. Prevents duplicates
4. Creates scrobbling history

That's why the manual trigger design is perfect for this use case.
