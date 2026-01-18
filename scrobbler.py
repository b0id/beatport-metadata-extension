#!/usr/bin/env python3
"""
Beatport Scrobbler - Validate and scrobble tracks to ListenBrainz and Last.fm

Usage:
    python scrobbler.py [YYYY-MM-DD]

If no date provided, uses today's date.

Requirements:
    pip install pylast musicbrainzngs requests python-Levenshtein
"""

import sys
import os
import json
import time
from datetime import datetime, date
from pathlib import Path
import requests
import musicbrainzngs
import pylast

# Configuration
LOGS_DIR = Path('/mnt/aux/beatport-logs')
CONFIG_FILE = Path(__file__).parent / 'scrobbler-config.json'

# Set up MusicBrainz
musicbrainzngs.set_useragent('BeatportScrobbler', '1.0', 'beatport@scrobbler.local')

class ScrobblerConfig:
    """Load and validate configuration"""
    def __init__(self, config_path):
        if not config_path.exists():
            print(f"ERROR: Config file not found: {config_path}")
            print("Create scrobbler-config.json with your API credentials.")
            sys.exit(1)

        with open(config_path) as f:
            self.config = json.load(f)

        # Validate required fields
        self.listenbrainz_token = self.config.get('listenbrainz_token')
        self.lastfm_api_key = self.config.get('lastfm_api_key')
        self.lastfm_api_secret = self.config.get('lastfm_api_secret')
        self.lastfm_username = self.config.get('lastfm_username')
        self.lastfm_password_hash = self.config.get('lastfm_password_hash')

        if not self.listenbrainz_token:
            print("WARNING: No ListenBrainz token configured")
        if not all([self.lastfm_api_key, self.lastfm_api_secret,
                   self.lastfm_username, self.lastfm_password_hash]):
            print("WARNING: Last.fm credentials incomplete")

class TrackValidator:
    """Validate tracks against MusicBrainz and Last.fm APIs"""

    def __init__(self):
        pass

    def query_musicbrainz(self, artist, title):
        """Query MusicBrainz for track information"""
        try:
            # Add delay to respect rate limit (1 req/sec)
            time.sleep(1.1)

            result = musicbrainzngs.search_recordings(
                artist=artist,
                recording=title,
                limit=5
            )

            if result['recording-list']:
                matches = []
                for recording in result['recording-list']:
                    score = int(recording.get('ext:score', 0))
                    rec_title = recording.get('title', '')
                    rec_artist = recording.get('artist-credit-phrase', '')

                    matches.append({
                        'artist': rec_artist,
                        'title': rec_title,
                        'score': score,
                        'source': 'MusicBrainz'
                    })

                return matches

        except Exception as e:
            print(f"  MusicBrainz error: {e}")

        return []

    def query_lastfm(self, network, artist, title):
        """Query Last.fm for track information"""
        try:
            # Search for track
            results = network.search_for_track(artist, title)

            matches = []
            for track in results.get_next_page()[:5]:
                matches.append({
                    'artist': str(track.artist),
                    'title': str(track.title),
                    'score': 85,  # Last.fm doesn't provide scores
                    'source': 'Last.fm'
                })

            return matches

        except Exception as e:
            print(f"  Last.fm error: {e}")

        return []

    def fuzzy_match_score(self, str1, str2):
        """Calculate similarity between two strings (0-100)"""
        try:
            from Levenshtein import ratio
            return int(ratio(str1.lower(), str2.lower()) * 100)
        except ImportError:
            # Fallback: simple equality check
            return 100 if str1.lower() == str2.lower() else 0

    def validate_track(self, artist, title, lastfm_network):
        """
        Validate track against MusicBrainz and Last.fm
        Returns: (validated_artist, validated_title, confidence)
        """
        print(f"\n  Validating: {artist} - {title}")

        # Query both APIs
        mb_matches = self.query_musicbrainz(artist, title)
        lfm_matches = self.query_lastfm(lastfm_network, artist, title)

        all_matches = mb_matches + lfm_matches

        if not all_matches:
            print(f"  No matches found, using original")
            return (artist, title, 50)

        # Find best match
        best_match = None
        best_score = 0

        for match in all_matches:
            # Calculate fuzzy match score
            artist_score = self.fuzzy_match_score(artist, match['artist'])
            title_score = self.fuzzy_match_score(title, match['title'])
            combined_score = (artist_score + title_score) / 2

            if combined_score > best_score:
                best_score = combined_score
                best_match = match

        if best_match and best_score >= 80:
            print(f"  ✓ Matched ({best_score}%): {best_match['artist']} - {best_match['title']} [{best_match['source']}]")
            return (best_match['artist'], best_match['title'], best_score)
        elif best_match:
            print(f"  ~ Low confidence ({best_score}%): {best_match['artist']} - {best_match['title']}")
            print(f"    Using original instead")
            return (artist, title, best_score)
        else:
            print(f"  No good matches, using original")
            return (artist, title, 50)

class Scrobbler:
    """Handle scrobbling to ListenBrainz and Last.fm"""

    def __init__(self, config):
        self.config = config
        self.listenbrainz_url = 'https://api.listenbrainz.org/1/submit-listens'

        # Set up Last.fm
        self.lastfm_network = None
        if config.lastfm_api_key and config.lastfm_api_secret:
            try:
                self.lastfm_network = pylast.LastFMNetwork(
                    api_key=config.lastfm_api_key,
                    api_secret=config.lastfm_api_secret,
                    username=config.lastfm_username,
                    password_hash=config.lastfm_password_hash
                )
                print("✓ Last.fm authenticated")
            except Exception as e:
                print(f"✗ Last.fm authentication failed: {e}")

    def scrobble_to_listenbrainz(self, artist, title, timestamp):
        """Scrobble track to ListenBrainz"""
        if not self.config.listenbrainz_token:
            return False

        try:
            payload = {
                'listen_type': 'single',
                'payload': [{
                    'listened_at': int(timestamp),
                    'track_metadata': {
                        'artist_name': artist,
                        'track_name': title
                    }
                }]
            }

            headers = {
                'Authorization': f'Token {self.config.listenbrainz_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                self.listenbrainz_url,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return True
            else:
                print(f"  ListenBrainz error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"  ListenBrainz error: {e}")
            return False

    def scrobble_to_lastfm(self, artist, title, timestamp):
        """Scrobble track to Last.fm"""
        if not self.lastfm_network:
            return False

        try:
            self.lastfm_network.scrobble(
                artist=artist,
                title=title,
                timestamp=int(timestamp)
            )
            return True

        except Exception as e:
            print(f"  Last.fm error: {e}")
            return False

def parse_log_file(log_path):
    """Parse daily log file and extract tracks with timestamps"""
    tracks = []

    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or ' | ' not in line:
                continue

            try:
                timestamp_str, track = line.split(' | ', 1)
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

                if ' - ' in track:
                    artist, title = track.split(' - ', 1)
                    tracks.append({
                        'artist': artist.strip(),
                        'title': title.strip(),
                        'timestamp': int(timestamp.timestamp())
                    })

            except Exception as e:
                print(f"Warning: Could not parse line: {line} ({e})")
                continue

    return tracks

def main():
    # Parse arguments
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
        try:
            log_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"ERROR: Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        log_date = date.today()

    log_file = LOGS_DIR / f'{log_date}.log'

    print(f"Beatport Scrobbler")
    print(f"=" * 60)
    print(f"Date: {log_date}")
    print(f"Log file: {log_file}")
    print()

    # Check log file exists
    if not log_file.exists():
        print(f"ERROR: Log file not found: {log_file}")
        sys.exit(1)

    # Load configuration
    config = ScrobblerConfig(CONFIG_FILE)

    # Parse log file
    tracks = parse_log_file(log_file)
    print(f"Found {len(tracks)} tracks in log\n")

    if not tracks:
        print("No tracks to scrobble")
        sys.exit(0)

    # Initialize services
    validator = TrackValidator()
    scrobbler = Scrobbler(config)

    # Process each track
    stats = {
        'total': len(tracks),
        'listenbrainz_success': 0,
        'lastfm_success': 0,
        'validation_high': 0,
        'validation_low': 0
    }

    for i, track in enumerate(tracks, 1):
        print(f"\n[{i}/{len(tracks)}] Processing: {track['artist']} - {track['title']}")

        # Validate track
        validated_artist, validated_title, confidence = validator.validate_track(
            track['artist'],
            track['title'],
            scrobbler.lastfm_network
        )

        if confidence >= 80:
            stats['validation_high'] += 1
        else:
            stats['validation_low'] += 1

        # Scrobble to ListenBrainz
        if config.listenbrainz_token:
            if scrobbler.scrobble_to_listenbrainz(
                validated_artist,
                validated_title,
                track['timestamp']
            ):
                print(f"  ✓ Scrobbled to ListenBrainz")
                stats['listenbrainz_success'] += 1
            else:
                print(f"  ✗ Failed to scrobble to ListenBrainz")

        # Scrobble to Last.fm
        if scrobbler.lastfm_network:
            if scrobbler.scrobble_to_lastfm(
                validated_artist,
                validated_title,
                track['timestamp']
            ):
                print(f"  ✓ Scrobbled to Last.fm")
                stats['lastfm_success'] += 1
            else:
                print(f"  ✗ Failed to scrobble to Last.fm")

        # Add delay between tracks to avoid rate limits
        if i < len(tracks):
            time.sleep(0.5)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Total tracks: {stats['total']}")
    print(f"  High confidence matches (≥80%): {stats['validation_high']}")
    print(f"  Low confidence matches (<80%): {stats['validation_low']}")
    if config.listenbrainz_token:
        print(f"  ListenBrainz scrobbles: {stats['listenbrainz_success']}/{stats['total']}")
    if scrobbler.lastfm_network:
        print(f"  Last.fm scrobbles: {stats['lastfm_success']}/{stats['total']}")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()
