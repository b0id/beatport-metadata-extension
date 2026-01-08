// BeatportDJ Metadata Tracker (with "pending" + manual publish)
console.log('BeatportDJ Metadata Tracker loaded');

let lastDeck1 = '';
let lastDeck2 = '';
let pendingDeck1 = '';
let pendingDeck2 = '';

let lastPublished = '';
let lastChangedDeck = 0; // 1 or 2

function extractTrackInfo(songId, tagId) {
  const songDiv = document.querySelector(songId);
  const tagDiv = document.querySelector(tagId);

  if (!songDiv || !tagDiv) return null;

  const titleEl = songDiv.querySelector('.song_link1, .song_link2');
  const title = titleEl ? titleEl.textContent.trim() : null;

  const artistEls = tagDiv.querySelectorAll('.tag_artist_link');
  const artists = Array.from(artistEls).map(el => el.textContent.trim()).join(', ');

  if (title && artists) return `${artists} - ${title}`;
  return null;
}

function postTrack(track) {
  if (!track || track === lastPublished) return;

  console.log('PUBLISH:', track);
  fetch('http://localhost:3000/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ track })
  }).catch(err => console.error('Failed to update metadata:', err));

  lastPublished = track;
}

function updatePending() {
  const track1 = extractTrackInfo('#song1', '#tag1');
  const track2 = extractTrackInfo('#song2', '#tag2');

  if (track1 && track1 !== lastDeck1) {
    console.log('Deck A loaded (pending):', track1);
    lastDeck1 = track1;
    pendingDeck1 = track1;
    lastChangedDeck = 1;
  }

  if (track2 && track2 !== lastDeck2) {
    console.log('Deck B loaded (pending):', track2);
    lastDeck2 = track2;
    pendingDeck2 = track2;
    lastChangedDeck = 2;
  }
}

function publishPending(whichDeck = lastChangedDeck) {
  const track = whichDeck === 1 ? pendingDeck1 : pendingDeck2;
  if (!track) return console.log('Nothing pending to publish.');
  postTrack(track);
}

// Hotkey: Ctrl+Shift+U publishes the most recently changed deck
window.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.shiftKey && (e.code === 'KeyU' || e.key.toLowerCase() === 'u')) {
    e.preventDefault();
    publishPending();
  }
});

// Tiny on-screen button (optional but handy)
(function addPublishButton() {
  const btn = document.createElement('button');
  btn.textContent = 'Update overlay';
  btn.style.cssText = `
    position: fixed; z-index: 999999;
    bottom: 16px; right: 16px;
    padding: 8px 10px;
    font: 12px/1.2 sans-serif;
    border: 1px solid #444; border-radius: 8px;
    background: rgba(0,0,0,0.75); color: #fff;
    cursor: pointer;
  `;
  btn.addEventListener('click', () => publishPending());
  document.documentElement.appendChild(btn);
})();

// Observe player mutations, but only update "pending" — never auto-publish
const observer = new MutationObserver(() => updatePending());

const checkPlayer = setInterval(() => {
  const player = document.getElementById('player');
  if (player) {
    console.log('Player found, starting observer');
    observer.observe(player, { childList: true, subtree: true, characterData: true });
    clearInterval(checkPlayer);
    updatePending();
  }
}, 1000);

// Lightweight polling as backup
setInterval(updatePending, 3000);

