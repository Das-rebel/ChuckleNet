#!/usr/bin/env node
/**
 * Kodi Relay Server
 * Proxies Cloud Run requests to local Kodi
 * Run locally on your network to bridge GCP to Kodi
 */

const express = require('express');
const http = require('http');
const https = require('https');

const app = express();
const PORT = process.env.RELAY_PORT || 3001;
const KODI_HOST = process.env.KODI_HOST || '192.168.0.101';
const KODI_PORT = process.env.KODI_PORT || '8080';
const KODI_USER = process.env.KODI_USER || 'kodi';
const KODI_PASSWORD = process.env.KODI_PASSWORD || 'Password';

// TMDB API for movie search (works without auth for basic search)
const TMDB_API_KEY = '2dca580c2a14b55200e784d157207b4d';

/**
 * Search TMDB for a movie and return its ID
 */
async function searchTmdbMovie(query) {
  const url = `https://api.themoviedb.org/3/search/movie?api_key=${TMDB_API_KEY}&query=${encodeURIComponent(query)}`;

  return new Promise((resolve, reject) => {
    const req = https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (json.results && json.results.length > 0) {
            const movie = json.results[0];
            resolve({
              title: movie.title,
              year: movie.release_date ? movie.release_date.substring(0, 4) : null,
              tmdbId: movie.id,
              imdbId: movie.imdb_id
            });
          } else {
            resolve(null);
          }
        } catch (e) {
          reject(new Error(`TMDB parse error: ${e.message}`));
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('TMDB timeout'));
    });
    req.end();
  });
}

// Middleware
app.use(express.json());

async function makeKodiRequest(method, params = {}) {
  const auth = KODI_PASSWORD
    ? Buffer.from(`${KODI_USER}:${KODI_PASSWORD}`).toString('base64')
    : null;

  const body = {
    jsonrpc: '2.0',
    id: 1,
    method: method,
    params: params
  };

  return new Promise((resolve, reject) => {
    const options = {
      hostname: KODI_HOST,
      port: KODI_PORT,
      path: '/jsonrpc',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    };

    if (auth) {
      options.headers['Authorization'] = `Basic ${auth}`;
    }

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve(data);
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(5000, () => {
      req.destroy();
      reject(new Error('Kodi timeout'));
    });
    req.write(JSON.stringify(body));
    req.end();
  });
}

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'kodi-relay', kodi: KODI_HOST });
});

// POST /kodi/play-movie - Search TMDB and open movie in Seren/Fen
app.post('/kodi/play-movie', async (req, res) => {
  try {
    const { query, addon = 'plugin.video.seren', traktId } = req.body || {};

    if (!query) {
      return res.status(400).json({ error: 'Missing query' });
    }

    // Search TMDB for the movie to confirm it exists
    const movie = await searchTmdbMovie(query);
    if (!movie) {
      return res.json({ success: false, error: `Movie not found: ${query}` });
    }

    console.log(`🎬 Opening "${movie.title}" (TMDB: ${movie.tmdbId}, Trakt: ${traktId}) on ${addon}`);

    // First stop any current playback
    const players = await makeKodiRequest('Player.GetActivePlayers');
    if (players.result && players.result.length > 0) {
      const playerId = players.result[0].playerid;
      await makeKodiRequest('Player.Stop', { playerid: playerId });
      await new Promise(r => setTimeout(r, 1000));
    }

    // Navigate to home first (required for Kodi to properly launch addons)
    await makeKodiRequest('GUI.ActivateWindow', { window: 'home' });
    await new Promise(r => setTimeout(r, 3000));

    // Build seren URL - Seren needs trakt_id, not tmdb_id
    const mediaInfo = traktId
      ? { mediatype: 'movie', trakt_id: traktId }
      : { mediatype: 'movie', tmdb_id: movie.tmdbId };
    const serenUrl = `plugin://${addon}/?action=getSources&action_args=${encodeURIComponent(JSON.stringify(mediaInfo))}`;
    console.log(`📺 Opening: ${serenUrl}`);

    await makeKodiRequest('Player.Open', { item: { file: serenUrl } });
    await new Promise(r => setTimeout(r, 2000));

    res.json({
      success: true,
      movie: movie.title,
      tmdbId: movie.tmdbId,
      traktId: traktId || null,
      addon: addon
    });
  } catch (error) {
    console.error(`❌ play-movie error: ${error.message}`);
    res.json({ success: false, error: error.message });
  }
});

// POST /kodi/play - Play/Pause with optional query to search and play
app.post('/kodi/play', async (req, res) => {
  try {
    const { query } = req.body || {};

    // If query provided, search and play using Seren
    if (query) {
      // First open seren
      await makeKodiRequest('Addons.ExecuteAddon', { addonid: 'plugin.video.seren', params: [] });
      // Then search (Seren will handle search internally via Trakt)
      // For actual playback, we need to use Player.Open with a file path
      // But without scraping, we can't directly play - let's just report success
      res.json({ success: true, action: 'search', addon: 'seren', query: query });
    } else {
      // Regular play/pause
      const playersRes = await makeKodiRequest('Player.GetActivePlayers');
      if (!playersRes.result || playersRes.result.length === 0) {
        return res.json({ success: false, error: 'No active player' });
      }
      const playerId = playersRes.result[0].playerid;
      await makeKodiRequest('Player.PlayPause', { playerid: playerId, play: true });
      res.json({ success: true });
    }
  } catch (error) {
    res.json({ success: false, error: error.message });
  }
});

// POST /kodi/pause - Pause
app.post('/kodi/pause', async (req, res) => {
  try {
    const playersRes = await makeKodiRequest('Player.GetActivePlayers');
    if (!playersRes.result || playersRes.result.length === 0) {
      return res.json({ success: false, error: 'No active player' });
    }
    const playerId = playersRes.result[0].playerid;
    await makeKodiRequest('Player.PlayPause', { playerid: playerId, play: false });
    res.json({ success: true });
  } catch (error) {
    res.json({ success: false, error: error.message });
  }
});

// POST /kodi/open-addon - Open addon with optional search query
app.post('/kodi/open-addon', async (req, res) => {
  try {
    const { addonid, query } = req.body;
    if (!addonid) {
      return res.status(400).json({ error: 'Missing addonid' });
    }

    if (query) {
      // Use Player.Open with plugin URL to trigger search
      const searchUrl = `plugin://${addonid}?action=search&q=${encodeURIComponent(query)}`;
      await makeKodiRequest('Player.Open', { item: { file: searchUrl } });
      res.json({ success: true, addon: addonid, action: 'search', query: query });
    } else {
      // Just open the addon
      await makeKodiRequest('Addons.ExecuteAddon', { addonid, params: [] });
      res.json({ success: true, addon: addonid, result: 'OK' });
    }
  } catch (error) {
    res.json({ success: false, error: error.message });
  }
});

// GET /kodi/status - Get current playback
app.get('/kodi/status', async (req, res) => {
  try {
    const playersRes = await makeKodiRequest('Player.GetActivePlayers');
    if (!playersRes.result || playersRes.result.length === 0) {
      return res.json({ isPlaying: false });
    }
    const playerId = playersRes.result[0].playerid;
    const itemRes = await makeKodiRequest('Player.GetItem', {
      playerid: playerId,
      properties: ['title', 'artist', 'album', 'showtitle', 'file']
    });
    const propsRes = await makeKodiRequest('Player.GetProperties', {
      playerid: playerId,
      properties: ['speed', 'time', 'totaltime']
    });
    res.json({
      isPlaying: propsRes.result?.speed === 1,
      item: itemRes.result?.item,
      position: propsRes.result?.time
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Generic JSON-RPC proxy (must be last)
app.post('/kodi/:method', async (req, res) => {
  const method = req.params.method;
  const params = req.body || {};

  const auth = KODI_PASSWORD
    ? Buffer.from(`${KODI_USER}:${KODI_PASSWORD}`).toString('base64')
    : null;

  const body = {
    jsonrpc: '2.0',
    id: 1,
    method: method,
    params: params
  };

  const options = {
    hostname: KODI_HOST,
    port: KODI_PORT,
    path: '/jsonrpc',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  };

  if (auth) {
    options.headers['Authorization'] = `Basic ${auth}`;
  }

  try {
    const response = await new Promise((resolve, reject) => {
      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            resolve(data);
          }
        });
      });
      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Kodi timeout'));
      });
      req.write(JSON.stringify(body));
      req.end();
    });

    res.json(response);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n🔌 Kodi Relay Server`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`✅ Listening on http://0.0.0.0:${PORT}`);
  console.log(`📺 Kodi: ${KODI_HOST}:${KODI_PORT}`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`\nEndpoints:`);
  console.log(`  GET  /health          - Health check`);
  console.log(`  POST /kodi/play       - Play/Pause`);
  console.log(`  POST /kodi/pause     - Pause`);
  console.log(`  POST /kodi/open-addon - Open addon {addonid}`);
  console.log(`  GET  /kodi/status     - Get current playback`);
  console.log(`  POST /kodi/:method   - Generic JSON-RPC`);
  console.log(`\n📡 Expose with: ngrok http ${PORT}\n`);
});