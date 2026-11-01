(() => {
  'use strict';

  const RADIO_API = [
    'https://de1.api.radio-browser.info/json',
    'https://nl1.api.radio-browser.info/json',
    'https://at1.api.radio-browser.info/json'
  ];
  const IPTV_BASE = 'https://iptv-org.github.io/iptv/';
  const NEWS = [
    {name:'BBC News', region:'WORLD', initials:'BBC', url:'https://www.bbc.com/news', detail:'World news, explainers, and live coverage.'},
    {name:'The Hindu', region:'INDIA', initials:'TH', url:'https://www.thehindu.com/', detail:'National reporting, analysis, and opinion.'},
    {name:'The Indian Express', region:'INDIA', initials:'IE', url:'https://indianexpress.com/', detail:'India and international headlines.'},
    {name:'Sikkim Express', region:'SIKKIM', initials:'SE', url:'https://www.sikkimexpress.com/', detail:'News and reporting from Sikkim.'},
    {name:'Daily Thanthi', region:'TAMIL', initials:'த', url:'https://www.dailythanthi.com/', detail:'Tamil news and regional coverage.'},
    {name:'All India Radio News', region:'INDIA', initials:'AIR', url:'https://www.newsonair.gov.in/', detail:'News from India’s public broadcaster.'},
    {name:'Reuters', region:'WORLD', initials:'R', url:'https://www.reuters.com/world/', detail:'International news and reporting.'},
    {name:'The Guardian', region:'WORLD', initials:'G', url:'https://www.theguardian.com/international', detail:'Global news, culture, and features.'},
    {name:'Google News India', region:'INDIA', initials:'GN', url:'https://news.google.com/home?hl=en-IN&gl=IN&ceid=IN:en', detail:'Browse headlines from many publishers.'}
  ];
  const COUNTRY_COORDS = {
    IN:[20.6,78.9], SG:[1.35,103.82], NP:[28.39,84.12], LK:[7.87,80.77], BD:[23.68,90.36],
    US:[39.8,-98.6], GB:[54,-2.5], AU:[-25.3,133.8], CA:[56.1,-106.3], JP:[36.2,138.2],
    KR:[36.4,127.9], CN:[35.9,104.2], FR:[46.2,2.2], DE:[51.2,10.4], IT:[41.9,12.6],
    BR:[-10.8,-52.9], ZA:[-29,24], AE:[23.4,53.8], NZ:[-41.2,174.8], PH:[12.9,122.8],
    MY:[4.2,102.2], ID:[-2.5,118], TH:[15.8,101], PK:[30.4,69.3], MX:[23.6,-102.5]
  };
  const WMO = {0:'Clear sky',1:'Mostly clear',2:'Partly cloudy',3:'Overcast',45:'Fog',48:'Rime fog',51:'Light drizzle',53:'Drizzle',55:'Heavy drizzle',61:'Light rain',63:'Rain',65:'Heavy rain',71:'Light snow',73:'Snow',75:'Heavy snow',80:'Rain showers',81:'Showers',82:'Heavy showers',95:'Thunderstorm',96:'Thunderstorm with hail',99:'Strong thunderstorm'};
  const $ = (id) => document.getElementById(id);
  const safe = (value) => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const radioAudio = $('radio-player');
  const tvVideo = $('tv-player');
  let radioStations = [];
  let tvStations = [];
  let showingRadioFavorites = false;
  let showingTVFavorites = false;
  let tvFilterTouched = false;
  let currentRadio = null;
  let currentTV = null;
  let hls = null;
  let tvLoadController = null;
  let selectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  let toastTimer = null;
  let activeGenre = 'all';
  let activeRegion = 'global';
  let shuffleFavorites = false;
  let repeatCurrent = false;
  const favoriteHistory = [];
  let favoriteHistoryMode = '';

  const readStore = (key) => {
    try { const value = JSON.parse(localStorage.getItem(key) || '{}'); return value && typeof value === 'object' ? value : {}; }
    catch { return {}; }
  };
  const radioFavorites = readStore('coolmag.radio.favorites.v1');
  const tvFavorites = readStore('coolmag.tv.favorites.v1');
  showingTVFavorites = Object.keys(tvFavorites).length > 0;
  const persist = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { toast('This browser could not save favorites.'); } };
  const toast = (message) => {
    const node = $('toast'); node.textContent = message; node.classList.add('show');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => node.classList.remove('show'), 2600);
  };

  function activeMedia() { return currentTV ? tvVideo : currentRadio ? radioAudio : null; }
  function syncTransport() {
    const media=activeMedia();
    const playing=Boolean(media&&!media.paused&&!media.ended);
    $('play-pause').textContent=playing?'Ⅱ':'▶';
    $('play-pause').setAttribute('aria-label',playing?'Pause playback':'Play playback');
    $('play-pause').title=playing?'Pause playback':'Play playback';
    const tvMode=$('tv-view').classList.contains('active')||Boolean(currentTV);
    const favorites=tvMode?Object.keys(tvFavorites).length:Object.keys(radioFavorites).length;
    $('previous-favorite').disabled=favorites===0;
    $('next-favorite').disabled=favorites===0;
    $('shuffle-toggle').classList.toggle('active',shuffleFavorites);
    $('shuffle-toggle').setAttribute('aria-pressed',String(shuffleFavorites));
    $('repeat-toggle').classList.toggle('active',repeatCurrent);
    $('repeat-toggle').setAttribute('aria-pressed',String(repeatCurrent));
    let canSeek=false;
    try { canSeek=Boolean(media&&media.seekable&&media.seekable.length&&media.seekable.end(media.seekable.length-1)-media.seekable.start(media.seekable.length-1)>1); } catch {}
    $('seek-back').disabled=!canSeek;
    $('seek-forward').disabled=!canSeek;
    $('audio-visualizer')?.classList.toggle('active',playing);
    $('dock-quality').textContent=currentRadio?.bitrate?`${currentRadio.bitrate} KBPS`:'AUTO';
    try { if(navigator.mediaSession) navigator.mediaSession.playbackState=media?(playing?'playing':'paused'):'none'; } catch {}
  }
  function setMediaMetadata(title,detail) {
    if(!navigator.mediaSession||typeof MediaMetadata==='undefined')return;
    try { navigator.mediaSession.metadata=new MediaMetadata({title:title||'CoolMag Media Center',artist:detail||'',album:'CoolMag Media Center'}); } catch {}
  }
  function playPauseActive() {
    const media=activeMedia();
    if(!media){toast('Choose a station or channel first.');return;}
    if(media.paused){media.play().catch(()=>toast('Playback could not start.'));}
    else media.pause();
    syncTransport();
  }
  function stepFavorite(direction) {
    const tvMode=$('tv-view').classList.contains('active')||Boolean(currentTV);
    const list=Object.values(tvMode?tvFavorites:radioFavorites);
    if(!list.length){toast('Add favorites to use previous and next.');syncTransport();return;}
    const current=tvMode?currentTV:currentRadio;
    const historyMode=tvMode?'tv':'radio';if(favoriteHistoryMode!==historyMode){favoriteHistory.length=0;favoriteHistoryMode=historyMode;}
    if(shuffleFavorites&&direction<0&&favoriteHistory.length){const previous=favoriteHistory.pop();if(previous){if(tvMode)playTV(previous);else playRadio(previous);return;}}
    if(shuffleFavorites&&direction>0){const choices=list.filter(item=>tvMode?item.url!==current?.url:radioKey(item)!==radioKey(current||{}));if(current)favoriteHistory.push(current);const random=choices[Math.floor(Math.random()*choices.length)]||list[0];if(tvMode)playTV(random);else playRadio(random);return;}
    let index=list.findIndex(item=>tvMode?item.url===current?.url:radioKey(item)===radioKey(current||{}));
    if(index<0)index=direction>0?-1:0;
    const next=list[(index+direction+list.length)%list.length];
    if(tvMode)playTV(next);else playRadio(next);
  }
  function seekActive(seconds) {
    const media=activeMedia();
    if(!media){toast('Choose a station or channel first.');return;}
    try {
      const ranges=media.seekable;
      if(!ranges||!ranges.length){toast('This live stream does not support rewind or forward.');syncTransport();return;}
      const start=ranges.start(ranges.length-1),end=ranges.end(ranges.length-1);
      media.currentTime=Math.max(start,Math.min(end,media.currentTime+seconds));
    } catch { toast('This stream does not support seeking.'); }
    syncTransport();
  }
  function setupMediaSession() {
    if(!navigator.mediaSession?.setActionHandler)return;
    const actions={play:()=>{const media=activeMedia();if(media)media.play().catch(()=>{});},pause:()=>activeMedia()?.pause(),previoustrack:()=>stepFavorite(-1),nexttrack:()=>stepFavorite(1),seekbackward:event=>seekActive(-(event.seekOffset||10)),seekforward:event=>seekActive(event.seekOffset||10)};
    for(const [action,handler] of Object.entries(actions)){try{navigator.mediaSession.setActionHandler(action,handler);}catch{}}
  }

  function setView(view) {
    if(view==='tv')showingTVFavorites=Object.keys(tvFavorites).length>0;
    document.querySelectorAll('.side-link').forEach(button=>button.classList.toggle('active',button.dataset.view===view||(view==='playlists'&&button.dataset.action==='playlists')));
    document.querySelectorAll('.view-panel').forEach(panel => panel.classList.toggle('active', panel.id === `${view}-view`));
    const titles={home:'Your media, in one place',radio:'World Radio',tv:'Live TV',schedule:'Schedule & queue',favorites:'Your favorites',playlists:'TV playlists',news:'News & magazines'};
    $('section-title').textContent=titles[view]||'COOLmagRaTv';
    if(view==='tv'&&currentRadio){radioAudio.pause();radioAudio.removeAttribute('src');radioAudio.load();currentRadio=null;}
    if(view==='radio'&&currentTV)stopTV();
    if(view==='news'){if(currentRadio){radioAudio.pause();radioAudio.removeAttribute('src');radioAudio.load();currentRadio=null;}if(currentTV)stopTV();}
    if(!activeMedia()){$('playing-title').textContent='COOLmagRaTv';$('playing-subtitle').textContent='Choose a stream to begin';}
    if(view==='favorites')renderFavorites();
    if(view==='tv')renderTV();
    renderSchedule();
    $('sidebar').classList.remove('open');
    syncTransport();
  }
  document.querySelectorAll('.side-link[data-view],.text-button[data-view]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.view)));
  document.querySelectorAll('[data-action="playlists"]').forEach(button=>button.addEventListener('click',()=>setView('playlists')));
  document.querySelectorAll('[data-home-link]').forEach(link=>link.addEventListener('click',event=>{event.preventDefault();setView('home');}));
  $('menu-button').addEventListener('click',()=> $('sidebar').classList.toggle('open'));
  $('landscape-button').addEventListener('click',async()=>{
    const button=$('landscape-button');
    if(document.fullscreenElement){
      try{screen.orientation?.unlock?.();}catch{}
      try{await document.exitFullscreen();}catch{}
      return;
    }
    try{await document.documentElement.requestFullscreen();}catch{}
    try{
      await screen.orientation.lock('landscape');
      toast('Landscape player view is on.');
    }catch{
      toast('Rotate your phone sideways for the landscape player view.');
    }
    button.setAttribute('aria-label','Exit landscape fullscreen');
  });
  document.addEventListener('fullscreenchange',()=>{
    const button=$('landscape-button');
    const active=Boolean(document.fullscreenElement);
    button.classList.toggle('active',active);
    button.setAttribute('aria-label',active?'Exit landscape fullscreen':'Enter landscape fullscreen');
  });
  document.querySelectorAll('[data-genre]').forEach(button=>button.addEventListener('click',()=>{activeGenre=button.dataset.genre;document.querySelectorAll('[data-genre]').forEach(chip=>chip.classList.toggle('active',chip===button));renderHomeTV();}));
  document.querySelectorAll('[data-region]').forEach(button=>button.addEventListener('click',()=>{activeRegion=button.dataset.region;document.querySelectorAll('[data-region]').forEach(chip=>chip.classList.toggle('active',chip===button));renderHomeTV();}));
  $('settings-button').addEventListener('click',()=>toast('Volume and playback controls are in the player dock.'));
  $('hero-watch').addEventListener('click',()=>{if(tvStations.length){setView('tv');playTV(tvStations[0]);}else setView('playlists');});

  function showOrigin(countryName, countryCode) {
    $('origin-country').textContent = countryName || 'Selected country';
    $('origin-code').textContent = countryCode
      ? `${countryCode.toUpperCase()} · COUNTRY OF ORIGIN`
      : 'COUNTRY OF ORIGIN';
  }
  async function radioGet(path) {
    let lastError;
    for (const base of RADIO_API) {
      try {
        const response = await fetch(`${base}${path}`, {headers:{'Accept':'application/json'}});
        if (!response.ok) throw new Error(`Radio directory returned ${response.status}`);
        return await response.json();
      } catch (error) { lastError = error; }
    }
    throw lastError || new Error('Radio directory is unavailable.');
  }
  async function loadCountries() {
    try {
      const rows = await radioGet('/countries?order=stationcount&reverse=true');
      const select = $('country-select');
      const byCode = new Map(rows.filter(row => row.iso_3166_1 && row.name).map(row => [row.iso_3166_1,row.name]));
      const sorted = [...byCode.entries()].sort((a,b) => a[1].localeCompare(b[1]));
      select.innerHTML = '<option value="all">Worldwide</option>' + sorted.map(([code,name]) => `<option value="${safe(code)}">${safe(name)}</option>`).join('');
      select.value = byCode.has('IN') ? 'IN' : 'all';
    } catch { /* Keep the built-in India option when the directory is unavailable. */ }
  }
  function radioKey(station) { return station.stationuuid || station.url_resolved || station.url || station.name; }
  function toggleRadioFavorite(station) {
    const key = radioKey(station);
    if (radioFavorites[key]) delete radioFavorites[key]; else radioFavorites[key] = station;
    persist('coolmag.radio.favorites.v1',radioFavorites); updateFavoriteCounts(); renderRadio();
    if (currentRadio && radioKey(currentRadio) === key) updateCurrentRadioStar();
  }
  function updateFavoriteCounts() {
    $('radio-favorite-count').textContent = Object.keys(radioFavorites).length;
    $('tv-favorite-count').textContent = Object.keys(tvFavorites).length;
    $('sidebar-favorite-count').textContent = Object.keys(radioFavorites).length+Object.keys(tvFavorites).length;
    syncTransport();
  }
  async function loadSharedFavorites() {
    const base = 'https://raw.githubusercontent.com/suppuone/RADIOtv/main/';
    const sources = [
      ['map_favorites.json', radioFavorites, 'coolmag.radio.favorites.v1'],
      ['surak_home_tv_favorites.json', tvFavorites, 'coolmag.tv.favorites.v1']
    ];
    await Promise.all(sources.map(async ([file, target, storageKey]) => {
      try {
        const response = await fetch(base + file, {cache:'no-store'});
        if (!response.ok) return;
        const shared = await response.json();
        if (!shared || typeof shared !== 'object' || Array.isArray(shared)) return;
        for (const [key, station] of Object.entries(shared)) target[key] = station;
        persist(storageKey, target);
      } catch { /* Local favorites keep working if GitHub is unreachable. */ }
    }));
    updateFavoriteCounts();
    if (showingRadioFavorites) renderRadio();
    if (!tvFilterTouched && Object.keys(tvFavorites).length) showingTVFavorites = true;
    if (showingTVFavorites) renderTV();
    renderHomeRadio();renderHomeTV();renderFavorites();renderSchedule();
  }
  function updateCurrentRadioStar() {
    const starred = Boolean(currentRadio && radioFavorites[radioKey(currentRadio)]);
    $('play-pause').title = 'Play / pause';
    $('playing-title').dataset.favorite = starred ? 'yes' : 'no';
  }
  function stationCountryCode(station) {
    const code = (station.countrycode || station.countryCode || '').toUpperCase();
    if (code.length === 2) return code;
    const options = $('country-select').options;
    const country = (station.country || '').toLowerCase();
    for (const option of options) if (option.text.toLowerCase() === country) return option.value;
    return '';
  }
  async function loadWeather(countryName, countryCode) {
    $('weather-place').textContent = countryName || 'Selected country';
    $('weather-summary').textContent = 'Fetching local conditions…';
    $('weather-temperature').textContent = '--°'; $('weather-wind').textContent = '--'; $('weather-humidity').textContent = '--';
    try {
      let place = null;
      if (countryCode && COUNTRY_COORDS[countryCode]) place = {latitude:COUNTRY_COORDS[countryCode][0],longitude:COUNTRY_COORDS[countryCode][1],timezone:null};
      if (!place) {
        const geoUrl = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(countryName || 'India')}&count=1&language=en&format=json`;
        const geo = await (await fetch(geoUrl)).json(); place = geo.results?.[0];
      }
      if (!place) throw new Error('Location not found');
      selectedTimezone = place.timezone || 'UTC';
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${place.latitude}&longitude=${place.longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&timezone=auto`;
      const weather = await (await fetch(url)).json(); const now = weather.current;
      if (!now) throw new Error('No current weather');
      selectedTimezone = weather.timezone || place.timezone || selectedTimezone;
      $('weather-temperature').textContent = `${Math.round(now.temperature_2m)}°`;
      $('weather-summary').textContent = `${WMO[now.weather_code] || 'Current conditions'} · feels like ${Math.round(now.apparent_temperature)}°`;
      $('weather-wind').textContent = `${Math.round(now.wind_speed_10m)} km/h`;
      $('weather-humidity').textContent = `${now.relative_humidity_2m}%`;
      $('weather-symbol').textContent = now.weather_code === 0 ? '☀' : now.weather_code >= 61 ? '☂' : '☁';
      showOrigin(countryName,countryCode);
      syncHomeWeather();
    } catch {
      $('weather-summary').textContent = 'Live weather is unavailable right now.';
      showOrigin(countryName,countryCode);
      syncHomeWeather();
    }
  }
  function renderRadio() {
    const target = $('radio-stations');
    const rows = (showingRadioFavorites ? Object.values(radioFavorites) : radioStations).slice(0,100);
    $('station-list-title').textContent = showingRadioFavorites ? 'Your radio favorites' : `${$('country-select').selectedOptions[0]?.text || 'Worldwide'} stations`;
    if (!rows.length) { target.innerHTML = '<div class="empty-state">No stations found. Try another search or country.</div>';renderHomeRadio();renderFavorites();renderSchedule();return; }
    target.innerHTML = rows.map((station,index) => {
      const key = safe(radioKey(station)); const favorite = Boolean(radioFavorites[radioKey(station)]);
      const playing = currentRadio && radioKey(currentRadio) === radioKey(station);
      const tags = (station.tags || '').split(',').map(v => v.trim()).filter(Boolean).slice(0,2).join(' · ');
      const meta = [station.country || 'Internet radio', tags || station.codec || 'Live stream'].filter(Boolean).join(' · ');
      const art=station.favicon?`<img class="tile-logo" src="${safe(station.favicon)}" loading="lazy" alt="" onerror="this.style.display='none'">`:`<span class="tile-initials" aria-hidden="true">${safe((station.name||'FM').trim().slice(0,2).toUpperCase())}</span>`;
      return `<article class="station-card radio-tile tile-tone-${index%9} ${playing?'playing':''}" data-radio-key="${key}" tabindex="0" role="button" aria-label="Play ${safe(station.name)}"><button class="tile-star star-button ${favorite?'is-favorite':''}" data-radio-star="${key}" title="${favorite?'Remove':'Add'} favorite" aria-label="${favorite?'Remove':'Add'} favorite">${favorite?'★':'☆'}</button><span class="tile-wave" aria-hidden="true">${playing?'♫':'〰'}</span>${art}<b>${safe(station.name || 'Unnamed station')}</b><small>${safe(meta)}</small><span class="tile-quality">${station.bitrate?`${station.bitrate} KBPS`:safe(station.codec||'LIVE')}</span></article>`;
    }).join('');
    target.querySelectorAll('.station-card').forEach(card => {
      const station = rows.find(row => radioKey(row) === card.dataset.radioKey);
      card.addEventListener('click', event => { if (event.target.closest('[data-radio-star]')) return; playRadio(station); });
      card.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); playRadio(station); } });
    });
    target.querySelectorAll('[data-radio-star]').forEach(button => button.addEventListener('click', event => { event.stopPropagation(); const station = rows.find(row => radioKey(row) === button.dataset.radioStar); if (station) toggleRadioFavorite(station); }));
    renderHomeRadio();renderFavorites();renderSchedule();
  }

  function syncHomeWeather() {
    $('home-weather-place').textContent=$('weather-place').textContent;
    $('home-weather-temperature').textContent=$('weather-temperature').textContent;
    $('home-weather-summary').textContent=$('weather-summary').textContent;
  }
  function renderHomeRadio() {
    const target=$('home-radio-grid');if(!target)return;
    const rows=radioStations.slice(0,9);
    if(!rows.length){target.innerHTML='<div class="empty-state">Radio stations are loading…</div>';return;}
    target.innerHTML=rows.map((station,index)=>{
      const key=safe(radioKey(station));const favorite=Boolean(radioFavorites[radioKey(station)]);
      const initials=safe((station.name||'FM').trim().slice(0,2).toUpperCase());
      return `<article class="radio-tile tile-tone-${index%9}" data-home-radio="${key}" tabindex="0" role="button"><button class="tile-star ${favorite?'is-favorite':''}" data-home-radio-star="${key}" aria-label="Toggle favorite">${favorite?'★':'☆'}</button><span class="tile-wave" aria-hidden="true">♫</span>${station.favicon?`<img class="tile-logo" src="${safe(station.favicon)}" loading="lazy" alt="" onerror="this.style.display='none'">`:`<span class="tile-initials" aria-hidden="true">${initials}</span>`}<b>${safe(station.name||'Radio station')}</b><small>${safe(station.country||'INTERNET RADIO')}</small><span class="tile-quality">${station.bitrate?`${station.bitrate} KBPS`:'LIVE'}</span></article>`;
    }).join('');
    target.querySelectorAll('[data-home-radio]').forEach(tile=>{const station=rows.find(item=>radioKey(item)===tile.dataset.homeRadio);tile.addEventListener('click',event=>{if(event.target.closest('[data-home-radio-star]'))return;playRadio(station);});tile.addEventListener('keydown',event=>{if(event.key==='Enter')playRadio(station);});});
    target.querySelectorAll('[data-home-radio-star]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const station=rows.find(item=>radioKey(item)===button.dataset.homeRadioStar);if(station)toggleRadioFavorite(station);}));
  }
  function homeTVRows() {
    let rows=filteredTV();
    if(activeGenre!=='all')rows=rows.filter(row=>String(row.group||'').toLowerCase().includes(activeGenre));
    if(activeRegion==='local'){
      const code=$('country-select').value;const country=$('country-select').selectedOptions[0]?.text?.toLowerCase()||'';
      rows=rows.filter(row=>{const origin=String(row.country||'').toLowerCase();return origin&&(origin===code.toLowerCase()||origin===country||origin.includes(country));});
    }
    return rows;
  }
  function renderHomeTV() {
    const target=$('home-tv-grid');if(!target)return;
    const rows=homeTVRows().slice(0,6);
    if(!rows.length){target.innerHTML='<div class="empty-state">Choose a playlist to browse live channels.<button class="button primary" data-home-playlists>Choose playlist</button></div>';target.querySelector('[data-home-playlists]')?.addEventListener('click',()=>setView('playlists'));return;}
    const featured=rows[0];$('hero-title').textContent=featured.name;$('hero-subtitle').textContent=`${featured.group||'Live channel'} · Select WATCH LIVE to start.`;
    const logo=$('hero-logo');if(featured.logo){logo.src=featured.logo;logo.style.display='block';}else{logo.removeAttribute('src');logo.style.display='none';}
    target.innerHTML=rows.map(row=>`<article class="home-channel" data-home-tv="${safe(row.url)}" tabindex="0" role="button"><div class="channel-art">${row.logo?`<img src="${safe(row.logo)}" loading="lazy" alt="" onerror="this.style.display='none'">`:'<span>▣</span>'}<i>LIVE</i></div><button class="tile-star ${tvFavorites[tvKey(row)]?'is-favorite':''}" data-home-tv-star="${safe(row.url)}" aria-label="Toggle favorite">${tvFavorites[tvKey(row)]?'★':'☆'}</button><b>${safe(row.name)}</b><small>${safe(row.group||'Live television')}</small></article>`).join('');
    target.querySelectorAll('[data-home-tv]').forEach(card=>{const row=rows.find(item=>item.url===card.dataset.homeTv);card.addEventListener('click',event=>{if(event.target.closest('[data-home-tv-star]'))return;setView('tv');playTV(row);});card.addEventListener('keydown',event=>{if(event.key==='Enter'){setView('tv');playTV(row);}});});
    target.querySelectorAll('[data-home-tv-star]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const row=rows.find(item=>item.url===button.dataset.homeTvStar);if(row)toggleTVFavorite(row);}));
  }
  function renderFavorites() {
    const radioTarget=$('favorite-radio-grid'),tvTarget=$('favorite-tv-grid');if(!radioTarget||!tvTarget)return;
    const radios=Object.values(radioFavorites),tvs=Object.values(tvFavorites);
    radioTarget.innerHTML=radios.length?radios.map(station=>`<article class="favorite-row" data-fav-radio="${safe(radioKey(station))}"><span>♫</span><div><b>${safe(station.name||'Radio station')}</b><small>${safe(station.country||'Internet radio')}</small></div><button class="tile-star is-favorite" data-fav-radio-remove="${safe(radioKey(station))}" aria-label="Remove favorite">★</button></article>`).join(''):'<div class="empty-state">No radio favorites saved yet.</div>';
    tvTarget.innerHTML=tvs.length?tvs.map(station=>`<article class="favorite-row" data-fav-tv="${safe(station.url)}"><span>▣</span><div><b>${safe(station.name||'TV channel')}</b><small>${safe(station.group||'Live television')}</small></div><button class="tile-star is-favorite" data-fav-tv-remove="${safe(station.url)}" aria-label="Remove favorite">★</button></article>`).join(''):'<div class="empty-state">No TV favorites saved yet.</div>';
    radioTarget.querySelectorAll('[data-fav-radio]').forEach(card=>card.addEventListener('click',event=>{if(event.target.closest('[data-fav-radio-remove]'))return;const station=radios.find(item=>radioKey(item)===card.dataset.favRadio);if(station){setView('radio');playRadio(station);}}));
    radioTarget.querySelectorAll('[data-fav-radio-remove]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const station=radios.find(item=>radioKey(item)===button.dataset.favRadioRemove);if(station)toggleRadioFavorite(station);}));
    tvTarget.querySelectorAll('[data-fav-tv]').forEach(card=>card.addEventListener('click',event=>{if(event.target.closest('[data-fav-tv-remove]'))return;const station=tvs.find(item=>item.url===card.dataset.favTv);if(station){setView('tv');playTV(station);}}));
    tvTarget.querySelectorAll('[data-fav-tv-remove]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const station=tvs.find(item=>item.url===button.dataset.favTvRemove);if(station)toggleTVFavorite(station);}));
  }
  function renderSchedule() {
    const title=currentTV?.name||currentRadio?.name||'Nothing playing';
    const detail=currentTV?`LIVE TV · ${currentTV.group||'Live'}`:currentRadio?`${currentRadio.country||'Radio'} · LIVE`:'Choose a station or channel.';
    let favorites=currentTV?Object.values(tvFavorites):Object.values(radioFavorites);
    if(!favorites.length)favorites=currentTV?Object.values(radioFavorites):Object.values(tvFavorites);
    const active=currentTV||currentRadio;let index=favorites.findIndex(item=>currentTV?item.url===currentTV.url:currentRadio&&radioKey(item)===radioKey(currentRadio));
    const next=favorites.length?favorites[(index+1+favorites.length)%favorites.length]:null;
    const nextName=next?.name||'No next favorite';const nextMeta=next?(next.group||next.country||'Saved favorite'):'Save favorites to build your queue.';
    ['home-now-title','schedule-page-now'].forEach(id=>$(id).textContent=title);
    $('home-now-meta').textContent=detail;$('schedule-page-now-meta').textContent=detail;
    ['home-next-title','schedule-page-next'].forEach(id=>$(id).textContent=nextName);
    $('home-next-meta').textContent=nextMeta;$('schedule-page-next-meta').textContent=nextMeta;
    $('schedule-now-art').textContent=currentTV?'▣':'♫';
  }
  async function searchRadio() {
    showingRadioFavorites = false;
    const term = $('radio-search').value.trim(); const country = $('country-select').value;
    $('radio-status').textContent = 'Searching…'; $('radio-stations').innerHTML = '<div class="empty-state">Finding stations…</div>';
    try {
      let path;
      if (term) {
        const params = new URLSearchParams({name:term,limit:'100',order:'clickcount',reverse:'true',hidebroken:'true'});
        if (country !== 'all') params.set('countrycode',country);
        path = `/stations/search?${params}`;
      } else if (country !== 'all') path = `/stations/bycountrycodeexact/${encodeURIComponent(country)}?limit=100&order=clickcount&reverse=true&hidebroken=true`;
      else path = '/stations/topclick/100';
      const rows = await radioGet(path);
      radioStations = Array.isArray(rows) ? rows.filter(station => station.url_resolved || station.url) : [];
      $('radio-status').textContent = `${radioStations.length} stations`;
      renderRadio();
    } catch (error) {
      radioStations = []; renderRadio(); $('radio-status').textContent = 'Could not load stations';
      $('radio-stations').innerHTML = `<div class="empty-state">${safe(error.message)}<br>Check your connection and try again.</div>`;
    }
  }
  function playRadio(station) {
    const url = station?.url_resolved || station?.url;
    if (!url) { toast('This station has no playable stream URL.'); return; }
    stopTV();radioAudio.pause();currentRadio = station;
    radioAudio.src = url; radioAudio.volume = Number($('volume').value);
    $('playing-title').textContent = station.name || 'Internet radio';
    $('playing-subtitle').textContent = `${station.country || 'WORLDWIDE'} · LIVE${station.bitrate ? ` · ${station.bitrate} KBPS` : ''}`;
    setMediaMetadata(station.name||'Internet radio',station.country||'WORLDWIDE');syncTransport();
    const code = stationCountryCode(station);
    const name = station.country || $('country-select').selectedOptions[0]?.text || 'India';
    if (code) $('country-select').value = code;
    loadWeather(name,code); renderRadio();
    radioAudio.play().then(() => { $('radio-status').textContent = `Playing · ${station.name}`;syncTransport(); }).catch(() => {
      $('radio-status').textContent = 'Stream could not start in this browser';
      toast('This stream may be unsupported by the browser. Try another station.');syncTransport();
    });
  }
  $('radio-search-button').addEventListener('click',searchRadio);
  $('radio-search').addEventListener('keydown',event=>{if(event.key==='Enter')searchRadio();});
  $('country-select').addEventListener('change',()=>{const name=$('country-select').selectedOptions[0]?.text||'India';loadWeather(name,$('country-select').value==='all'?'':$('country-select').value);searchRadio();});
  $('load-more-radio').addEventListener('click',searchRadio);
  $('radio-favorites-button').addEventListener('click',()=>{showingRadioFavorites=!showingRadioFavorites;renderRadio();if(showingRadioFavorites)$('radio-status').textContent=`${Object.keys(radioFavorites).length} favorites`;else searchRadio();});

  function tvKey(station) { return station.url; }
  function toggleTVFavorite(station) {
    const key=tvKey(station); if(tvFavorites[key])delete tvFavorites[key];else tvFavorites[key]=station;
    if(!Object.keys(tvFavorites).length)showingTVFavorites=false;
    persist('coolmag.tv.favorites.v1',tvFavorites);updateFavoriteCounts();renderTV();updateTVStar();
  }
  function updateTVStar() {
    const button=$('tv-current-favorite'); const favorite=Boolean(currentTV&&tvFavorites[tvKey(currentTV)]);
    button.classList.toggle('is-favorite',favorite);button.textContent=favorite?'★':'♡';
    button.title=favorite?'Remove from favorites':'Add to favorites';
  }
  function playlistRow(meta,url) {
    const attr=key=>{const match=meta.match(new RegExp(`${key}="([^"]*)"`,'i'));return match?.[1]||'';};
    const name=meta.includes(',')?meta.slice(meta.indexOf(',')+1).trim():'TV channel';
    return {name,url,group:attr('group-title')||'Other',logo:attr('tvg-logo'),country:attr('tvg-country')||attr('tvg-country-code')||''};
  }
  function addCountryReservoir(reservoirs,row,limit=20) {
    const country=(row.country||'Unknown').split(/[;,]/)[0].trim().toUpperCase()||'UNKNOWN';
    let bucket=reservoirs.get(country);if(!bucket){bucket={seen:0,rows:[]};reservoirs.set(country,bucket);}
    bucket.seen++;
    if(bucket.rows.length<limit)bucket.rows.push(row);
    else {const index=Math.floor(Math.random()*bucket.seen);if(index<limit)bucket.rows[index]=row;}
  }
  function chooseDiverseSample(reservoirs,limit=20) {
    const groups=[...reservoirs.values()].map(bucket=>bucket.rows);
    for(let i=groups.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[groups[i],groups[j]]=[groups[j],groups[i]];}
    const result=[];
    for(let offset=0;result.length<limit;offset++){
      let added=false;
      for(const rows of groups){if(rows[offset]){result.push(rows[offset]);added=true;if(result.length===limit)break;}}
      if(!added)break;
    }
    for(let i=result.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[result[i],result[j]]=[result[j],result[i]];}
    return result;
  }
  async function samplePlaylist(response,limit=20,onProgress=()=>{}) {
    const reservoirs=new Map();let meta='',buffer='',scanned=0,chunks=0;
    const consume=line=>{
      line=line.trim();
      if(line.startsWith('#EXTINF')){meta=line;return;}
      if(!line||line.startsWith('#')||!meta)return;
      addCountryReservoir(reservoirs,playlistRow(meta,line),limit);scanned++;meta='';
    };
    if(!response.body?.getReader){
      const text=await response.text();
      for(const line of text.split(/\r?\n/))consume(line);
      onProgress(scanned);
      return chooseDiverseSample(reservoirs,limit);
    }
    const reader=response.body.getReader(),decoder=new TextDecoder();
    while(true){
      const {value,done}=await reader.read();
      buffer+=decoder.decode(value||new Uint8Array(),{stream:!done});
      const lines=buffer.split(/\r?\n/);buffer=lines.pop()||'';
      for(const line of lines)consume(line);
      if(done){if(buffer)consume(buffer);break;}
      if(++chunks%16===0){onProgress(scanned);await new Promise(resolve=>setTimeout(resolve,0));}
    }
    onProgress(scanned);
    return chooseDiverseSample(reservoirs,limit);
  }
  async function loadTV() {
    const source=$('tv-source').value;const file=source==='index'?'index.m3u':`${source.toLowerCase()}.m3u`;
    tvLoadController?.abort();const controller=new AbortController();tvLoadController=controller;
    const button=$('load-tv');button.disabled=true;button.textContent='Loading…';
    tvStations=[];showingTVFavorites=Object.keys(tvFavorites).length>0;
    if(showingTVFavorites)renderTV();else $('tv-channels').innerHTML='<div class="empty-state">Scanning playlist and selecting 20 random channels across countries…</div>';
    $('tv-channel-count').textContent=showingTVFavorites?Object.keys(tvFavorites).length.toLocaleString():'…';renderHomeTV();
    try{
      const response=await fetch(IPTV_BASE+file,{cache:'no-cache',signal:controller.signal});if(!response.ok)throw new Error(`Playlist could not be fetched (${response.status}).`);
      tvStations=await samplePlaylist(response,20,count=>{if(!showingTVFavorites)$('tv-channel-count').textContent=count?`${count.toLocaleString()} scanned`:'…';});
      renderTV();toast(`Loaded ${tvStations.length} random channels from across the playlist`);
    }catch(error){if(error.name==='AbortError')return;tvStations=[];$('tv-channel-count').textContent='0';$('tv-channels').innerHTML=`<div class="empty-state">${safe(error.message)} Check the connection or select another playlist.</div>`;renderHomeTV();}
    finally{if(tvLoadController===controller){tvLoadController=null;button.disabled=false;button.textContent='Load channels';}}
  }
  function filteredTV() {
    const rows=showingTVFavorites?Object.values(tvFavorites):tvStations;const term=$('tv-search').value.trim().toLowerCase();
    const filtered=rows.filter(row=>!term||String(row.name||'').toLowerCase().includes(term)||String(row.group||'').toLowerCase().includes(term));
    return showingTVFavorites?filtered:filtered.slice(0,120);
  }
  function renderTV() {
    const rows=filteredTV();const list=$('tv-channels');
    const favoritesFirst=showingTVFavorites&&Object.keys(tvFavorites).length>0;
    $('tv-channel-count').textContent=rows.length.toLocaleString();
    $('tv-view').classList.toggle('favorites-first',favoritesFirst&&!currentTV);
    $('tv-favorites-button').classList.toggle('active',showingTVFavorites);
    $('tv-favorites-button').innerHTML=`${showingTVFavorites?'★ Your favorites':'♡ Favorites'} <span class="count-pill" id="tv-favorite-count">${Object.keys(tvFavorites).length}</span>`;
    $('tv-list-eyebrow').textContent=showingTVFavorites?'YOUR TV FAVORITES':'CHANNEL GUIDE';
    $('tv-list-title').textContent=showingTVFavorites?'Favorite channels':'Live TV';
    if(!rows.length){list.innerHTML=showingTVFavorites?'<div class="empty-state">No TV favorites saved yet. Star channels to keep them here.</div>':'<div class="empty-state">No matching channels. Choose a playlist or adjust your search.</div>';renderHomeTV();renderFavorites();return;}
    list.innerHTML=rows.map(row=>`<article class="home-channel tv-channel ${currentTV&&currentTV.url===row.url?'active':''}" data-tv-url="${safe(row.url)}" tabindex="0" role="button"><div class="channel-art">${row.logo?`<img src="${safe(row.logo)}" loading="lazy" alt="" onerror="this.style.display='none'">`:'<span>▣</span>'}<i>LIVE</i></div><button class="tile-star ${tvFavorites[tvKey(row)]?'is-favorite':''}" data-tv-star="${safe(row.url)}" aria-label="Toggle favorite">${tvFavorites[tvKey(row)]?'★':'☆'}</button><b>${safe(row.name)}</b><small>${safe(row.group||'Live television')}</small></article>`).join('');
    list.querySelectorAll('.tv-channel').forEach(item=>{const row=rows.find(candidate=>candidate.url===item.dataset.tvUrl);item.addEventListener('click',event=>{if(event.target.closest('[data-tv-star]'))return;playTV(row);});item.addEventListener('keydown',event=>{if(event.key==='Enter'){playTV(row);}});});
    list.querySelectorAll('[data-tv-star]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const row=rows.find(candidate=>candidate.url===button.dataset.tvStar);if(row)toggleTVFavorite(row);}));
    renderHomeTV();renderFavorites();renderSchedule();
  }
  function requestMobileTVLandscape() {
    if (!window.matchMedia('(max-width:760px)').matches) return;
    const stage=$('video-stage');
    if (document.fullscreenElement===stage) return;
    if (typeof stage.requestFullscreen!=='function') {
      toast('Turn your phone sideways for the landscape TV view.');
      return;
    }
    stage.requestFullscreen().then(()=>{
      if (screen.orientation?.lock) {
        return screen.orientation.lock('landscape').catch(()=>toast('Turn your phone sideways for landscape TV.'));
      }
      toast('Turn your phone sideways for the landscape TV view.');
    }).catch(()=>toast('Turn your phone sideways for the landscape TV view.'));
  }
  function toggleTVFullView() {
    const stage=$('video-stage');
    if(!currentTV){toast('Start a TV channel first.');return;}
    if(document.fullscreenElement===stage){document.exitFullscreen?.();return;}
    if(typeof stage.requestFullscreen!=='function'){toast('Use your browser video full-screen control, then turn your phone sideways.');return;}
    stage.requestFullscreen().then(()=>{
      if(window.matchMedia('(max-width:760px)').matches&&screen.orientation?.lock){
        return screen.orientation.lock('landscape').catch(()=>toast('Turn your phone sideways for landscape TV.'));
      }
    }).catch(()=>toast('Full view is blocked by this browser. Turn your phone sideways to fit the TV screen.'));
  }
  function playTV(station) {
    if(!station?.url)return;requestMobileTVLandscape();radioAudio.pause();radioAudio.removeAttribute('src');radioAudio.load();currentRadio=null;currentTV=station;
    if(hls){hls.destroy();hls=null;}tvVideo.pause();tvVideo.removeAttribute('src');tvVideo.load();
    $('video-stage').querySelector('.video-placeholder').classList.add('hidden');$('tv-now-playing').textContent=station.name;
    $('playing-title').textContent=station.name;$('playing-subtitle').textContent=`LIVE TV · ${station.group}`;
    setMediaMetadata(station.name,station.group||'LIVE TV');syncTransport();
    const isHls=/\.m3u8($|\?)/i.test(station.url);
    if(isHls&&window.Hls&&Hls.isSupported()){
      hls=new Hls({enableWorker:true,lowLatencyMode:false,maxBufferLength:18});hls.loadSource(station.url);hls.attachMedia(tvVideo);
      hls.on(Hls.Events.MANIFEST_PARSED,()=>tvVideo.play().then(syncTransport).catch(()=>toast('Press play on the video to start this channel.')));
      hls.on(Hls.Events.ERROR,(_event,data)=>{if(data.fatal)toast('This channel stream is unavailable or blocked by its host.');});
    }else{tvVideo.src=station.url;tvVideo.play().then(syncTransport).catch(()=>toast('This stream may not be supported in this browser.'));}
    currentRadio=null;renderTV();updateTVStar();
  }
  function stopTV(){if(hls){hls.destroy();hls=null;}if(tvVideo){tvVideo.pause();tvVideo.removeAttribute('src');tvVideo.load();}currentTV=null;if($('tv-now-playing'))$('tv-now-playing').textContent='No channel selected';if($('video-stage'))$('video-stage').querySelector('.video-placeholder').classList.remove('hidden');if($('tv-current-favorite'))updateTVStar();syncTransport();}
  $('load-tv').addEventListener('click',loadTV);$('tv-search').addEventListener('input',renderTV);
  $('tv-source').addEventListener('change',loadTV);
  $('tv-fullscreen').addEventListener('click',toggleTVFullView);
  $('tv-favorites-button').addEventListener('click',()=>{if(!Object.keys(tvFavorites).length){toast('Star a TV channel to save your first favorite.');return;}tvFilterTouched=true;showingTVFavorites=!showingTVFavorites;renderTV();if(showingTVFavorites)toast(`${Object.keys(tvFavorites).length} saved TV favorites`);});
  $('tv-current-favorite').addEventListener('click',()=>{if(currentTV)toggleTVFavorite(currentTV);});
  $('pip-toggle').addEventListener('click',async()=>{if(!currentTV){toast('Start a TV channel first.');return;}try{if(document.pictureInPictureElement)await document.exitPictureInPicture();else if(tvVideo.requestPictureInPicture)await tvVideo.requestPictureInPicture();else toast('Picture in picture is not supported by this browser.');}catch{toast('Picture in picture is unavailable for this stream.');}});
  $('cast-toggle').addEventListener('click',async()=>{if(!currentTV){toast('Start a TV channel first.');return;}try{if(tvVideo.remote?.prompt)await tvVideo.remote.prompt();else if(tvVideo.webkitShowPlaybackTargetPicker)tvVideo.webkitShowPlaybackTargetPicker();else toast('Casting is not supported by this browser.');}catch{toast('No cast device is available.');}});
  $('shuffle-toggle').addEventListener('click',()=>{shuffleFavorites=!shuffleFavorites;favoriteHistory.length=0;syncTransport();});
  $('repeat-toggle').addEventListener('click',()=>{repeatCurrent=!repeatCurrent;radioAudio.loop=repeatCurrent;tvVideo.loop=repeatCurrent;syncTransport();});
  $('previous-favorite').addEventListener('click',()=>stepFavorite(-1));
  $('next-favorite').addEventListener('click',()=>stepFavorite(1));
  $('seek-back').addEventListener('click',()=>seekActive(-10));
  $('seek-forward').addEventListener('click',()=>seekActive(10));
  $('play-pause').addEventListener('click',playPauseActive);
  [radioAudio,tvVideo].forEach(media=>['play','pause','progress','loadedmetadata','durationchange','seeked','emptied','timeupdate'].forEach(event=>media.addEventListener(event,syncTransport)));
  setupMediaSession();syncTransport();
  $('volume').addEventListener('input',()=>{const value=Number($('volume').value);radioAudio.volume=value;tvVideo.volume=value;$('volume-label').textContent=`${Math.round(value*100)}%`;});
  $('add-stream').addEventListener('click',()=>{const url=prompt('Paste a direct radio stream URL (https:// or http://):');if(!url)return;const clean=url.trim();if(!/^https?:\/\//i.test(clean)){toast('Please enter a valid HTTP or HTTPS stream URL.');return;}const name=prompt('Station name:','My station')?.trim()||'My station';const station={stationuuid:`custom:${clean}`,name,url:clean,url_resolved:clean,country:'Custom stream',tags:'Added by you'};radioFavorites[radioKey(station)]=station;persist('coolmag.radio.favorites.v1',radioFavorites);updateFavoriteCounts();toast('Station saved to your favorites.');if(showingRadioFavorites)renderRadio();});

  function renderNews(){
    $('news-grid').innerHTML=NEWS.map(item=>`<a class="news-card" href="${safe(item.url)}" target="_blank" rel="noopener noreferrer"><div class="news-card-top"><span class="news-logo">${safe(item.initials)}</span><span class="eyebrow">${safe(item.region)}</span></div><div><h3>${safe(item.name)}</h3><p>${safe(item.detail)}</p></div><span class="news-open">OPEN PUBLISHER ↗</span></a>`).join('');
  }
  function updateClock(){try{$('local-time').textContent=new Intl.DateTimeFormat('en-GB',{timeZone:selectedTimezone,hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date());$('local-date').textContent=new Intl.DateTimeFormat('en',{timeZone:selectedTimezone,weekday:'short',day:'2-digit',month:'short'}).format(new Date()).toUpperCase();}catch{$('local-time').textContent=new Date().toLocaleTimeString();}}

  renderNews();updateFavoriteCounts();updateClock();setInterval(updateClock,1000);loadSharedFavorites();
  loadCountries().then(()=>{const name=$('country-select').selectedOptions[0]?.text||'India';loadWeather(name,$('country-select').value);searchRadio();});
})();
