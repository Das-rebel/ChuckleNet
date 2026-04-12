/**
 * Kodi/XBMC JSON-RPC API Client
 * Controls Kodi media center via JSON-RPC v2.0 over HTTP
 */

class KodiClient {
  constructor(config = {}) {
    this.host = config.host || process.env.KODI_HOST || 'http://localhost:8080';
    this.username = config.username || process.env.KODI_USERNAME || 'kodi';
    this.password = config.password || process.env.KODI_PASSWORD || '';
    this.timeout = config.timeout || 10000;

    this.enabled = !!this.host;
    this.jsonRpcVersion = '2.0';

    if (this.enabled) {
      console.log('📺 Kodi Client initialized');
      console.log(`   - Host: ${this.host}`);
      console.log(`   - Auth: ${this.username}${this.password ? ' (password set)' : ' (no password)'}`);
    } else {
      console.warn('⚠️ Kodi API disabled (no host configured)');
    }
  }

  /**
   * Make JSON-RPC call to Kodi
   */
  async _call(method, params = {}) {
    const auth = this.password
      ? Buffer.from(`${this.username}:${this.password}`).toString('base64')
      : null;

    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };

    if (auth) {
      headers['Authorization'] = `Basic ${auth}`;
    }

    const body = {
      jsonrpc: this.jsonRpcVersion,
      id: 1,
      method: method,
      params: params
    };

    try {
      const response = await fetch(this.host, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(this.timeout)
      });

      if (!response.ok) {
        throw new Error(`Kodi API returned ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(`Kodi JSON-RPC error: ${data.error.message || JSON.stringify(data.error)}`);
      }

      return data.result;
    } catch (error) {
      console.error(`❌ Kodi call failed (${method}): ${error.message}`);
      throw error;
    }
  }

  /**
   * Get active players
   */
  async getPlayers() {
    try {
      const result = await this._call('Player.GetActivePlayers');
      return {
        success: true,
        players: result || []
      };
    } catch (error) {
      return { success: false, error: error.message, players: [] };
    }
  }

  /**
   * Get playback state
   */
  async getPlaybackState() {
    try {
      const players = await this.getPlayers();
      if (!players.success || players.players.length === 0) {
        return { success: true, playing: false, state: 'stopped' };
      }

      const playerId = players.players[0].playerid;

      // Get item playing
      const itemResult = await this._call('Player.GetItem', {
        playerid: playerId,
        properties: ['title', 'artist', 'album', 'showtitle', 'season', 'episode', 'file']
      });

      // Get properties (position, time, etc)
      const propsResult = await this._call('Player.GetProperties', {
        playerid: playerId,
        properties: ['speed', 'time', 'totaltime', 'percentage', 'shuffled', 'repeat']
      });

      const current = propsResult.time || {};
      const total = propsResult.totaltime || {};

      return {
        success: true,
        playing: propsResult.speed === 1,
        playerId: playerId,
        type: players.players[0].type,
        item: itemResult.item,
        position: `${current.hours || 0}:${String(current.minutes || 0).padStart(2, '0')}:${String(current.seconds || 0).padStart(2, '0')}`,
        duration: `${total.hours || 0}:${String(total.minutes || 0).padStart(2, '0')}:${String(total.seconds || 0).padStart(2, '0')}`,
        percentage: propsResult.percentage || 0,
        shuffled: propsResult.shuffled || false,
        repeat: propsResult.repeat || 'off'
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Play
   */
  async play() {
    try {
      const players = await this.getPlayers();
      if (!players.success || players.players.length === 0) {
        return { success: false, error: 'No active player' };
      }

      const playerId = players.players[0].playerid;
      await this._call('Player.PlayPause', { playerid: playerId, play: true });
      console.log('✅ Kodi playback started/resumed');
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Pause
   */
  async pause() {
    try {
      const players = await this.getPlayers();
      if (!players.success || players.players.length === 0) {
        return { success: false, error: 'No active player' };
      }

      const playerId = players.players[0].playerid;
      await this._call('Player.PlayPause', { playerid: playerId, play: false });
      console.log('✅ Kodi playback paused');
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Stop
   */
  async stop() {
    try {
      const players = await this.getPlayers();
      if (!players.success || players.players.length === 0) {
        return { success: false, error: 'No active player' };
      }

      const playerId = players.players[0].playerid;
      await this._call('Player.Stop', { playerid: playerId });
      console.log('✅ Kodi playback stopped');
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Execute arbitrary action
   */
  async executeAction(action) {
    try {
      const players = await this.getPlayers();
      if (!players.success || players.players.length === 0) {
        return { success: false, error: 'No active player' };
      }

      const playerId = players.players[0].playerid;
      await this._call('Player.SendText', {
        playerid: playerId,
        text: action
      });
      console.log(`✅ Kodi action executed: ${action}`);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Show movies
   */
  async showMovies(limit = 10) {
    try {
      const result = await this._call('VideoLibrary.GetMovies', {
        properties: ['title', 'originaltitle', 'year', 'rating', 'genre', 'thumbnail'],
        limits: { start: 0, end: limit }
      });

      const movies = (result.movies || []).map(movie => ({
        id: movie.movieid,
        title: movie.title,
        year: movie.year,
        rating: movie.rating ? movie.rating.toFixed(1) : 'N/A',
        genre: movie.genre ? movie.genre.slice(0, 3).join(', ') : 'Unknown',
        thumbnail: movie.thumbnail
      }));

      return {
        success: true,
        movies: movies,
        total: result.limits?.total || movies.length
      };
    } catch (error) {
      return { success: false, error: error.message, movies: [] };
    }
  }

  /**
   * Show TV shows
   */
  async showTVShows(limit = 10) {
    try {
      const result = await this._call('VideoLibrary.GetTVShows', {
        properties: ['title', 'year', 'rating', 'genre', 'thumbnail'],
        limits: { start: 0, end: limit }
      });

      const shows = (result.tvshows || []).map(show => ({
        id: show.tvshowid,
        title: show.title,
        year: show.year,
        rating: show.rating ? show.rating.toFixed(1) : 'N/A',
        genre: show.genre ? show.genre.slice(0, 3).join(', ') : 'Unknown',
        thumbnail: show.thumbnail
      }));

      return {
        success: true,
        shows: shows,
        total: result.limits?.total || shows.length
      };
    } catch (error) {
      return { success: false, error: error.message, shows: [] };
    }
  }

  /**
   * Get application properties (volume, muted, etc)
   */
  async getApplicationProperties() {
    try {
      const result = await this._call('Application.GetProperties', {
        properties: ['volume', 'muted', 'name', 'version']
      });

      return {
        success: true,
        volume: result.volume,
        muted: result.muted,
        name: result.name,
        version: result.version
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Set volume (0-100)
   */
  async setVolume(volume) {
    try {
      await this._call('Application.SetVolume', { volume: volume });
      console.log(`✅ Kodi volume set to ${volume}`);
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Open addon by name (e.g., "seren", "fen", "oplasma")
   */
  async openAddon(addonName) {
    try {
      // Use Player.Open with addon item to launch addons
      const result = await this._call('Player.Open', {
        item: { addonid: addonName }
      });
      console.log(`✅ Kodi addon opened: ${addonName}`);
      return { success: true, addon: addonName };
    } catch (error) {
      // Fallback - try different method
      try {
        await this._call('Addons.ExecuteAddon', { addonid: addonName });
        console.log(`✅ Kodi addon executed: ${addonName}`);
        return { success: true, addon: addonName };
      } catch (error2) {
        return { success: false, error: error2.message };
      }
    }
  }

  /**
   * Get addon details
   */
  async getAddon(addonName) {
    try {
      const result = await this._call('Addons.GetAddonDetails', {
        addonid: addonName,
        properties: ['name', 'version', 'description', 'enabled']
      });
      return {
        success: true,
        addon: {
          name: result.addon.name,
          version: result.addon.version,
          description: result.addon.description,
          enabled: result.addon.enabled
        }
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  /**
   * Get status
   */
  getStatus() {
    return {
      platform: 'kodi',
      host: this.host,
      enabled: this.enabled,
      timeout: this.timeout
    };
  }
}

module.exports = KodiClient;