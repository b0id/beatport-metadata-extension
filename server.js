const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

const OUTPUT_FILE = '/home/b0id/beatport-nowplaying.txt';
const LOGS_DIR = '/mnt/aux/beatport-logs';

// Parse track to extract first artist and clean title
function parseTrack(track) {
  // Input: "Artist1, Artist2 - Track Title - Original Mix"
  // Output: "Artist1 - Track Title"

  const parts = track.split(' - ');
  if (parts.length < 2) {
    // Fallback if format is unexpected
    return track;
  }

  // Get first artist (split on comma and take first)
  const artistPart = parts[0].split(',')[0].trim();

  // Get clean title (second part, ignoring mix version)
  const title = parts[1].trim();

  return `${artistPart} - ${title}`;
}

// Get today's log file path
function getTodayLogFile() {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  return path.join(LOGS_DIR, `${today}.log`);
}

app.post('/update', (req, res) => {
  const { track } = req.body;
  if (track) {
    // Write full track to butt file (existing functionality)
    fs.writeFileSync(OUTPUT_FILE, track + '\n');
    console.log('Updated:', track);

    // Parse and write to daily log
    const cleanTrack = parseTrack(track);
    const timestamp = new Date().toISOString();
    const logEntry = `${timestamp} | ${cleanTrack}\n`;
    const logFile = getTodayLogFile();

    try {
      fs.appendFileSync(logFile, logEntry);
      console.log('Logged:', cleanTrack);
    } catch (err) {
      console.error('Failed to write to log:', err.message);
    }
  }
  res.send('OK');
});

app.listen(3000, () => {
  console.log('Metadata server running on http://localhost:3000');
  console.log('Writing to:', OUTPUT_FILE);
  console.log('Daily logs:', LOGS_DIR);
});
