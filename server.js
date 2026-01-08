const express = require('express');
const fs = require('fs');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

const OUTPUT_FILE = '/home/b0id/beatport-nowplaying.txt';

app.post('/update', (req, res) => {
  const { track } = req.body;
  if (track) {
    fs.writeFileSync(OUTPUT_FILE, track + '\n');
    console.log('Updated:', track);
  }
  res.send('OK');
});

app.listen(3000, () => {
  console.log('Metadata server running on http://localhost:3000');
  console.log('Writing to:', OUTPUT_FILE);
});
