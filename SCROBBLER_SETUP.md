# Scrobbler Setup Guide

## Overview

The scrobbler script validates your track metadata against MusicBrainz and Last.fm, then scrobbles to both ListenBrainz and Last.fm.

**IMPORTANT:** Tracks only appear in your daily log when you manually publish them during your DJ set using **Ctrl+Shift+U** or the "Update overlay" button. The scrobbler processes your intentionally published tracks, not every track you load in BeatportDJ.

## Prerequisites

### 1. Python Dependencies

Install Python packages in virtual environment:

```bash
cd /mnt/aux/beatport-metadata-extension
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. ListenBrainz Token

1. Go to https://listenbrainz.org/
2. Create account or log in
3. Go to https://listenbrainz.org/profile/
4. Scroll down to "User Token"
5. Copy your user token

### 3. Last.fm API Credentials

**Get API Key and Secret:**

1. Go to https://www.last.fm/api/account/create
2. Fill in application details:
   - Application name: "Beatport Scrobbler"
   - Description: "Personal DJ set scrobbler"
3. Submit and copy your API key and shared secret

**Get Password Hash:**

Last.fm requires a password hash (MD5 of your password). Generate it:

```bash
echo -n "your_lastfm_password" | md5sum
```

**Important:** Never commit your actual password to git!

## Configuration

### Create Config File

Copy the template and fill in your credentials:

```bash
cd /mnt/aux/beatport-metadata-extension
cp scrobbler-config.json.template scrobbler-config.json
nano scrobbler-config.json
```

Edit `scrobbler-config.json`:

```json
{
  "listenbrainz_token": "YOUR_LISTENBRAINZ_TOKEN_HERE",
  "lastfm_api_key": "YOUR_LASTFM_API_KEY_HERE",
  "lastfm_api_secret": "YOUR_LASTFM_SHARED_SECRET_HERE",
  "lastfm_username": "your_lastfm_username",
  "lastfm_password_hash": "YOUR_MD5_PASSWORD_HASH_HERE"
}
```

**Security Note:** The config file is in `.gitignore` and won't be committed to git.

## How Daily Logs Are Created

Understanding the workflow:

1. **During Your Set:**
   - You load a track on Deck A or B
   - Extension detects it and stores as "pending"
   - **Nothing is logged yet**

2. **When You Publish (Ctrl+Shift+U or button click):**
   - Track is sent to server
   - Server writes to `/home/b0id/beatport-nowplaying.txt` (full format)
   - Server **also** writes to `/mnt/aux/beatport-logs/2026-01-18.log` (simplified format)
   - **This is when the track enters your history**

3. **After Your Set:**
   - Your daily log contains only the tracks you published
   - Run scrobbler to validate and scrobble them to ListenBrainz/Last.fm

**Example:** If you load 50 tracks but only publish 20 (the ones you actually played out), your daily log will contain exactly 20 entries - the tracks you broadcasted to your stream.

## Usage

### Basic Usage

After a DJ set, scrobble today's tracks:

```bash
cd /mnt/aux/beatport-metadata-extension
source venv/bin/activate
python scrobbler.py
```

### Scrobble Specific Date

```bash
python scrobbler.py 2026-01-18
```

### What It Does

For each track in your daily log:

1. **Validation:**
   - Queries MusicBrainz API for matches
   - Queries Last.fm API for matches
   - Uses fuzzy matching to find best match
   - Shows confidence score (0-100%)

2. **Scrobbling:**
   - If confidence ≥ 80%: Uses validated metadata
   - If confidence < 80%: Uses original cleaned metadata
   - Scrobbles to ListenBrainz with timestamp
   - Scrobbles to Last.fm with timestamp

3. **Output:**
   - Shows validation results for each track
   - Shows scrobble success/failure
   - Provides summary at end

### Example Output

```
Beatport Scrobbler
============================================================
Date: 2026-01-18
Log file: /mnt/aux/beatport-logs/2026-01-18.log

Found 3 tracks in log

✓ Last.fm authenticated

[1/3] Processing: Sidney Charles - Hyper Rave

  Validating: Sidney Charles - Hyper Rave
  ✓ Matched (92%): Sidney Charles - Hyper Rave [MusicBrainz]
  ✓ Scrobbled to ListenBrainz
  ✓ Scrobbled to Last.fm

[2/3] Processing: Charlotte de Witte - Sgadi Li Mi

  Validating: Charlotte de Witte - Sgadi Li Mi
  ✓ Matched (95%): Charlotte de Witte - Sgadi Li Mi [Last.fm]
  ✓ Scrobbled to ListenBrainz
  ✓ Scrobbled to Last.fm

[3/3] Processing: Amelie Lens - In My Mind

  Validating: Amelie Lens - In My Mind
  ~ Low confidence (68%): Amelie Lens - In My Mind (Club Mix)
    Using original instead
  ✓ Scrobbled to ListenBrainz
  ✓ Scrobbled to Last.fm

============================================================
Summary:
  Total tracks: 3
  High confidence matches (≥80%): 2
  Low confidence matches (<80%): 1
  ListenBrainz scrobbles: 3/3
  Last.fm scrobbles: 3/3
============================================================
```

## Rate Limits

The script respects API rate limits:

- **MusicBrainz:** 1 request per second (automatic delay)
- **Last.fm:** Generous limits, no special handling needed
- **ListenBrainz:** No strict limits

For a 2-hour set (~30 tracks), the script takes about 30-60 seconds to complete.

## Troubleshooting

### "Config file not found"

Create `scrobbler-config.json` from the template (see Configuration above).

### "ListenBrainz error: 401"

Invalid ListenBrainz token. Get a new one from your profile page.

### "Last.fm authentication failed"

- Check your API key and shared secret
- Verify your username is correct
- Regenerate password hash: `echo -n "password" | md5sum`

### "No matches found"

Some tracks (especially white labels, unreleased, or very new tracks) may not be in MusicBrainz or Last.fm databases. The script will use your cleaned metadata instead.

### Low confidence matches

If many tracks show low confidence, it might mean:

- Artist name format differs (e.g., "Artist A & Artist B" vs "Artist A, Artist B")
- Track is from a compilation or remix album
- Track is very new and not yet in databases

**Solution:** Use Bijou.fm for manual scrobbling of problem tracks.

## Integration with Bijou.fm

For tracks that fail validation or if you prefer manual review:

1. After your set, check the daily log: `/mnt/aux/beatport-logs/2026-01-18.log`
2. Copy track list
3. Use Bijou.fm (https://bijou.fm/) to manually scrobble
4. Bijou.fm gives you full control over artist/title/timestamp

## Daily Workflow

### Option 1: Auto-scrobble everything

After your DJ set:

```bash
cd /mnt/aux/beatport-metadata-extension
source venv/bin/activate
python scrobbler.py
```

Review the output, check ListenBrainz/Last.fm profiles.

### Option 2: Review before scrobbling

1. Check daily log for accuracy: `cat /mnt/aux/beatport-logs/$(date +%Y-%m-%d).log`
2. Manually fix any issues in the log file if needed
3. Run scrobbler: `python scrobbler.py`

### Option 3: Manual scrobbling only

Skip the scrobbler entirely and use Bijou.fm with your daily log files.

## Files Created

- `/mnt/aux/beatport-logs/YYYY-MM-DD.log` - Daily track history
- `scrobbler-config.json` - Your API credentials (not in git)
- `venv/` - Python virtual environment (not in git)

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DURING YOUR DJ SET                        │
└─────────────────────────────────────────────────────────────┘

  Load Track → Pending     ┌──────────────────────┐
  (Auto-detect)            │   Nothing logged     │
                           │   Nothing written    │
                           └──────────────────────┘

  Press Ctrl+Shift+U       ┌──────────────────────┐
  or Click Button    ───→  │  Write to BOTH:      │
                           │  1. Stream file      │
                           │  2. Daily log        │
                           └──────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     AFTER YOUR SET                           │
└─────────────────────────────────────────────────────────────┘

  Daily Log File           ┌──────────────────────┐
  /mnt/aux/beatport-logs/  │  Contains only the   │
  2026-01-18.log     ───→  │  tracks you published│
                           └──────────────────────┘

  Run Scrobbler            ┌──────────────────────┐
  python scrobbler.py ───→ │  1. Validate tracks  │
                           │  2. Scrobble to LB   │
                           │  3. Scrobble to LFM  │
                           └──────────────────────┘
```

## Uninstalling

To remove scrobbling functionality but keep logging:

```bash
cd /mnt/aux/beatport-metadata-extension
rm -rf venv/
rm scrobbler.py
rm scrobbler-config.json
rm requirements.txt
```

Daily logs will still be created, and you can use them with Bijou.fm.
