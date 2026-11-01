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
  let currentRadio = null;
  let currentTV = null;
  let hls = null;
  let selectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  let toastTimer = null;

  const readStore = (key) => {
    try { const value = JSON.parse(localStorage.getItem(key) || '{}'); return value && typeof value === 'object' ? value : {}; }
    catch { return {}; }
  };
  const radioFavorites = readStore('coolmag.radio.favorites.v1');
  const tvFavorites = readStore('coolmag.tv.favorites.v1');
  const persist = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { toast('This browser could not save favorites.'); } };
  const toast = (message) => {
    const node = $('toast'); node.textContent = message; node.classList.add('show');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => node.classList.remove('show'), 2600);
  };

  function setView(view) {
    document.querySelectorAll('.nav-button').forEach(button => button.classList.toggle('active', button.dataset.view === view));
    document.querySelectorAll('.view-panel').forEach(panel => panel.classList.toggle('active', panel.id === `${view}-view`));
    const titles = {radio:['World Radio','Explore stations around the world and tune in instantly.'],tv:['Live TV','Browse public IPTV playlists and play compatible streams.'],news:['News & Magazines','Open trusted newsrooms and regional publications.']};
    $('section-title').textContent = titles[view][0]; $('section-subtitle').textContent = titles[view][1];
    if (view === 'tv') { radioAudio.pause(); $('play-pause').textContent = '▶'; }
    if (view === 'radio') stopTV();
  }
  document.querySelectorAll('.nav-button').forEach(button => button.addEventListener('click', () => { setView(button.dataset.view); document.querySelector('.main-nav').classList.remove('open'); }));
  $('menu-button').addEventListener('click', () => document.querySelector('.main-nav').classList.toggle('open'));

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
    if (showingTVFavorites) renderTV();
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
    } catch {
      $('weather-summary').textContent = 'Live weather is unavailable right now.';
      showOrigin(countryName,countryCode);
    }
  }
  function renderRadio() {
    const target = $('radio-stations');
    const rows = (showingRadioFavorites ? Object.values(radioFavorites) : radioStations).slice(0,100);
    $('station-list-title').textContent = showingRadioFavorites ? 'Your radio favorites' : `${$('country-select').selectedOptions[0]?.text || 'Worldwide'} stations`;
    if (!rows.length) { target.innerHTML = '<div class="empty-state">No stations found. Try another search or country.</div>'; return; }
    target.innerHTML = rows.map(station => {
      const key = safe(radioKey(station)); const favorite = Boolean(radioFavorites[radioKey(station)]);
      const playing = currentRadio && radioKey(currentRadio) === radioKey(station);
      const tags = (station.tags || '').split(',').map(v => v.trim()).filter(Boolean).slice(0,2).join(' · ');
      const meta = [station.country || 'Internet radio', tags || station.codec || 'Live stream'].filter(Boolean).join(' · ');
      return `<article class="station-card ${playing?'playing':''}" data-radio-key="${key}" tabindex="0" role="button" aria-label="Play ${safe(station.name)}"><button class="star-button ${favorite?'is-favorite':''}" data-radio-star="${key}" title="${favorite?'Remove':'Add'} favorite">${favorite?'★':'☆'}</button><div class="station-icon">${playing?'♫':'◉'}</div><h3>${safe(station.name || 'Unnamed station')}</h3><p>${safe(meta)}</p></article>`;
    }).join('');
    target.querySelectorAll('.station-card').forEach(card => {
      const station = rows.find(row => radioKey(row) === card.dataset.radioKey);
      card.addEventListener('click', event => { if (event.target.closest('[data-radio-star]')) return; playRadio(station); });
      card.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); playRadio(station); } });
    });
    target.querySelectorAll('[data-radio-star]').forEach(button => button.addEventListener('click', event => { event.stopPropagation(); const station = rows.find(row => radioKey(row) === button.dataset.radioStar); if (station) toggleRadioFavorite(station); }));
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
    stopTV(); currentRadio = station;
    radioAudio.src = url; radioAudio.volume = Number($('volume').value);
    $('playing-title').textContent = station.name || 'Internet radio';
    $('playing-subtitle').textContent = `${station.country || 'WORLDWIDE'} · LIVE${station.bitrate ? ` · ${station.bitrate} KBPS` : ''}`;
    $('play-pause').textContent = 'Ⅱ';
    const code = stationCountryCode(station);
    const name = station.country || $('country-select').selectedOptions[0]?.text || 'India';
    if (code) $('country-select').value = code;
    loadWeather(name,code); renderRadio();
    radioAudio.play().then(() => { $('radio-status').textContent = `Playing · ${station.name}`; }).catch(() => {
      $('radio-status').textContent = 'Stream could not start in this browser';
      toast('This stream may be unsupported by the browser. Try another station.'); $('play-pause').textContent='▶';
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
    persist('coolmag.tv.favorites.v1',tvFavorites);updateFavoriteCounts();renderTV();updateTVStar();
  }
  function updateTVStar() {
    const button=$('tv-current-favorite'); const favorite=Boolean(currentTV&&tvFavorites[tvKey(currentTV)]);
    button.classList.toggle('is-favorite',favorite);button.textContent=favorite?'★':'♡';
    button.title=favorite?'Remove from favorites':'Add to favorites';
  }
  function parseM3U(text) {
    const rows=[];let meta='';
    for(const line of text.split(/\r?\n/)){
      if(line.startsWith('#EXTINF')){meta=line;continue;}
      const url=line.trim();if(!url||url.startsWith('#')||!meta)continue;
      const name=meta.includes(',')?meta.slice(meta.indexOf(',')+1).trim():'TV channel';
      const attr=(key)=>{const match=meta.match(new RegExp(`${key}="([^"]*)"`,'i'));return match?.[1]||'';};
      rows.push({name,url,group:attr('group-title')||'Other',logo:attr('tvg-logo'),country:attr('tvg-country')});meta='';
      if(rows.length>=15000)break;
    }
    return rows;
  }
  async function loadTV() {
    const source=$('tv-source').value;const file=source==='index'?'index.m3u':`${source.toLowerCase()}.m3u`;
    $('tv-channels').innerHTML='<div class="empty-state">Loading playlist…</div>';$('tv-channel-count').textContent='…';
    try{
      const response=await fetch(IPTV_BASE+file,{cache:'no-cache'});if(!response.ok)throw new Error(`Playlist could not be fetched (${response.status}).`);
      const text=await response.text();tvStations=parseM3U(text);showingTVFavorites=false;renderTV();
      $('tv-channel-count').textContent=tvStations.length.toLocaleString();toast(`Loaded ${tvStations.length.toLocaleString()} channels`);
    }catch(error){$('tv-channel-count').textContent='0';$('tv-channels').innerHTML=`<div class="empty-state">${safe(error.message)} Check the connection or select another playlist.</div>`;}
  }
  function filteredTV() {
    const rows=showingTVFavorites?Object.values(tvFavorites):tvStations;const term=$('tv-search').value.trim().toLowerCase();
    return rows.filter(row=>!term||row.name.toLowerCase().includes(term)||row.group.toLowerCase().includes(term)).slice(0,120);
  }
  function renderTV() {
    const rows=filteredTV();const list=$('tv-channels');
    if(!rows.length){list.innerHTML='<div class="empty-state">No matching channels. Try another search or playlist.</div>';return;}
    list.innerHTML=rows.map(row=>`<div class="channel-row ${currentTV&&currentTV.url===row.url?'active':''}" data-tv-url="${safe(row.url)}" tabindex="0" role="button">${row.logo?`<img class="channel-logo" loading="lazy" src="${safe(row.logo)}" alt="" onerror="this.style.display='none'">`:'<span class="channel-logo channel-logo-fallback">▣</span>'}<div class="channel-title"><b>${safe(row.name)}</b><small>${safe(row.group)}</small></div><button class="star-button ${tvFavorites[tvKey(row)]?'is-favorite':''}" data-tv-star="${safe(row.url)}" aria-label="Toggle favorite">${tvFavorites[tvKey(row)]?'★':'☆'}</button></div>`).join('');
    list.querySelectorAll('.channel-row').forEach(item=>{const row=rows.find(candidate=>candidate.url===item.dataset.tvUrl);item.addEventListener('click',event=>{if(event.target.closest('[data-tv-star]'))return;playTV(row);});item.addEventListener('keydown',event=>{if(event.key==='Enter'){playTV(row);}});});
    list.querySelectorAll('[data-tv-star]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const row=rows.find(candidate=>candidate.url===button.dataset.tvStar);if(row)toggleTVFavorite(row);}));
  }
  function playTV(station) {
    if(!station?.url)return;radioAudio.pause();$('play-pause').textContent='▶';currentTV=station;
    if(hls){hls.destroy();hls=null;}tvVideo.pause();tvVideo.removeAttribute('src');tvVideo.load();
    $('video-stage').querySelector('.video-placeholder').classList.add('hidden');$('tv-now-playing').textContent=station.name;
    $('playing-title').textContent=station.name;$('playing-subtitle').textContent=`LIVE TV · ${station.group}`;
    const isHls=/\.m3u8($|\?)/i.test(station.url);
    if(isHls&&window.Hls&&Hls.isSupported()){
      hls=new Hls({enableWorker:true,lowLatencyMode:false,maxBufferLength:18});hls.loadSource(station.url);hls.attachMedia(tvVideo);
      hls.on(Hls.Events.MANIFEST_PARSED,()=>tvVideo.play().catch(()=>toast('Press play on the video to start this channel.')));
      hls.on(Hls.Events.ERROR,(_event,data)=>{if(data.fatal)toast('This channel stream is unavailable or blocked by its host.');});
    }else{tvVideo.src=station.url;tvVideo.play().catch(()=>toast('This stream may not be supported in this browser.'));}
    currentRadio=null;renderTV();updateTVStar();
  }
  function stopTV(){if(hls){hls.destroy();hls=null;}if(tvVideo){tvVideo.pause();tvVideo.removeAttribute('src');tvVideo.load();}currentTV=null;if($('tv-now-playing'))$('tv-now-playing').textContent='No channel selected';if($('video-stage'))$('video-stage').querySelector('.video-placeholder').classList.remove('hidden');if($('tv-current-favorite'))updateTVStar();}
  $('load-tv').addEventListener('click',loadTV);$('tv-search').addEventListener('input',renderTV);
  $('tv-source').addEventListener('change',()=>{if(tvStations.length)loadTV();});
  $('tv-favorites-button').addEventListener('click',()=>{showingTVFavorites=!showingTVFavorites;renderTV();if(showingTVFavorites)toast(`${Object.keys(tvFavorites).length} saved TV favorites`);});
  $('tv-current-favorite').addEventListener('click',()=>{if(currentTV)toggleTVFavorite(currentTV);});

  $('play-pause').addEventListener('click',()=>{if(!radioAudio.src){toast('Choose a radio station first.');return;}if(radioAudio.paused){radioAudio.play().then(()=>$('play-pause').textContent='Ⅱ').catch(()=>toast('Could not play this stream.'));}else{radioAudio.pause();$('play-pause').textContent='▶';}});
  $('stop-audio').addEventListener('click',()=>{radioAudio.pause();radioAudio.removeAttribute('src');radioAudio.load();$('play-pause').textContent='▶';if(currentRadio){$('playing-title').textContent='Playback stopped';$('playing-subtitle').textContent='Choose a station to continue';}currentRadio=null;renderRadio();});
  $('volume').addEventListener('input',()=>{const value=Number($('volume').value);radioAudio.volume=value;tvVideo.volume=value;$('volume-label').textContent=`${Math.round(value*100)}%`;});
  $('add-stream').addEventListener('click',()=>{const url=prompt('Paste a direct radio stream URL (https:// or http://):');if(!url)return;const clean=url.trim();if(!/^https?:\/\//i.test(clean)){toast('Please enter a valid HTTP or HTTPS stream URL.');return;}const name=prompt('Station name:','My station')?.trim()||'My station';const station={stationuuid:`custom:${clean}`,name,url:clean,url_resolved:clean,country:'Custom stream',tags:'Added by you'};radioFavorites[radioKey(station)]=station;persist('coolmag.radio.favorites.v1',radioFavorites);updateFavoriteCounts();toast('Station saved to your favorites.');if(showingRadioFavorites)renderRadio();});

  function renderNews(){
    $('news-grid').innerHTML=NEWS.map(item=>`<a class="news-card" href="${safe(item.url)}" target="_blank" rel="noopener noreferrer"><div class="news-card-top"><span class="news-logo">${safe(item.initials)}</span><span class="eyebrow">${safe(item.region)}</span></div><div><h3>${safe(item.name)}</h3><p>${safe(item.detail)}</p></div><span class="news-open">OPEN PUBLISHER ↗</span></a>`).join('');
  }
  function updateClock(){try{$('local-time').textContent=new Intl.DateTimeFormat('en-GB',{timeZone:selectedTimezone,hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date());$('local-date').textContent=new Intl.DateTimeFormat('en',{timeZone:selectedTimezone,weekday:'short',day:'2-digit',month:'short'}).format(new Date()).toUpperCase();}catch{$('local-time').textContent=new Date().toLocaleTimeString();}}

  renderNews();updateFavoriteCounts();updateClock();setInterval(updateClock,1000);loadSharedFavorites();
  loadCountries().then(()=>{const name=$('country-select').selectedOptions[0]?.text||'India';loadWeather(name,$('country-select').value);searchRadio();});
})();
