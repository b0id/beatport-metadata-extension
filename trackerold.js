// BeatportDJ Metadata Tracker
console.log('BeatportDJ Metadata Tracker loaded');

let lastTrack = '';
let lastDeck1 = '';
let lastDeck2 = '';

function extractTrackInfo(songId, tagId) {
  const songDiv = document.querySelector(songId);
  const tagDiv = document.querySelector(tagId);
  
  if (!songDiv || !tagDiv) return null;
  
  const titleEl = songDiv.querySelector('.song_link1, .song_link2');
  const title = titleEl ? titleEl.textContent.trim() : null;
  
  const artistEls = tagDiv.querySelectorAll('.tag_artist_link');
  const artists = Array.from(artistEls).map(el => el.textContent.trim()).join(', ');
  
  if (title && artists) {
    return `${artists} - ${title}`;
  }
  return null;
}

function updateMetadata() {
  const track1 = extractTrackInfo('#song1', '#tag1');
  const track2 = extractTrackInfo('#song2', '#tag2');
  
  let currentTrack = null;
  
  // Check which deck changed most recently
  if (track1 && track1 !== lastDeck1) {
    console.log('Deck A changed:', track1);
    currentTrack = track1;
    lastDeck1 = track1;
  }
  
  if (track2 && track2 !== lastDeck2) {
    console.log('Deck B changed:', track2);
    currentTrack = track2;
    lastDeck2 = track2;
  }
  
  // Update if we have a new track
  if (currentTrack && currentTrack !== lastTrack) {
    console.log('Track update:', currentTrack);
    
    fetch('http://localhost:3000/update', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({track: currentTrack})
    }).catch(err => console.error('Failed to update metadata:', err));
    
    lastTrack = currentTrack;
  }
}

const observer = new MutationObserver(() => {
  updateMetadata();
});

const checkPlayer = setInterval(() => {
  const player = document.getElementById('player');
  if (player) {
    console.log('Player found, starting observer');
    observer.observe(player, {
      childList: true,
      subtree: true,
      characterData: true
    });
    clearInterval(checkPlayer);
    
    updateMetadata();
  }
}, 1000);

setInterval(updateMetadata, 3000);
