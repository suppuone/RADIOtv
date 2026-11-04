(() => {
  'use strict';

  const APP_VERSION = '4.1.2';

  const RADIO_API = [
    'https://de1.api.radio-browser.info/json',
    'https://nl1.api.radio-browser.info/json',
    'https://at1.api.radio-browser.info/json'
  ];
  const IPTV_BASE = 'https://iptv-org.github.io/iptv/';
  const CURATED_RADIO = [
    {stationuuid:'98adecf7-2683-4408-9be7-02d3f9098eb8',name:'BBC World Service',url:'https://as-hls-ww-live.akamaized.net/pool_87948813/live/ww/bbc_world_service/bbc_world_service.isml/bbc_world_service-audio=96000.norewind.m3u8',url_resolved:'https://as-hls-ww-live.akamaized.net/pool_87948813/live/ww/bbc_world_service/bbc_world_service.isml/bbc_world_service-audio=96000.norewind.m3u8',country:'United Kingdom',countrycode:'GB',language:'English',codec:'AAC',bitrate:96,tags:'News, World'},
    {stationuuid:'bbc:bbc_radio_fourfm',name:'BBC Radio 4',url:'https://as-hls-ww-live.akamaized.net/pool_55057080/live/ww/bbc_radio_fourfm/bbc_radio_fourfm.isml/bbc_radio_fourfm-audio=96000.norewind.m3u8',url_resolved:'https://as-hls-ww-live.akamaized.net/pool_55057080/live/ww/bbc_radio_fourfm/bbc_radio_fourfm.isml/bbc_radio_fourfm-audio=96000.norewind.m3u8',country:'United Kingdom',countrycode:'GB',language:'English',codec:'AAC',bitrate:96,tags:'News, Speech'},
    {stationuuid:'bbc:bbc_radio_five_live',name:'BBC Radio 5 Live',url:'https://as-hls-ww-live.akamaized.net/pool_89021708/live/ww/bbc_radio_five_live/bbc_radio_five_live.isml/bbc_radio_five_live-audio=96000.norewind.m3u8',url_resolved:'https://as-hls-ww-live.akamaized.net/pool_89021708/live/ww/bbc_radio_five_live/bbc_radio_five_live.isml/bbc_radio_five_live-audio=96000.norewind.m3u8',country:'United Kingdom',countrycode:'GB',language:'English',codec:'AAC',bitrate:96,tags:'News, Sport'},
    {stationuuid:'7dd71b85-139b-4362-81b1-4206133a517c',name:'Hindi Gold Radio',url:'https://azuracast.vibesounds.in:8010/radio.mp3',url_resolved:'https://azuracast.vibesounds.in:8010/radio.mp3',country:'India',countrycode:'IN',language:'Hindi',codec:'MP3',bitrate:128,tags:'Music'},
    {stationuuid:'e75a90d7-b812-49f2-a6be-a3585977ee12',name:'89.4 Tamil FM',url:'https://centova.aarenworld.com/proxy/894tamilfm/stream',url_resolved:'https://centova.aarenworld.com/proxy/894tamilfm/stream',country:'India',countrycode:'IN',language:'Tamil',codec:'MP3',bitrate:128,tags:'Music'},
    {stationuuid:'724e92cd-9d57-4fef-b7e6-adad9fcc270d',name:'Kantipur FM',url:'https://radio-broadcast.ekantipur.com/stream',url_resolved:'https://radio-broadcast.ekantipur.com/stream',country:'Nepal',countrycode:'NP',language:'Nepali',codec:'MP3',bitrate:128,tags:'News, Music'},
    {stationuuid:'4a1caf35-e380-4b0d-8a7b-43c46958cfe5',name:'Bhutan Broadcasting Service',url:'https://radio.bbs.bt/dz-ch',url_resolved:'https://radio.bbs.bt/dz-ch',country:'Bhutan',countrycode:'BT',language:'Dzongkha',codec:'MP3',bitrate:128,tags:'Public Radio'},
    {stationuuid:'akashvani:240',name:'Akashvani Gangtok',url:'https://radio.wavespb.com/live/a2fa73a479445b3d/a2fa73a479445b3d.m3u8',url_resolved:'https://radio.wavespb.com/live/a2fa73a479445b3d/a2fa73a479445b3d.m3u8',country:'India',countrycode:'IN',language:'Nepali, Hindi',codec:'HLS',bitrate:0,tags:'Public Radio'},
    {stationuuid:'akashvani:1',name:'Vividh Bharati',url:'https://radio.wavespb.com/live/146ed6ec6dea5a24/146ed6ec6dea5a24.m3u8',url_resolved:'https://radio.wavespb.com/live/146ed6ec6dea5a24/146ed6ec6dea5a24.m3u8',country:'India',countrycode:'IN',language:'Hindi',codec:'HLS',bitrate:0,tags:'Public Radio, Music'},
    {stationuuid:'mediacorp:938NOWAAC',name:'CNA938',url:'https://playerservices.streamtheworld.com/api/livestream-redirect/938NOWAAC.aac',url_resolved:'https://playerservices.streamtheworld.com/api/livestream-redirect/938NOWAAC.aac',country:'Singapore',countrycode:'SG',language:'English',codec:'AAC',bitrate:0,tags:'News, Talk'},
    {stationuuid:'mediacorp:SYMPHONY924AAC',name:'Symphony 924',url:'https://playerservices.streamtheworld.com/api/livestream-redirect/SYMPHONY924AAC.aac',url_resolved:'https://playerservices.streamtheworld.com/api/livestream-redirect/SYMPHONY924AAC.aac',country:'Singapore',countrycode:'SG',language:'English',codec:'AAC',bitrate:0,tags:'Classical'},
    {stationuuid:'55d2c0f1-0853-483e-969a-8de9052e952c',name:'Outlaw – Country Music Radio',url:'https://r.bgp.rodeo/listen/outlaw/radio.mp3',url_resolved:'https://r.bgp.rodeo/listen/outlaw/radio.mp3',country:'United States',countrycode:'US',language:'English',codec:'MP3',bitrate:320,tags:'Country Music'}
  ];
  const CURATED_TV = [
    {name:'DW English',group:'WORLD NEWS · HD',country:'Germany',url:'https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/master.m3u8',logo:'https://i.imgur.com/8MRNFb9.png'},
    {name:'Al Jazeera English (1080p)',group:'WORLD NEWS · 1080p',country:'Qatar',url:'https://live-hls-apps-aje-fa.getaj.net/AJE/index.m3u8',logo:'https://i.imgur.com/7bRVpnu.png'},
    {name:'France 24 English (1080p)',group:'WORLD NEWS · 1080p',country:'France',url:'https://amg00106-france24-france24-samsunguk-qvpp8.amagi.tv/playlist/amg00106-france24-france24-samsunguk/playlist.m3u8',logo:'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/France_24_logo_%282013%29.svg/512px-France_24_logo_%282013%29.svg.png'},
    {name:'NHK World-Japan',group:'WORLD NEWS · HD',country:'Japan',url:'https://nhk.lls.pbs.org/index.m3u8',logo:'https://jiotvimages.cdn.jio.com/dare_images/images/NHK_World_Japan.png'},
    {name:'ABC News (720p)',group:'WORLD NEWS · 720p',country:'United States',url:'https://abc-news-dmd-streams-1.akamaized.net/out/v1/701126012d044971b3fa89406a440133/index.m3u8',logo:'https://i.imgur.com/BrW7gk8.png'},
    {name:'TRT World',group:'WORLD NEWS · HD',country:'Türkiye',url:'https://dash2.antik.sk/live/test_trt_world_atktv/playlist.m3u8',logo:'https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/TRT_World.svg/512px-TRT_World.svg.png'},
    {name:'DD News (1080p)',group:'INDIA NEWS · 1080p',country:'India',url:'https://mumbai-edge.smartplaytv.in/DDNews/index.m3u8',logo:'https://ltsk-cdn.s3.eu-west-1.amazonaws.com/jumpstart/Temp_Live/cdn/HLS/Channel/transparentImages/DD%20News%20HD.png'},
    {name:'Thanthi TV (576p)',group:'TAMIL NEWS · 576p',country:'India',url:'https://streams.tangotv.in/THANTHITV/ORIGIN/index.m3u8',logo:'https://dtil.tmsimg.com/assets/s144000_ld_h15_aa.png?lock=720x540'},
    {name:'Kantipur TV',group:'NEPAL · HD',country:'Nepal',url:'https://ktvhdsg.ekantipur.com:8443/high_quality_85840165/hd/kantipurtv/hd_1080/chunks.m3u8',logo:'https://i.imgur.com/HEVo2Gc.png'},
    {name:'Create (PBS)',group:'EDUCATION · HD',country:'United States',url:'https://create.lls.pbs.org/index.m3u8',logo:'https://i.imgur.com/OIJTECP.png'}
  ];
  const COUNTRY_CODES='AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS XK YE YT ZA ZM ZW'.split(' ');
  // Add the Supabase project URL and publishable key to enable the live presence count.
  const PRESENCE_CONFIG = {url:'',publishableKey:''};
  const HOME_BBC = {
    name:'BBC News South Asia (720p)',
    group:'News · United Kingdom',
    country:'United Kingdom',
    url:'https://mumbai-edge.smartplaytv.in/BBCNews/index.m3u8',
    logo:'https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/BBC_News_2022_%28Alt%29.svg/512px-BBC_News_2022_%28Alt%29.svg.png'
  };
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
  function normalizeImageURL(value){
    try{
      const image=new URL(String(value||'').trim());if(image.protocol!=='https:')return '';
      if(image.hostname.toLowerCase()==='github.com'){
        const parts=image.pathname.split('/').filter(Boolean),marker=parts.indexOf('blob'),rawMarker=parts.indexOf('raw');
        const index=marker>=0?marker:rawMarker;
        if(index===2&&parts.length>4){image.hostname='raw.githubusercontent.com';image.pathname='/'+[parts[0],parts[1],...parts.slice(3)].join('/');image.search='';image.hash='';}
      }
      return image.href;
    }catch{return '';}
  }
  function radioImageCandidates(station){
    return [...new Set([station.favicon,station.logo,station.image,station.artwork].map(value=>{
      if(!value)return '';
      const text=String(value).trim();
      if(/^http:\/\//i.test(text))return normalizeImageURL(text.replace(/^http:/i,'https:'));
      return normalizeImageURL(text);
    }).filter(Boolean))];
  }
  function radioArtwork(station){
    const candidates=radioImageCandidates(station);
    const initials=safe((station.name||'FM').trim().slice(0,2).toUpperCase());
    return candidates.length?`<img data-radio-art data-radio-fallbacks="${safe(JSON.stringify(candidates.slice(1)))}" data-radio-initials="${initials}" src="${safe(candidates[0])}" loading="lazy" decoding="async" alt="${safe(station.name||'Radio station')} logo">`:`<span class="radio-art-fallback">${initials}</span>`;
  }
  function bindRadioArtwork(container){
    container.querySelectorAll('img[data-radio-art]').forEach(image=>image.addEventListener('error',()=>{
      let fallbacks=[];try{fallbacks=JSON.parse(image.dataset.radioFallbacks||'[]');}catch{}
      const next=fallbacks.shift();
      if(next){image.dataset.radioFallbacks=JSON.stringify(fallbacks);image.src=next;return;}
      const fallback=document.createElement('span');fallback.className='radio-art-fallback';fallback.textContent=image.dataset.radioInitials||'♫';image.replaceWith(fallback);
    }));
  }
  const PLAYER_ICONS={
    shuffle:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M3 7h2.5a5 5 0 0 1 3.7 1.7l5.6 6.6a5 5 0 0 0 3.7 1.7H21m-4-4 4 4-4 4M3 17h2.5a5 5 0 0 0 3.7-1.7l1.1-1.3M17 3l4 4-4 4m4-4h-2.5a5 5 0 0 0-3.7 1.7l-1.1 1.3"/></svg>',
    previous:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M5 5v14"/><path d="m19 6-9 6 9 6V6Zm-9 0-9 6 9 6V6Z" fill="currentColor" stroke="none"/></svg>',
    rewind:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M3 11a9 9 0 1 1 2.2 6M3 4v7h7"/><text x="12" y="14.5" text-anchor="middle" font-size="6.5" font-weight="800" fill="currentColor" stroke="none">10</text></svg>',
    play:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m8 5 11 7-11 7V5Z" fill="currentColor" stroke="none"/></svg>',
    pause:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M8 5h3v14H8zM15 5h3v14h-3z" fill="currentColor" stroke="none"/></svg>',
    forward:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M21 11a9 9 0 1 0-2.2 6M21 4v7h-7"/><text x="12" y="14.5" text-anchor="middle" font-size="6.5" font-weight="800" fill="currentColor" stroke="none">10</text></svg>',
    next:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M19 5v14"/><path d="m5 6 9 6-9 6V6Zm9 0 9 6-9 6V6Z" fill="currentColor" stroke="none"/></svg>',
    repeat:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m17 2 4 4-4 4M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4M21 13v2a3 3 0 0 1-3 3H3"/></svg>',
    volume:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M11 5 6 9H3v6h3l5 4V5Zm4 3a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14"/></svg>',
    muted:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M11 5 6 9H3v6h3l5 4V5Zm5 4 5 6m0-6-5 6"/></svg>',
    pip:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="5" width="18" height="14" rx="2"/><rect x="12" y="11" width="6" height="5" rx="1"/></svg>',
    cast:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 4h16v12h-7M4 20h.01M4 16a4 4 0 0 1 4 4M4 12a8 8 0 0 1 8 8"/></svg>',
    fullscreen:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m13-5v3a2 2 0 0 1-2 2h-3"/></svg>',
    add:'<svg class="player-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 5v14M5 12h14"/></svg>'
  };
  function setPlayerIcon(id,name){const button=$(id);if(button)button.innerHTML=PLAYER_ICONS[name]||'';}
  const radioAudio = $('radio-player');
  const tvVideo = $('tv-player');
  let radioStations = [];
  let tvStations = [];
  let radioLoading = true;
  let tvLoading = false;
  let showingRadioFavorites = false;
  let showingRadioTopPicks = false;
  let radioFilterTouched = false;
  let radioGenreFilter = 'all';
  let favoritesMediaMode = 'tv';
  try{if(localStorage.getItem('coolmag.favorites.mode.v1')==='radio')favoritesMediaMode='radio';}catch{}
  let showingTVFavorites = false;
  let showingTVTopPicks = false;
  let tvFilterTouched = false;
  let sharedTVFavoritesLoaded = false;
  let sharedFavoritesPromise = null;
  let currentRadio = null;
  let currentTV = null;
  let hls = null;
  let homePreviewHls = null;
  let homePreviewStarted = false;
  let homePreviewStation = null;
  let homePreviewCycleTimer = null;
  let tvLoadController = null;
  let selectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  let toastTimer = null;
  let shuffleFavorites = false;
  let repeatCurrent = false;
  let currentView = 'home';
  let viewSwapToken = 0;
  let commandMatches = [];
  let commandSelected = 0;
  let commandTVSearchTimer = null;
  let commandTVSearchController = null;
  let commandTVSearchToken = 0;
  let adminGitHubToken = '';
  let adminSharedFavorites = {};
  let adminFavoritesSha = '';
  let adminFavoriteType = 'tv';
  const adminFavoriteDrafts = {tv:null,radio:null};
  const favoriteHistory = [];
  let favoriteHistoryMode = '';

  const readStore = (key) => {
    try { const value = JSON.parse(localStorage.getItem(key) || '{}'); return value && typeof value === 'object' ? value : {}; }
    catch { return {}; }
  };
  const savedSettings=readStore('coolmag.ui.settings.v1');
  const useVolumeDefaults=savedSettings.settingsVersion!==2;
  const uiSettings={
    theme:['light','night','epaper'].includes(savedSettings.theme)?savedSettings.theme:'night',
    weather:savedSettings.weather===true,
    time:savedSettings.settingsVersion===3?savedSettings.time===true:true,
    volume:useVolumeDefaults?true:savedSettings.volume===true,
    volumeLevel:useVolumeDefaults?0.3:Number.isFinite(Number(savedSettings.volumeLevel))?Math.max(0,Math.min(1,Number(savedSettings.volumeLevel))):0.3,
    settingsVersion:3
  };
  const radioFavorites = readStore('coolmag.radio.favorites.v1');
  const tvFavorites = readStore('coolmag.tv.favorites.v1');
  // Repair entries saved to the wrong browser favorites store by older app builds.
  // Move only records with clear radio or TV metadata; preserve uncertain rows.
  function isRadioFavoriteEntry(item) {
    if (!item) return false;
    const name=String(item.name||'').trim();
    return Boolean(item.stationuuid || item.url_resolved || item.favicon || item.codec || item.bitrate || item.tags || /\b(?:radio|fm)\b|akashvani|all india radio|\bair\b|\b987\b/i.test(name));
  }
  function isTVFavoriteEntry(item) {
    return Boolean(item && !isRadioFavoriteEntry(item) && (item.group || item.logo || Array.isArray(item.options)));
  }
  function repairFavoriteStores() {
    let movedRadio = 0, movedTV = 0;
    for (const [key, item] of Object.entries(radioFavorites)) {
      if (!isRadioFavoriteEntry(item) && isTVFavoriteEntry(item)) {
        let targetKey = item.url || key, suffix = 2;
        while (tvFavorites[targetKey] && tvFavorites[targetKey].url !== item.url) targetKey = `${item.url || key}#${suffix++}`;
        if (!tvFavorites[targetKey]) tvFavorites[targetKey] = item;
        delete radioFavorites[key]; movedTV++;
      }
    }
    for (const [key, item] of Object.entries(tvFavorites)) {
      if (isRadioFavoriteEntry(item) && !isTVFavoriteEntry(item)) {
        const baseKey = item.stationuuid || item.url_resolved || item.url || key;
        let targetKey = baseKey, suffix = 2;
        while (radioFavorites[targetKey] && radioFavorites[targetKey].url !== item.url) targetKey = `${baseKey}#${suffix++}`;
        if (!radioFavorites[targetKey]) radioFavorites[targetKey] = item;
        delete tvFavorites[key]; movedRadio++;
      }
    }
    if (movedRadio) persist('coolmag.radio.favorites.v1', radioFavorites);
    if (movedTV) persist('coolmag.tv.favorites.v1', tvFavorites);
  }
  const savedSort=readStore('coolmag.list.sort.v1');
  let radioSortMode=['name','genre'].includes(savedSort.radio)?savedSort.radio:'name';
  let tvSortMode=['name','genre'].includes(savedSort.tv)?savedSort.tv:'name';
  const readRecent = key => { try { const value=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(value)?value.filter(item=>item&&typeof item==='object'):[]; } catch { return []; } };
  const recentHistory = {radio:readRecent('coolmag.recent.radio.v1'),tv:readRecent('coolmag.recent.tv.v1')};
  const persist = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { toast('This browser could not save favorites.'); } };
  repairFavoriteStores();
  showingTVFavorites = Object.keys(tvFavorites).length > 0;
  const toast = (message) => {
    const node = $('toast'); node.textContent = message; node.classList.add('show');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => node.classList.remove('show'), 2600);
  };
  function saveSettings(){persist('coolmag.ui.settings.v1',uiSettings);}
  function updateSettingsControls(){
    for(const name of ['weather','time','volume']){
      const control=$(`settings-${name}`);control.setAttribute('aria-checked',String(Boolean(uiSettings[name])));control.classList.toggle('active',Boolean(uiSettings[name]));
    }
    document.querySelectorAll('[data-theme-choice]').forEach(button=>button.classList.toggle('active',button.dataset.themeChoice===uiSettings.theme));
  }
  function applyUserSettings(){
    document.documentElement.dataset.theme=uiSettings.theme;
    document.body.classList.toggle('weather-hidden',!uiSettings.weather);
    document.body.classList.toggle('clock-hidden',!uiSettings.time);
    const shownVolume=uiSettings.volume?uiSettings.volumeLevel:0;
    $('volume').value=String(shownVolume);$('volume-label').textContent=`${Math.round(shownVolume*100)}%`;
    radioAudio.volume=uiSettings.volumeLevel;tvVideo.volume=uiSettings.volumeLevel;$('home-tv-preview').volume=uiSettings.volumeLevel;
    radioAudio.muted=!uiSettings.volume;tvVideo.muted=!uiSettings.volume;$('home-tv-preview').muted=true;
    updateSettingsControls();syncTransport();
  }
  function setUserSetting(name,value){
    uiSettings[name]=Boolean(value);
    if(name==='volume'&&uiSettings.volume&&uiSettings.volumeLevel<=0)uiSettings.volumeLevel=0.8;
    applyUserSettings();saveSettings();
  }
  function openSettings(){ $('sidebar').classList.remove('open');$('settings-overlay').hidden=false;document.body.classList.add('settings-open');$('settings-close').focus(); }
  function closeSettings(){ $('settings-overlay').hidden=true;document.body.classList.remove('settings-open');$('settings-button').focus(); }
  let remoteAppVersion=null;
  async function checkForUpdates(){
    const button=$('check-updates'),status=$('update-status');
    if(remoteAppVersion){
      const cacheTag=`${remoteAppVersion}-${Date.now()}`;
      document.querySelectorAll('link[rel="stylesheet"][href*="style.css"],script[src*="app.js"]').forEach(asset=>{
        const key=asset.tagName==='LINK'?'href':'src';const url=new URL(asset[key],location.href);url.searchParams.set('v',cacheTag);asset[key]=url.href;
      });
      status.textContent='Updating CoolMagRaTv…';button.disabled=true;button.textContent='Updating…';location.reload();return;
    }
    button.disabled=true;button.textContent='Checking…';status.textContent='Checking the latest version on this site…';
    try{
      const script=document.querySelector('script[src*="app.js"]');
      if(!script)throw new Error('App script not found');
      const url=new URL(script.src,location.href);url.searchParams.set('check',String(Date.now()));
      const response=await fetch(url,{cache:'no-store'});if(!response.ok)throw new Error(`HTTP ${response.status}`);
      const source=await response.text();const match=source.match(/const\s+APP_VERSION\s*=\s*['"]([^'"]+)['"]/);
      if(!match)throw new Error('Version information is missing');
      if(match[1]===APP_VERSION){status.textContent=`You’re up to date · ${APP_VERSION}`;button.textContent='Check again';}
      else{remoteAppVersion=match[1];status.textContent=`A published version is available · ${remoteAppVersion}`;button.textContent='Update now';}
    }catch(error){status.textContent='Could not check. Make sure you are online and the app is hosted.';button.textContent='Try again';}
    finally{button.disabled=false;}
  }
  function skeletonCards(count=6) {
    return Array.from({length:count},()=>'<div class="skeleton-card" aria-hidden="true"><span class="skeleton-art"></span><span class="skeleton-line wide"></span><span class="skeleton-line"></span></div>').join('');
  }

  function activeMedia() { return currentTV ? tvVideo : currentRadio ? radioAudio : currentView==='home'&&homePreviewStarted ? $('home-tv-preview') : null; }
  function syncTransport() {
    const media=activeMedia();
    const playing=Boolean(media&&!media.paused&&!media.ended);
    document.querySelector('.app-shell')?.classList.toggle('is-playing',Boolean((currentTV&&!tvVideo.paused&&!tvVideo.ended)||(currentRadio&&!radioAudio.paused&&!radioAudio.ended)));
    setPlayerIcon('play-pause',playing?'pause':'play');
    $('play-pause').setAttribute('aria-label',playing?'Pause playback':'Play playback');
    $('play-pause').title=playing?'Pause playback':'Play playback';
    $('dock-mute').disabled=!media;
    setPlayerIcon('dock-mute',media?.muted?'muted':'volume');
    $('dock-mute').setAttribute('aria-label',media?.muted?'Unmute audio':'Mute audio');
    $('dock-mute').title=media?.muted?'Unmute audio':'Mute audio';
    $('dock-mute').setAttribute('aria-pressed',String(Boolean(media?.muted)));
    const tvPlaying=Boolean(currentTV&&!tvVideo.paused&&!tvVideo.ended);
    $('tv-full-toggle').textContent=tvPlaying?'Ⅱ':'▶';
    $('tv-full-toggle').setAttribute('aria-label',tvPlaying?'Pause TV':'Play TV');
    $('tv-full-toggle').disabled=!currentTV;
    $('tv-full-previous').disabled=!Object.keys(tvFavorites).length;
    $('tv-full-next').disabled=!Object.keys(tvFavorites).length;
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
    $('audio-visualizer')?.classList.toggle('active',playing&&Boolean(currentRadio||currentTV));
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
  function sortStationRows(rows,mode,kind){
    const category=station=>{
      const value=kind==='tv'?station.group:(Array.isArray(station.tags)?station.tags.join(','):station.tags);
      return String(value||'Other').split(/[;,]/)[0].trim()||'Other';
    };
    return [...rows].sort((a,b)=>{
      if(mode==='genre'){
        const groupOrder=category(a).localeCompare(category(b),undefined,{sensitivity:'base'});
        if(groupOrder)return groupOrder;
      }
      return String(a.name||'').localeCompare(String(b.name||''),undefined,{sensitivity:'base',numeric:true});
    });
  }
  function stepFavorite(direction) {
    const tvMode=$('tv-view').classList.contains('active')||Boolean(currentTV);
    const list=sortStationRows(Object.values(tvMode?tvFavorites:radioFavorites),tvMode?tvSortMode:radioSortMode,tvMode?'tv':'radio');
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
  function getHomeHeroStation() {
    return sortStationRows(Object.values(tvFavorites).filter(station=>station&&station.url),tvSortMode,'tv')[0]||HOME_BBC;
  }
  function updateHomeHeroStation(station) {
    const isFavorite=Boolean(tvFavorites[station.url]);
    $('hero-title').textContent=station.name||'Live TV';
    $('hero-subtitle').textContent=isFavorite?`TV favorite · ${station.country||station.group||'Live television'}`:`Live BBC News preview · South Asia feed.`;
    $('home-tv-preview').setAttribute('aria-label',`${station.name||'TV channel'} live preview`);
    const artwork=$('hero-preview');
    artwork.replaceChildren();
    let logoURL='';try{const candidate=new URL(station.logo||'');if(candidate.protocol==='https:')logoURL=candidate.href;}catch{}
    if(logoURL){const image=document.createElement('img');image.src=logoURL;image.alt='';image.loading='lazy';artwork.append(image);}
    else{const mark=document.createElement('strong');mark.className=isFavorite?'hero-station-mark':'bbc-wordmark';mark.textContent=isFavorite?(station.name||'TV').trim().slice(0,4).toUpperCase():'BBC';artwork.append(mark);}
    if(!isFavorite){const label=document.createElement('span');label.id='hero-preview-label';label.textContent='WORLD NEWS';artwork.append(label);}
  }
  function scheduleHomePreviewRotation() {
    clearInterval(homePreviewCycleTimer);
    homePreviewCycleTimer=setInterval(()=>{
      const favorites=sortStationRows(Object.values(tvFavorites).filter(station=>station&&station.url),tvSortMode,'tv');
      if(favorites.length<2)return;
      const currentIndex=favorites.findIndex(station=>station.url===homePreviewStation?.url);
      startHomePreview(favorites[(currentIndex+1+favorites.length)%favorites.length]);
    },10000);
  }
  function startHomePreview(stationOverride=null) {
    const preview=$('home-tv-preview');
    const station=stationOverride||((homePreviewStation&&tvFavorites[homePreviewStation.url])?homePreviewStation:getHomeHeroStation());
    if(homePreviewStarted&&homePreviewStation?.url===station.url){preview.play().catch(()=>{});scheduleHomePreviewRotation();return;}
    if(homePreviewStarted)stopHomePreview();
    homePreviewStation=station;
    updateHomeHeroStation(station);
    homePreviewStarted=true;
    preview.muted=true;
    preview.volume=Number($('volume').value);
    const isHls=/\.m3u8($|\?)/i.test(station.url);
    scheduleHomePreviewRotation();
    if(isHls&&window.Hls&&Hls.isSupported()){
      homePreviewHls=new Hls({enableWorker:true,lowLatencyMode:false,maxBufferLength:8});
      homePreviewHls.loadSource(station.url);
      homePreviewHls.attachMedia(preview);
      homePreviewHls.on(Hls.Events.MANIFEST_PARSED,()=>preview.play().catch(()=>{}));
      homePreviewHls.on(Hls.Events.ERROR,(_event,data)=>{if(data.fatal)$('hero-subtitle').textContent='This favorite preview is unavailable right now · Select WATCH LIVE to retry.';});
      return;
    }
    if(!isHls||preview.canPlayType('application/vnd.apple.mpegurl')){
      preview.src=station.url;
      preview.play().catch(()=>{});
    }else $('hero-subtitle').textContent='This browser cannot preview the favorite stream · Select WATCH LIVE to open it.';
  }
  function stopHomePreview() {
    clearInterval(homePreviewCycleTimer);homePreviewCycleTimer=null;
    const preview=$('home-tv-preview');
    if(homePreviewHls){homePreviewHls.destroy();homePreviewHls=null;}
    if(preview){preview.pause();preview.removeAttribute('src');preview.load();}
    homePreviewStarted=false;
    homePreviewStation=null;
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
    if(!$(`${view}-view`))return;
    if(document.startViewTransition){
      document.startViewTransition(()=>{currentView=view;applyView(view);});
      return;
    }
    const main=$('main-content');const token=++viewSwapToken;
    main.classList.add('view-fade-out');
    setTimeout(()=>{
      if(token!==viewSwapToken)return;
      currentView=view;applyView(view);main.classList.remove('view-fade-out');main.classList.add('view-fade-in');
      setTimeout(()=>{if(token===viewSwapToken)main.classList.remove('view-fade-in');},260);
    },125);
  }
  function applyView(view) {
    if(view!=='tv'&&currentTV)stopTV();
    if(view!=='tv'){
      document.querySelector('.app-shell').classList.remove('cinema-mode');
      $('cinema-toggle').setAttribute('aria-pressed','false');
    }
    if(view==='tv'){
      showingTVFavorites=false;
      showingTVTopPicks=true;
      if(!sharedTVFavoritesLoaded)loadSharedFavorites();
      renderTV();
    }
    if(view==='radio'){
      showingRadioFavorites=false;
      showingRadioTopPicks=true;
      renderRadio();
    }
    if(view==='home'){
      if(currentTV)stopTV();
      if(currentRadio){radioAudio.pause();radioAudio.removeAttribute('src');radioAudio.load();currentRadio=null;}
      startHomePreview();
    }else stopHomePreview();
    document.querySelectorAll('.side-link').forEach(button=>button.classList.toggle('active',button.dataset.view===view));
    document.querySelectorAll('.view-panel').forEach(panel => panel.classList.toggle('active', panel.id === `${view}-view`));
    const titles={home:'Your media, in one place',radio:'World Radio',tv:'Live TV',recent:'Recently played',favorites:'Top Picks',news:'News & magazines'};
    const pageIcons={
      radio:'<svg viewBox="0 0 24 24" focusable="false"><rect x="3" y="8" width="18" height="12" rx="2"/><path d="m6 5 12-3M7 12h.01M7 16h.01m4-4h6m-6 4h6"/></svg>',
      tv:'<svg viewBox="0 0 24 24" focusable="false"><rect x="3" y="5" width="18" height="13" rx="2"/><path d="m8 22 4-4 4 4M8 10h8"/></svg>',
    };
    $('section-title-text').textContent=titles[view]||'COOLmagRaTv';
    $('section-icon').innerHTML=pageIcons[view]||'';
    $('section-title').classList.toggle('has-page-icon',Boolean(pageIcons[view]));
    $('section-icon').classList.toggle('radio-page-icon',view==='radio');
    $('section-icon').classList.toggle('tv-page-icon',view==='tv');
    if(view==='tv'&&currentRadio){radioAudio.pause();radioAudio.removeAttribute('src');radioAudio.load();currentRadio=null;}
    if(view==='radio'&&currentTV)stopTV();
    if(view==='news'){if(currentRadio){radioAudio.pause();radioAudio.removeAttribute('src');radioAudio.load();currentRadio=null;}if(currentTV)stopTV();}
    if(!activeMedia()){$('playing-title').textContent='COOLmagRaTv';$('playing-subtitle').textContent='Choose a stream to begin';}
    if(view==='favorites')renderFavorites();
    if(view==='recent')renderRecent();
    if(view==='tv')renderTV();
    $('sidebar').classList.remove('open');
    syncTransport();
  }
  function openCommandPalette(){
    const overlay=$('command-overlay');overlay.hidden=false;document.body.classList.add('command-open');
    $('command-input').value='';renderCommandResults();requestAnimationFrame(()=>$('command-input').focus());
  }
  function closeCommandPalette(){
    $('command-overlay').hidden=true;document.body.classList.remove('command-open');
  }
  function commandItems(query=''){
    const items=[];const add=(title,detail,type,action,id)=>items.push({title,detail,type,action,id});
    const pages=[['Home','Dashboard','home'],['Live TV','Watch live television','tv'],['Radio','Browse internet radio','radio'],['Recently played','Your listening history','recent'],['Top Picks','Saved stations and channels','favorites'],['News & Magazines','Open news publishers','news']];
    pages.forEach(([title,detail,view])=>add(title,detail,'page',()=>setView(view),view));
    const known=new Set();
    [...Object.values(radioFavorites),...radioStations].forEach(station=>{if(!station)return;const key=`radio:${radioKey(station)}`;if(known.has(key))return;known.add(key);add(station.name||'Radio station',`${station.country||'Radio'}${radioFavorites[radioKey(station)]?' · Favorite':''}`,'radio',()=>{setView('radio');playRadio(station);},key);});
    [...Object.values(tvFavorites),...tvStations].forEach(station=>{if(!station)return;const key=`tv:${station.url}`;if(known.has(key))return;known.add(key);add(station.name||'TV channel',`${station.group||station.country||'Live TV'}${tvFavorites[tvKey(station)]?' · Favorite':''}`,'tv',()=>{setView('tv');playTV(station);},key);});
    const term=query.trim().toLowerCase();
    let matches=term?items.filter(item=>`${item.title} ${item.detail}`.toLowerCase().includes(term)):items.filter(item=>item.type==='page'||item.detail.includes('Favorite'));
    if(term&&!matches.some(item=>item.type==='radio'))matches.push({title:`Search and play “${query.trim()}” on Radio`,detail:'Search Radio Browser for a matching station','type':'radio-search',action:()=>{setView('radio');$('radio-search').value=query.trim();searchRadio().then(()=>{if(radioStations.length)playRadio(radioStations[0]);});}});
    return matches.slice(0,14);
  }
  async function searchTVCatalog(query,signal){
    const country=$('tv-country-select').value;
    const file=country!=='all'?`countries/${country.toLowerCase()}.m3u`:'index.m3u';
    const response=await fetch(IPTV_BASE+file,{cache:'no-cache',signal});
    if(!response.ok)throw new Error(`TV catalog unavailable (${response.status})`);
    const needle=query.trim().toLocaleLowerCase();
    const matches=[];const seen=new Set();let meta='',buffer='';
    const consume=line=>{
      line=line.trim();
      if(line.startsWith('#EXTINF')){meta=line;return;}
      if(!line||line.startsWith('#')||!meta)return;
      const row=playlistRow(meta,line);meta='';
      if(`${row.name} ${row.group} ${row.country}`.toLocaleLowerCase().includes(needle)&&!seen.has(row.url)){
        seen.add(row.url);matches.push(row);
      }
    };
    if(!response.body?.getReader){
      for(const line of (await response.text()).split(/\r?\n/)){consume(line);if(matches.length>=20)break;}
      return matches;
    }
    const reader=response.body.getReader(),decoder=new TextDecoder();
    while(matches.length<20){
      const {value,done}=await reader.read();
      buffer+=decoder.decode(value||new Uint8Array(),{stream:!done});
      const lines=buffer.split(/\r?\n/);buffer=lines.pop()||'';
      for(const line of lines){consume(line);if(matches.length>=20)break;}
      if(done||matches.length>=20)break;
    }
    if(matches.length>=20)reader.cancel().catch(()=>{});
    return matches;
  }
  function renderCommandRows(){
    const target=$('command-results');
    if(!commandMatches.length){target.innerHTML='<div class="command-empty">No matching stations or actions.</div>';return;}
    target.innerHTML=commandMatches.map((item,index)=>`<button class="command-result ${index===commandSelected?'selected':''}" role="option" aria-selected="${index===commandSelected}" data-command-index="${index}"><span class="command-result-icon">${item.type==='tv'?'▣':item.type==='radio'?'♫':'⌕'}</span><span><b>${safe(item.title)}</b><small>${safe(item.detail)}</small></span><kbd>${item.type==='radio'||item.type==='tv'?'↵':''}</kbd></button>`).join('');
    target.querySelectorAll('[data-command-index]').forEach(button=>button.addEventListener('click',()=>runCommand(Number(button.dataset.commandIndex))));
  }
  function renderCommandResults(){
    const query=$('command-input').value.trim();
    clearTimeout(commandTVSearchTimer);commandTVSearchController?.abort();
    const token=++commandTVSearchToken;
    commandMatches=commandItems(query);commandSelected=0;renderCommandRows();
    if(query.length<3)return;
    const target=$('command-results');
    target.insertAdjacentHTML('beforeend',`<div class="command-empty" data-tv-search-status>Searching TV channels for “${safe(query)}”…</div>`);
    commandTVSearchTimer=setTimeout(async()=>{
      const controller=new AbortController();commandTVSearchController=controller;
      try{
        const matches=await searchTVCatalog(query,controller.signal);
        if(token!==commandTVSearchToken)return;
        const tvItems=matches.map(station=>({title:station.name||'TV channel',detail:`${station.country||'TV'} · ${station.group||'Live TV'} · IPTV-org`,type:'tv',id:`tv:${station.url}`,action:()=>{setView('tv');showingTVFavorites=false;if(!tvStations.some(row=>row.url===station.url))tvStations.unshift(station);renderTV();playTV(station);}}));
        const existing=commandItems(query),seen=new Set();
        commandMatches=[...tvItems,...existing].filter(item=>{const key=item.id||`${item.type}:${item.title}`;if(seen.has(key))return false;seen.add(key);return true;}).slice(0,14);
        commandSelected=0;renderCommandRows();
        if(!matches.length)$('command-results').insertAdjacentHTML('beforeend','<div class="command-empty">No TV channel matched. Try another name or country.</div>');
      }catch(error){
        if(error.name==='AbortError'||token!==commandTVSearchToken)return;
        const status=$('command-results').querySelector('[data-tv-search-status]');
        if(status)status.textContent='TV catalog search unavailable. Check your connection.';
      }
    },350);
  }
  function runCommand(index){const item=commandMatches[index];if(!item)return;closeCommandPalette();item.action();}
  $('command-open-top').addEventListener('click',openCommandPalette);
  $('command-open-side').addEventListener('click',openCommandPalette);
  $('command-overlay').addEventListener('click',event=>{if(event.target===$('command-overlay'))closeCommandPalette();});
  $('command-input').addEventListener('input',renderCommandResults);
  $('command-input').addEventListener('keydown',event=>{
    if(event.key==='ArrowDown'||event.key==='ArrowUp'){
      event.preventDefault();if(!commandMatches.length)return;
      commandSelected=(commandSelected+(event.key==='ArrowDown'?1:-1)+commandMatches.length)%commandMatches.length;
      $('command-results').querySelectorAll('.command-result').forEach((button,index)=>{button.classList.toggle('selected',index===commandSelected);button.setAttribute('aria-selected',String(index===commandSelected));});
    }else if(event.key==='Enter'){event.preventDefault();runCommand(commandSelected);}
  });
  $('cinema-toggle').addEventListener('click',()=>{
    const shell=document.querySelector('.app-shell'),enabled=!shell.classList.contains('cinema-mode');
    shell.classList.toggle('cinema-mode',enabled);$('cinema-toggle').setAttribute('aria-pressed',String(enabled));
    $('cinema-toggle').setAttribute('aria-label',enabled?'Exit cinema mode':'Enter cinema mode');
    $('cinema-toggle').title=enabled?'Exit cinema mode':'Cinema mode';
    if(enabled)requestAnimationFrame(()=>$('video-stage').scrollIntoView({block:'center',behavior:'smooth'}));
  });
  $('video-fullscreen').addEventListener('click',toggleTVFullView);
  function toggleMute(){
    const media=activeMedia()||(currentView==='home'?$('home-tv-preview'):null);if(!media)return;
    if(media===radioAudio||media===tvVideo){setUserSetting('volume',media.muted||!uiSettings.volume);return;}
    media.muted=!media.muted;
    const button=$('home-preview-sound');button.textContent=media.muted?'🔇':'🔊';button.setAttribute('aria-label',media.muted?'Unmute preview':'Mute preview');
    syncTransport();
  }
  $('dock-mute').addEventListener('click',toggleMute);
  document.addEventListener('keydown',event=>{
    if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();openCommandPalette();return;}
    if(event.key==='Escape'&&!$('admin-overlay').hidden){closeAdminFavorites();return;}
    if(event.key==='Escape'&&!$('settings-overlay').hidden){closeSettings();return;}
    if(event.key==='Escape'&&!$('command-overlay').hidden){closeCommandPalette();return;}
    const target=event.target;const typing=target instanceof HTMLElement&&(target.isContentEditable||['INPUT','TEXTAREA','SELECT'].includes(target.tagName));
    if(typing||(target instanceof HTMLElement&&target.closest('button,a,[role="button"]'))||event.altKey||event.ctrlKey||event.metaKey)return;
    if(event.code==='Space'){event.preventDefault();playPauseActive();}
    else if(event.key.toLowerCase()==='m')toggleMute();
    else if(event.key.toLowerCase()==='f'&&currentView==='tv')toggleTVFullView();
  });
  document.querySelectorAll('.side-link[data-view],.text-button[data-view]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.view)));
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
  $('settings-button').addEventListener('click',openSettings);
  $('settings-close').addEventListener('click',closeSettings);
  $('settings-overlay').addEventListener('click',event=>{if(event.target===$('settings-overlay'))closeSettings();});
  $('admin-open').addEventListener('click',openAdminFavorites);
  $('admin-close').addEventListener('click',closeAdminFavorites);
  $('admin-overlay').addEventListener('click',event=>{if(event.target===$('admin-overlay'))closeAdminFavorites();});
  $('admin-connect').addEventListener('click',connectAdminFavorites);
  $('admin-token').addEventListener('keydown',event=>{if(event.key==='Enter')connectAdminFavorites();});
  $('admin-tv-tab').addEventListener('click',()=>switchAdminFavoriteType('tv'));
  $('admin-radio-tab').addEventListener('click',()=>switchAdminFavoriteType('radio'));
  $('admin-list-search').addEventListener('input',filterAdminFavoriteList);
  $('admin-import-local').addEventListener('click',importBrowserFavorites);
  $('admin-import-json').addEventListener('click',()=>$('admin-json-file').click());
  $('admin-json-file').addEventListener('change',importAdminJSONFile);
  $('admin-add-channel').addEventListener('click',addAdminFavorite);
  $('admin-save').addEventListener('click',publishAdminFavorites);
  $('admin-disconnect').addEventListener('click',()=>{adminGitHubToken='';adminFavoritesSha='';adminSharedFavorites={};adminFavoriteDrafts.tv=null;adminFavoriteDrafts.radio=null;$('admin-token').value='';$('admin-workspace').hidden=true;$('admin-status').textContent='Disconnected. Your token has been cleared.';});
  $('settings-weather').addEventListener('click',()=>setUserSetting('weather',!uiSettings.weather));
  $('settings-time').addEventListener('click',()=>setUserSetting('time',!uiSettings.time));
  $('settings-volume').addEventListener('click',()=>setUserSetting('volume',!uiSettings.volume));
  $('check-updates').addEventListener('click',checkForUpdates);
  document.querySelectorAll('[data-theme-choice]').forEach(button=>button.addEventListener('click',()=>{uiSettings.theme=button.dataset.themeChoice;applyUserSettings();saveSettings();}));
  $('hero-watch').addEventListener('click',()=>{const station=(homePreviewStation&&tvFavorites[homePreviewStation.url])?homePreviewStation:getHomeHeroStation();setView('tv');playTV(station);});
  $('home-preview-sound').addEventListener('click',()=>{
    const preview=$('home-tv-preview');
    if(!homePreviewStarted)startHomePreview();
    preview.muted=!preview.muted;
    $('home-preview-sound').textContent=preview.muted?'🔇':'🔊';
    $('home-preview-sound').setAttribute('aria-label',preview.muted?'Unmute TV preview':'Mute TV preview');
    $('home-preview-sound').title=preview.muted?'Unmute preview':'Mute preview';
    syncTransport();
    preview.play().catch(()=>toast('TV preview could not start in this browser.'));
  });

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
    let apiRows=[];
    try {
      const result=await radioGet('/countries?order=stationcount&reverse=true');
      if(Array.isArray(result))apiRows=result;
    } catch { /* Use the built-in country list when the directory is unavailable. */ }
    let displayNames=null;
    try{displayNames=new Intl.DisplayNames(['en'],{type:'region'});}catch{}
    const byCode=new Map(COUNTRY_CODES.map(code=>[code,displayNames?.of(code)||code]));
    apiRows.filter(row=>row.iso_3166_1&&row.name).forEach(row=>byCode.set(row.iso_3166_1,row.name));
    const sorted=[...byCode.entries()].sort((a,b)=>a[1].localeCompare(b[1]));
    const select=$('country-select');
    select.innerHTML='<option value="all">Worldwide</option>'+sorted.map(([code,name])=>`<option value="${safe(code)}">${safe(name)}</option>`).join('');
    select.value=byCode.has('IN')?'IN':'all';
    const tvCountry=$('tv-country-select');
    tvCountry.innerHTML='<option value="all">All countries</option>'+sorted.map(([code,name])=>`<option value="${safe(code)}">${safe(name)}</option>`).join('');
    tvCountry.value='all';
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
    updateFullscreenTVHeader();
  }
  async function loadSharedFavorites() {
    if(sharedFavoritesPromise)return sharedFavoritesPromise;
    sharedFavoritesPromise=(async()=>{
      const sources=[
        ['map_favorites.json',radioFavorites,'coolmag.radio.favorites.v1'],
        ['surak_home_tv_favorites.json',tvFavorites,'coolmag.tv.favorites.v1']
      ];
      await Promise.all(sources.map(async([file,target,storageKey])=>{
        const urls=[
          `https://raw.githubusercontent.com/suppuone/RADIOtv/main/${file}?refresh=${Date.now()}`,
          `https://cdn.jsdelivr.net/gh/suppuone/RADIOtv@main/${file}`
        ];
        for(const url of urls){
          try{
            const response=await fetch(url,{cache:'no-store'});
            if(!response.ok)continue;
            const shared=await response.json();
            if(!shared||typeof shared!=='object'||Array.isArray(shared))continue;
            for(const[key,station]of Object.entries(shared))target[key]=station;
            persist(storageKey,target);
            if(file==='surak_home_tv_favorites.json')sharedTVFavoritesLoaded=true;
            break;
          }catch{/* Retry through the alternate public mirror. */}
        }
      }));
      repairFavoriteStores();
      updateFavoriteCounts();
      if(showingRadioFavorites)renderRadio();
      if(showingTVFavorites||$('tv-view').classList.contains('active'))renderTV();
      renderHomeRadio();renderHomeTV();renderFavorites();
      if(currentView==='home')startHomePreview();
    })();
    try{return await sharedFavoritesPromise;}
    finally{sharedFavoritesPromise=null;}
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

  const ADMIN_FAVORITES_API={
    tv:'https://api.github.com/repos/suppuone/RADIOtv/contents/surak_home_tv_favorites.json',
    radio:'https://api.github.com/repos/suppuone/RADIOtv/contents/map_favorites.json'
  };
  function adminHeaders(){return {Authorization:`Bearer ${adminGitHubToken}`,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'};}
  function decodeGitHubFile(content){const binary=atob(content.replace(/\s/g,''));return new TextDecoder().decode(Uint8Array.from(binary,char=>char.charCodeAt(0)));}
  function encodeGitHubFile(value){const bytes=new TextEncoder().encode(JSON.stringify(value,null,2));let binary='';for(const byte of bytes)binary+=String.fromCharCode(byte);return btoa(binary);}
  function captureAdminDraft(){
    document.querySelectorAll('#admin-favorite-list [data-admin-row]').forEach(row=>{
      const key=row.dataset.adminRow,item=adminSharedFavorites[key];if(!item)return;
      item.name=row.querySelector('[data-admin-name]').value.trim()||(adminFavoriteType==='radio'?'Radio station':'TV channel');
      if(adminFavoriteType==='radio'){
        item.country=row.querySelector('[data-admin-group]').value.trim();
        const stream=row.querySelector('[data-admin-stream]')?.value.trim();
        if(stream){item.url=stream;item.url_resolved=stream;}
      }
      else item.group=row.querySelector('[data-admin-group]').value.trim()||'Live TV';
      const logo=row.querySelector('[data-admin-logo]').value.trim();
      if(adminFavoriteType==='radio')item.favicon=logo;
      else item.logo=logo;
    });
    adminFavoriteDrafts[adminFavoriteType]={favorites:adminSharedFavorites,sha:adminFavoritesSha};
  }
  function updateAdminFavoriteLabels(){
    const radio=adminFavoriteType==='radio';
    $('admin-tv-tab').classList.toggle('active',!radio);$('admin-tv-tab').setAttribute('aria-selected',String(!radio));
    $('admin-radio-tab').classList.toggle('active',radio);$('admin-radio-tab').setAttribute('aria-selected',String(radio));
    $('admin-heading').textContent=radio?'Shared Radio Favorites':'Shared TV Favorites';
    $('admin-add-heading').textContent=radio?'Add a shared radio station':'Add a shared TV channel';
    $('admin-name-label').textContent=radio?'Station name':'Channel name';
    $('admin-group-label').textContent=radio?'Country':'Category';
    $('admin-channel-group').placeholder=radio?'India':'News';
    $('admin-channel-name').placeholder=radio?'BBC World Service':'Adventure Earth';
    $('admin-channel-logo').placeholder=radio?'https://… (optional)':'https://…m3u8';
    $('admin-logo-label').textContent=radio?'Station image URL (optional)':'Logo URL (optional)';
    $('admin-list-title').textContent=radio?'Shared radio stations · stream and logo URLs':'Shared TV channels';
    $('admin-list-search').placeholder=radio?'Search all radio stations by name, tag, country, or URL…':'Search all TV channels by name, category, country, or URL…';
    $('admin-import-help').textContent=`Imports ${radio?'radio stations':'TV channels'} saved in this browser. Localhost and the hosted site have separate lists.`;
    $('admin-json-import-help').textContent=`Imports a ${radio?'radio':'TV'} JSON file. New items are added and missing logos are filled; existing stream URLs and station details are preserved.`;
  }
  function filterAdminFavoriteList(){
    const target=$('admin-favorite-list'),term=$('admin-list-search').value.trim().toLocaleLowerCase(),rows=[...target.querySelectorAll('[data-admin-row]')];let visible=0;
    rows.forEach(row=>{const fields=[row.dataset.adminSearch,...[...row.querySelectorAll('input')].map(input=>input.value)].join(' ').toLocaleLowerCase();const match=!term||fields.includes(term);row.hidden=!match;if(match)visible++;});
    $('admin-count').textContent=term?`${visible} / ${rows.length}`:String(rows.length);
  }
  function renderAdminFavorites(){
    const target=$('admin-favorite-list'),entries=Object.entries(adminSharedFavorites).sort(([,a],[,b])=>String(a?.name||'').localeCompare(String(b?.name||''),undefined,{sensitivity:'base'})),radio=adminFavoriteType==='radio';
    $('admin-count').textContent=String(entries.length);
    if(!entries.length){target.innerHTML=`<div class="command-empty">No shared ${radio?'radio stations':'TV channels'} yet.</div>`;return;}
    target.innerHTML=entries.map(([key,item])=>{const logo=item.favicon||item.logo||item.image||item.artwork||'',search=[key,item.name,item.country,item.group,item.tags,item.url,item.url_resolved,logo].filter(Boolean).join(' ');return radio?`<article class="admin-favorite-row radio-admin-row" data-admin-row="${safe(key)}" data-admin-search="${safe(search)}"><label class="admin-field"><span>Station name</span><input data-admin-name value="${safe(item.name||'Radio station')}"></label><label class="admin-field"><span>Country</span><input data-admin-group value="${safe(item.country||'')}"></label><label class="admin-field"><span>Stream URL</span><input data-admin-stream type="url" value="${safe(item.url_resolved||item.url||'')}" placeholder="https://…"></label><label class="admin-field"><span>Logo URL</span><input data-admin-logo type="url" value="${safe(logo)}" placeholder="https://…"></label><button class="admin-remove" data-admin-remove="${safe(key)}" type="button">Remove</button></article>`:`<article class="admin-favorite-row" data-admin-row="${safe(key)}" data-admin-search="${safe(search)}"><label class="admin-field"><span>Channel name</span><input data-admin-name value="${safe(item.name||'TV channel')}"></label><label class="admin-field"><span>Category</span><input data-admin-group value="${safe(item.group||'Live TV')}"></label><label class="admin-field"><span>Logo image URL</span><input data-admin-logo type="url" value="${safe(logo)}" placeholder="https://…"></label><button class="admin-remove" data-admin-remove="${safe(key)}" type="button">Remove</button><div class="admin-favorite-url" title="${safe(item.url_resolved||item.url||key)}">${safe(item.url_resolved||item.url||key)}</div></article>`;}).join('');
    target.querySelectorAll('.admin-favorite-row input').forEach(input=>input.addEventListener('input',captureAdminDraft));
    target.querySelectorAll('[data-admin-remove]').forEach(button=>button.addEventListener('click',()=>{delete adminSharedFavorites[button.dataset.adminRemove];renderAdminFavorites();}));
    filterAdminFavoriteList();
  }
  async function loadAdminFavoriteType(type){
    adminFavoriteType=type;updateAdminFavoriteLabels();
    const draft=adminFavoriteDrafts[type];
    if(draft){adminSharedFavorites=draft.favorites;adminFavoritesSha=draft.sha;renderAdminFavorites();$('admin-status').textContent=`Connected · ${Object.keys(adminSharedFavorites).length} shared ${type==='radio'?'radio stations':'TV channels'} loaded.`;return;}
    if(!adminGitHubToken){$('admin-status').textContent='Connect to GitHub to load this shared list.';return;}
    adminSharedFavorites={};adminFavoritesSha='';renderAdminFavorites();
    $('admin-status').textContent=`Loading shared ${type==='radio'?'radio stations':'TV channels'} from GitHub…`;
    try{
      const response=await fetch(`${ADMIN_FAVORITES_API[type]}?ref=main`,{headers:adminHeaders(),cache:'no-store'});
      if(!response.ok)throw new Error(response.status===401||response.status===403?'GitHub rejected the token. Check that it has Contents read/write access to RADIOtv.':`GitHub request failed (${response.status}).`);
      const file=await response.json(),favorites=JSON.parse(decodeGitHubFile(file.content));
      if(!favorites||Array.isArray(favorites)||typeof favorites!=='object')throw new Error('The shared favorites file is not a valid list.');
      adminSharedFavorites=favorites;adminFavoritesSha=file.sha;adminFavoriteDrafts[type]={favorites,sha:file.sha};
      $('admin-workspace').hidden=false;renderAdminFavorites();
      $('admin-status').textContent=`Connected · ${Object.keys(favorites).length} shared ${type==='radio'?'radio stations':'TV channels'} loaded.`;
    }catch(error){$('admin-status').textContent=error.message||'Could not load the shared list.';}
  }
  function switchAdminFavoriteType(type){
    if(type===adminFavoriteType)return;
    captureAdminDraft();$('admin-list-search').value='';loadAdminFavoriteType(type);
  }
  async function connectAdminFavorites(){
    const button=$('admin-connect'),status=$('admin-status');
    adminGitHubToken=$('admin-token').value.trim();
    if(!adminGitHubToken){status.textContent='Paste your GitHub token to connect.';return;}
    adminFavoriteDrafts.tv=null;adminFavoriteDrafts.radio=null;adminFavoritesSha='';
    button.disabled=true;button.textContent='Connecting…';status.textContent='Loading shared favorites from GitHub…';
    try{await loadAdminFavoriteType(adminFavoriteType);if(!adminFavoritesSha)throw new Error(status.textContent);}
    catch(error){adminGitHubToken='';$('admin-token').value='';status.textContent=error.message||'Could not connect to GitHub.';}
    finally{button.disabled=false;button.textContent='Connect';}
  }
  function importBrowserFavorites(){
    const radio=adminFavoriteType==='radio',storageKey=radio?'coolmag.radio.favorites.v1':'coolmag.tv.favorites.v1';
    let localFavorites={};
    try{const parsed=JSON.parse(localStorage.getItem(storageKey)||'{}');if(parsed&&typeof parsed==='object'&&!Array.isArray(parsed))localFavorites=parsed;}catch{}
    const saved=Object.entries(localFavorites).filter(([,station])=>station&&(station.url||station.url_resolved));
    if(!saved.length){$('admin-status').textContent=`No ${radio?'radio':'TV'} favorites were found for ${location.origin}. Localhost and hosted site lists are separate.`;return;}
    let added=0;
    saved.forEach(([key,station])=>{
      const url=station.url_resolved||station.url;
      const sharedKey=radio?(station.stationuuid||key||url):url;
      const normalized=radio?{...station,url,url_resolved:station.url_resolved||url}:{...station,url};
      const exists=Boolean(adminSharedFavorites[sharedKey]);adminSharedFavorites[sharedKey]={...(adminSharedFavorites[sharedKey]||{}),...normalized};if(!exists)added++;
    });
    captureAdminDraft();renderAdminFavorites();
    $('admin-status').textContent=`Imported ${saved.length} browser ${radio?'radio stations':'TV channels'} (${added} new). Publish the shared list to send them to GitHub.`;
  }
  function adminImportedLogo(item){return item?.favicon||item?.logo||item?.image||item?.artwork||'';}
  function findImportedFavoriteMatch(key,item){
    const entries=Object.entries(adminSharedFavorites),ids=[item?.stationuuid,key].filter(Boolean).map(String),urls=[item?.url_resolved,item?.url].filter(Boolean).map(String);
    let match=entries.find(([,current])=>ids.some(id=>id===String(current?.stationuuid||'')));
    if(!match)match=entries.find(([,current])=>urls.some(url=>url===String(current?.url_resolved||'')||url===String(current?.url||'')));
    if(match)return match;
    const name=String(item?.name||'').trim().toLocaleLowerCase(),country=String(item?.country||'').trim().toLocaleLowerCase();
    if(!name)return null;
    return entries.find(([,current])=>String(current?.name||'').trim().toLocaleLowerCase()===name&&(!country||!current?.country||String(current.country).trim().toLocaleLowerCase()===country))||null;
  }
  async function importAdminJSONFile(event){
    const input=event.currentTarget,file=input.files?.[0];if(!file)return;
    const radio=adminFavoriteType==='radio';$('admin-status').textContent=`Reading ${file.name}…`;
    try{
      const parsed=JSON.parse(await file.text()),entries=Array.isArray(parsed)?parsed.map((item,index)=>[item?.stationuuid||item?.url||`import-${index}`,item]):parsed&&typeof parsed==='object'?Object.entries(parsed):null;
      if(!entries)throw new Error('Choose a JSON object or list of stations/channels.');
      let added=0,logos=0,skipped=0;
      for(const[rawKey,item]of entries){
        if(!item||typeof item!=='object'||Array.isArray(item)){skipped++;continue;}
        const key=String(rawKey||item.stationuuid||item.url_resolved||item.url||item.name||'').trim();if(!key){skipped++;continue;}
        const matched=findImportedFavoriteMatch(key,item);
        if(!matched){let uniqueKey=key,suffix=2;while(Object.prototype.hasOwnProperty.call(adminSharedFavorites,uniqueKey))uniqueKey=`${key}#${suffix++}`;adminSharedFavorites[uniqueKey]=item;added++;continue;}
        const existing=matched[1],incomingLogo=String(adminImportedLogo(item)||'').trim(),currentLogo=String(adminImportedLogo(existing)||'').trim();
        const genericLogo=/apple-touch-icon|(?:^|\/)favicon\.(?:ico|png)|placeholder/i.test(currentLogo);
        if(incomingLogo&&(!currentLogo||genericLogo)){
          if(radio)existing.favicon=incomingLogo;else existing.logo=incomingLogo;
          logos++;
        }
      }
      captureAdminDraft();renderAdminFavorites();
      $('admin-status').textContent=`Imported ${added} new ${radio?'stations':'channels'} and filled ${logos} missing logo${logos===1?'':'s'}. Existing stream URLs and station details were preserved${skipped?`; skipped ${skipped} invalid row${skipped===1?'':'s'}`:''}. Click Publish shared list to save these changes to GitHub.`;
    }catch(error){$('admin-status').textContent=error.message||'Could not read this JSON file.';}
    finally{input.value='';}
  }
  function addAdminFavorite(){
    const radio=adminFavoriteType==='radio',name=$('admin-channel-name').value.trim(),url=$('admin-channel-url').value.trim(),extra=$('admin-channel-group').value.trim(),logo=$('admin-channel-logo').value.trim();
    if(!name||!url){$('admin-status').textContent='Enter both a name and stream URL.';return;}
    if(!/^https?:\/\//i.test(url)){$('admin-status').textContent='The stream URL must begin with http:// or https://.';return;}
    if(radio){adminSharedFavorites[url]={stationuuid:url,name,url,url_resolved:url,country:extra,favicon:logo,tags:'',codec:'',bitrate:0};}
    else{adminSharedFavorites[url]={name,group:extra||'Live TV',logo,url,options:[]};}
    $('admin-channel-name').value='';$('admin-channel-url').value='';$('admin-channel-group').value='';$('admin-channel-logo').value='';
    captureAdminDraft();renderAdminFavorites();$('admin-status').textContent=`${radio?'Radio station':'Channel'} added. Publish the shared list to make it visible to everyone.`;
  }
  async function publishAdminFavorites(){
    const status=$('admin-status'),button=$('admin-save'),type=adminFavoriteType;
    if(!adminGitHubToken||!adminFavoritesSha){status.textContent='Connect to GitHub first.';return;}
    captureAdminDraft();button.disabled=true;button.textContent='Publishing…';status.textContent=`Publishing shared ${type==='radio'?'radio stations':'TV channels'} to GitHub…`;
    try{
      const response=await fetch(ADMIN_FAVORITES_API[type],{method:'PUT',headers:{...adminHeaders(),'Content-Type':'application/json'},body:JSON.stringify({message:`Update shared ${type==='radio'?'radio':'TV'} favorites from CoolMagRaTv admin`,content:encodeGitHubFile(adminSharedFavorites),sha:adminFavoritesSha,branch:'main'})});
      const result=await response.json();
      if(!response.ok)throw new Error(response.status===409||response.status===422?'The GitHub file changed since you connected. Disconnect and reconnect to load the latest list, then try again.':result.message||`Publish failed (${response.status}).`);
      adminFavoritesSha=result.content.sha;adminFavoriteDrafts[type]={favorites:adminSharedFavorites,sha:adminFavoritesSha};
      if(type==='radio'){Object.assign(radioFavorites,adminSharedFavorites);persist('coolmag.radio.favorites.v1',radioFavorites);renderRadio();renderHomeRadio();}
      else{Object.assign(tvFavorites,adminSharedFavorites);persist('coolmag.tv.favorites.v1',tvFavorites);renderTV();renderHomeTV();}
      updateFavoriteCounts();renderFavorites();
      status.textContent=`Published ${Object.keys(adminSharedFavorites).length} shared ${type==='radio'?'radio stations':'TV channels'}. Users get the list when they refresh.`;
    }catch(error){status.textContent=error.message||'Could not publish the shared list.';}
    finally{button.disabled=false;button.textContent='Publish shared list';}
  }
  function openAdminFavorites(){closeSettings();$('admin-overlay').hidden=false;document.body.classList.add('admin-open');$('admin-token').focus();}
  function closeAdminFavorites(){
    $('admin-overlay').hidden=true;document.body.classList.remove('admin-open');
  }
  function classifyRadioGenre(station){
    const text=`${station.name||''} ${station.tags||''} ${station.genre||''}`.toLowerCase();
    if(/\b(news|bulletin|current affairs|headlines|weather|business news)\b/.test(text))return 'news';
    if(/\b(talk|spoken|speech|discussion|interview|podcast|chat|debate)\b/.test(text))return 'talks';
    if(/\b(music|song|pop|rock|jazz|classical|dance|electronic|folk|oldies|hits|soul|country)\b/.test(text))return 'music';
    return 'others';
  }
  function updateRadioGenreButtons(){
    document.querySelectorAll('[data-radio-genre]').forEach(button=>{const active=button.dataset.radioGenre===radioGenreFilter;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
  }
  function renderRadio() {
    const target = $('radio-stations');
    const source=showingRadioTopPicks?CURATED_RADIO:showingRadioFavorites?Object.values(radioFavorites).filter(item=>!isTVFavoriteEntry(item)||isRadioFavoriteEntry(item)):radioStations;
    const genreRows=radioGenreFilter==='all'?source:source.filter(station=>classifyRadioGenre(station)===radioGenreFilter);
    const rows=(showingRadioTopPicks?genreRows:sortStationRows(genreRows,radioSortMode,'radio')).slice(0,100);
    const genreName={all:'',music:' · Music',news:' · News',talks:' · Talks',others:' · Others'}[radioGenreFilter]||'';
    const listName=showingRadioTopPicks?'Curated top radio':showingRadioFavorites?'Your radio favorites':`${$('country-select').selectedOptions[0]?.text||'Worldwide'} stations`;
    $('radio-top-picks-button').classList.toggle('curated-active',showingRadioTopPicks);
    $('radio-favorites-button').classList.toggle('active',showingRadioFavorites);
    $('station-list-title').textContent=listName+genreName;updateRadioGenreButtons();
    if (!rows.length) { target.innerHTML=!showingRadioFavorites&&!showingRadioTopPicks&&radioLoading&&radioGenreFilter==='all'?`<div class="station-grid skeleton-grid">${skeletonCards(6)}</div>`:`<div class="empty-state">${showingRadioFavorites?'No saved favorites in this genre yet.':showingRadioTopPicks?'No curated stations in this genre.':'No stations match this genre. Try another country or genre.'}</div>`;renderHomeRadio();renderFavorites();return; }
    target.innerHTML = rows.map((station,index) => {
      const key = safe(radioKey(station)); const favorite = Boolean(radioFavorites[radioKey(station)]);
      const playing = currentRadio && radioKey(currentRadio) === radioKey(station);
      const tags = (station.tags || '').split(',').map(v => v.trim()).filter(Boolean).slice(0,2).join(' · ');
      const meta = [station.country || 'Internet radio', tags || station.codec || 'Live stream',station.bitrate?`${station.bitrate} KBPS`:null].filter(Boolean).join(' · ');
      const art=radioArtwork(station);
      return `<article class="home-channel radio-library-channel ${playing?'active':''}" data-radio-key="${key}" tabindex="0" role="button" aria-label="Play ${safe(station.name)}"><div class="channel-art">${art}<i class="media-badge media-badge-radio" aria-label="Radio station" title="Radio"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="8" width="18" height="12" rx="2"/><path d="m6 5 12-3M7 12h.01M7 16h.01m4-4h6m-6 4h6"/></svg></i></div><button class="tile-star ${favorite?'is-favorite':''}" data-radio-star="${key}" title="${favorite?'Remove':'Add'} favorite" aria-label="${favorite?'Remove':'Add'} favorite">${favorite?'★':'☆'}</button><b>${safe(station.name || 'Unnamed station')}</b><small>${safe(meta)}</small></article>`;
    }).join('');
    bindRadioArtwork(target);
    target.querySelectorAll('.radio-library-channel').forEach(card => {
      const station = rows.find(row => radioKey(row) === card.dataset.radioKey);
      card.addEventListener('click', event => { if (event.target.closest('[data-radio-star]')) return; playRadio(station); });
      card.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); playRadio(station); } });
    });
    target.querySelectorAll('[data-radio-star]').forEach(button => button.addEventListener('click', event => { event.stopPropagation(); const station = rows.find(row => radioKey(row) === button.dataset.radioStar); if (station) toggleRadioFavorite(station); }));
    renderHomeRadio();renderFavorites();
  }

  function syncHomeWeather() {
    $('home-weather-place').textContent=$('weather-place').textContent;
    $('home-weather-temperature').textContent=$('weather-temperature').textContent;
    $('home-weather-summary').textContent=$('weather-summary').textContent;
  }
  function renderHomeRadio() {
    const target=$('home-radio-grid');if(!target)return;
    const rows=radioStations.slice(0,9);
    if(!rows.length){target.innerHTML=radioLoading?`<div class="skeleton-grid">${skeletonCards(4)}</div>`:'<div class="empty-state">Radio stations are unavailable right now.</div>';return;}
    target.innerHTML=rows.map((station,index)=>{
      const key=safe(radioKey(station));const favorite=Boolean(radioFavorites[radioKey(station)]);
      const logo=radioArtwork(station);
      const active=currentRadio&&radioKey(currentRadio)===radioKey(station);
      return `<article class="home-channel home-radio-channel ${active?'active':''}" data-home-radio="${key}" tabindex="0" role="button" aria-label="Play ${safe(station.name||'Radio station')}"><div class="channel-art">${logo}<i class="media-badge media-badge-radio" aria-label="Radio station" title="Radio"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="8" width="18" height="12" rx="2"/><path d="m6 5 12-3M7 12h.01M7 16h.01m4-4h6m-6 4h6"/></svg></i></div><button class="tile-star ${favorite?'is-favorite':''}" data-home-radio-star="${key}" aria-label="Toggle favorite">${favorite?'★':'☆'}</button><b>${safe(station.name||'Radio station')}</b><small>${safe(station.country||'Internet radio')}${station.bitrate?` · ${safe(station.bitrate)} KBPS`:''}</small></article>`;
    }).join('');
    bindRadioArtwork(target);
    target.querySelectorAll('[data-home-radio]').forEach(tile=>{const station=rows.find(item=>radioKey(item)===tile.dataset.homeRadio);tile.addEventListener('click',event=>{if(event.target.closest('[data-home-radio-star]'))return;playRadio(station);});tile.addEventListener('keydown',event=>{if(event.key==='Enter')playRadio(station);});});
    target.querySelectorAll('[data-home-radio-star]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const station=rows.find(item=>radioKey(item)===button.dataset.homeRadioStar);if(station)toggleRadioFavorite(station);}));
  }
  function homeTVRows() {
    return filteredTV();
  }
  function renderHomeTV() {
    const target=$('home-tv-grid');if(!target)return;
    const rows=homeTVRows().slice(0,6);
    if(!rows.length){target.innerHTML=tvLoading?`<div class="skeleton-grid">${skeletonCards(6)}</div>`:'<div class="empty-state">Choose a channel source in Live TV to browse channels.<button class="button primary" data-home-playlists>Open Live TV</button></div>';target.querySelector('[data-home-playlists]')?.addEventListener('click',()=>{setView('tv');loadTV();});return;}
    target.innerHTML=rows.map(row=>`<article class="home-channel ${currentTV?.url===row.url?'active':''}" data-home-tv="${safe(row.url)}" tabindex="0" role="button"><div class="channel-art">${row.logo?`<img src="${safe(row.logo)}" loading="lazy" alt="" onerror="this.style.display='none'">`:'<span>▣</span>'}<i class="media-badge media-badge-tv" aria-label="TV live" title="TV live"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="6" width="18" height="14" rx="2"/><path d="m8 3 4 3 4-3M8 11h8M8 15h5"/></svg></i></div><button class="tile-star ${tvFavorites[tvKey(row)]?'is-favorite':''}" data-home-tv-star="${safe(row.url)}" aria-label="Toggle favorite">${tvFavorites[tvKey(row)]?'★':'☆'}</button><b>${safe(row.name)}</b><small>${safe(row.group||'Live television')}</small></article>`).join('');
    target.querySelectorAll('[data-home-tv]').forEach(card=>{const row=rows.find(item=>item.url===card.dataset.homeTv);card.addEventListener('click',event=>{if(event.target.closest('[data-home-tv-star]'))return;setView('tv');playTV(row);});card.addEventListener('keydown',event=>{if(event.key==='Enter'){setView('tv');playTV(row);}});});
    target.querySelectorAll('[data-home-tv-star]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const row=rows.find(item=>item.url===button.dataset.homeTvStar);if(row)toggleTVFavorite(row);}));
  }
  function setFavoritesMode(mode){
    favoritesMediaMode=mode==='radio'?'radio':'tv';
    $('favorite-radio-panel').hidden=favoritesMediaMode!=='radio';$('favorite-tv-panel').hidden=favoritesMediaMode!=='tv';
    document.querySelectorAll('[data-favorites-mode]').forEach(button=>{const active=button.dataset.favoritesMode===favoritesMediaMode;button.classList.toggle('active',active);button.setAttribute('aria-selected',String(active));});
    try{localStorage.setItem('coolmag.favorites.mode.v1',favoritesMediaMode);}catch{}
  }
  function renderFavorites() {
    const radioTarget=$('favorite-radio-grid'),tvTarget=$('favorite-tv-grid');if(!radioTarget||!tvTarget)return;
    const radios=sortStationRows(Object.values(radioFavorites).filter(item=>!isTVFavoriteEntry(item)||isRadioFavoriteEntry(item)),radioSortMode,'radio'),tvs=sortStationRows(Object.values(tvFavorites).filter(item=>!isRadioFavoriteEntry(item)||isTVFavoriteEntry(item)),tvSortMode,'tv');
    $('favorites-radio-count').textContent=String(radios.length);$('favorites-tv-count').textContent=String(tvs.length);
    radioTarget.innerHTML=radios.length?radios.map(station=>`<article class="favorite-row" data-fav-radio="${safe(radioKey(station))}"><span>♫</span><div><b>${safe(station.name||'Radio station')}</b><small>${safe(station.country||'Internet radio')}</small></div><button class="tile-star is-favorite" data-fav-radio-remove="${safe(radioKey(station))}" aria-label="Remove favorite">★</button></article>`).join(''):'<div class="empty-state">No radio favorites saved yet.</div>';
    tvTarget.innerHTML=tvs.length?tvs.map(station=>`<article class="favorite-row" data-fav-tv="${safe(station.url)}"><span>▣</span><div><b>${safe(station.name||'TV channel')}</b><small>${safe(station.group||'Live television')}</small></div><button class="tile-star is-favorite" data-fav-tv-remove="${safe(station.url)}" aria-label="Remove favorite">★</button></article>`).join(''):'<div class="empty-state">No TV favorites saved yet.</div>';
    radioTarget.querySelectorAll('[data-fav-radio]').forEach(card=>card.addEventListener('click',event=>{if(event.target.closest('[data-fav-radio-remove]'))return;const station=radios.find(item=>radioKey(item)===card.dataset.favRadio);if(station){setView('radio');playRadio(station);}}));
    radioTarget.querySelectorAll('[data-fav-radio-remove]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const station=radios.find(item=>radioKey(item)===button.dataset.favRadioRemove);if(station)toggleRadioFavorite(station);}));
    tvTarget.querySelectorAll('[data-fav-tv]').forEach(card=>card.addEventListener('click',event=>{if(event.target.closest('[data-fav-tv-remove]'))return;const station=tvs.find(item=>item.url===card.dataset.favTv);if(station){setView('tv');playTV(station);}}));
    tvTarget.querySelectorAll('[data-fav-tv-remove]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const station=tvs.find(item=>item.url===button.dataset.favTvRemove);if(station)toggleTVFavorite(station);}));
  }
  function recordRecent(kind,station) {
    const rows=recentHistory[kind];if(!rows||!station)return;
    const key=kind==='tv'?station.url:radioKey(station);
    const saved={...station,playedAt:new Date().toISOString()};
    recentHistory[kind]=[saved,...rows.filter(item=>(kind==='tv'?item.url:radioKey(item))!==key)].slice(0,20);
    try{localStorage.setItem(`coolmag.recent.${kind}.v1`,JSON.stringify(recentHistory[kind]));}catch{}
    renderRecent();
  }
  function renderRecent() {
    const radioTarget=$('recent-radio-grid'),tvTarget=$('recent-tv-grid');if(!radioTarget||!tvTarget)return;
    const render=(kind,target)=>{
      const rows=recentHistory[kind];
      if(!rows.length){target.innerHTML=`<div class="empty-state">No ${kind==='tv'?'TV channels':'radio stations'} played yet.</div>`;return;}
      target.innerHTML=rows.map((item,index)=>{
        const date=item.playedAt?new Date(item.playedAt):null;
        const when=date&&!Number.isNaN(date.getTime())?date.toLocaleString(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):'Recently played';
        const title=item.name||(kind==='tv'?'TV channel':'Radio station');
        const detail=kind==='tv'?(item.group||item.country||'Live television'):(item.country||'Internet radio');
        return `<article class="favorite-row recent-row" data-recent-${kind}="${index}" tabindex="0" role="button"><span>${kind==='tv'?'▣':'♫'}</span><div><b>${safe(title)}</b><small>${safe(detail)} · ${safe(when)}</small></div><i aria-hidden="true">▶</i></article>`;
      }).join('');
      target.querySelectorAll(`[data-recent-${kind}]`).forEach(card=>{
        const play=()=>{const item=recentHistory[kind][Number(card.dataset[`recent${kind==='tv'?'Tv':'Radio'}`])];if(item){if(kind==='tv')playTV(item);else playRadio(item);}};
        card.addEventListener('click',play);card.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();play();}});
      });
    };
    render('radio',radioTarget);render('tv',tvTarget);
  }
  async function searchRadio(preserveFavorites=false) {
    if(!preserveFavorites){showingRadioFavorites=false;showingRadioTopPicks=false;radioFilterTouched=true;}
    radioLoading=true;
    const term = $('radio-search').value.trim(); const country = $('country-select').value;
    $('radio-status').textContent = 'Searching…';
    if(showingRadioFavorites)renderRadio();else $('radio-stations').innerHTML = `<div class="station-grid skeleton-grid">${skeletonCards(6)}</div>`;
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
      radioLoading=false;
      $('radio-status').textContent = `${radioStations.length} stations`;
      renderRadio();
    } catch (error) {
      radioLoading=false;radioStations = []; renderRadio(); $('radio-status').textContent = 'Could not load stations';
      if(!showingRadioFavorites)$('radio-stations').innerHTML = `<div class="empty-state">${safe(error.message)}<br>Check your connection and try again.</div>`;
    }
  }
  function playRadio(station) {
    const url = station?.url_resolved || station?.url;
    if (!url) { toast('This station has no playable stream URL.'); return; }
    stopHomePreview();recordRecent('radio',station);
    stopTV();radioAudio.pause();currentRadio = station;
    radioAudio.src=url;radioAudio.volume=uiSettings.volumeLevel;radioAudio.muted=!uiSettings.volume;
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
  $('radio-sort-select').value=radioSortMode;
  $('radio-sort-select').addEventListener('change',()=>{radioSortMode=$('radio-sort-select').value;persist('coolmag.list.sort.v1',{radio:radioSortMode,tv:tvSortMode});renderRadio();renderFavorites();});
  $('country-select').addEventListener('change',()=>{const name=$('country-select').selectedOptions[0]?.text||'India';loadWeather(name,$('country-select').value==='all'?'':$('country-select').value);searchRadio();});
  $('load-more-radio').addEventListener('click',searchRadio);
  $('radio-favorites-button').addEventListener('click',()=>{radioFilterTouched=true;showingRadioTopPicks=false;showingRadioFavorites=!showingRadioFavorites;renderRadio();if(showingRadioFavorites)$('radio-status').textContent=`${Object.keys(radioFavorites).length} favorites`;else searchRadio();});
  $('radio-top-picks-button').addEventListener('click',()=>{radioFilterTouched=true;showingRadioFavorites=false;showingRadioTopPicks=!showingRadioTopPicks;renderRadio();$('radio-status').textContent=showingRadioTopPicks?`${CURATED_RADIO.length} curated stations`:`${radioStations.length} stations`;if(!showingRadioTopPicks)searchRadio();});
  document.querySelectorAll('[data-radio-genre]').forEach(button=>button.addEventListener('click',()=>{radioGenreFilter=button.dataset.radioGenre||'all';renderRadio();}));
  document.querySelectorAll('[data-favorites-mode]').forEach(button=>button.addEventListener('click',()=>setFavoritesMode(button.dataset.favoritesMode)));
  setFavoritesMode(favoritesMediaMode);

  function tvKey(station) { return station.url; }
  function toggleTVFavorite(station) {
    const key=tvKey(station); if(tvFavorites[key])delete tvFavorites[key];else tvFavorites[key]=station;
    if(!Object.keys(tvFavorites).length)showingTVFavorites=false;
    persist('coolmag.tv.favorites.v1',tvFavorites);updateFavoriteCounts();renderTV();updateTVStar();if(currentView==='home'&&homePreviewStation?.url===key&&!tvFavorites[key])startHomePreview();
  }
  function updateTVStar() {
    const button=$('tv-current-favorite'); const favorite=Boolean(currentTV&&tvFavorites[tvKey(currentTV)]);
    button.classList.toggle('is-favorite',favorite);button.textContent=favorite?'★':'♡';
    button.title=favorite?'Remove from favorites':'Add to favorites';
  }
  function scrollTVDisplayIntoView(){
    requestAnimationFrame(()=>{
      const stage=$('video-stage');
      if(!stage||document.fullscreenElement===stage)return;
      const top=window.scrollY+stage.getBoundingClientRect().top-8;
      window.scrollTo({top:Math.max(0,top),behavior:'smooth'});
    });
  }
  function updateFullscreenTVHeader(){
    const name=$('fullscreen-tv-name'),nextLabel=$('fullscreen-next-favorite');
    if(!name||!nextLabel)return;
    name.textContent=currentTV?.name||'Live TV';
    const favorites=sortStationRows(Object.values(tvFavorites).filter(item=>item&&item.url),tvSortMode,'tv');
    if(!favorites.length){nextLabel.textContent='No saved TV favorites';return;}
    const currentIndex=favorites.findIndex(item=>item.url===currentTV?.url);
    const next=currentIndex<0?favorites[0]:favorites.length>1?favorites[(currentIndex+1)%favorites.length]:null;
    nextLabel.textContent=next?`NEXT FAVORITE · ${next.name||'TV channel'}`:'No other favorite channel';
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
    const country=$('tv-country-select').value;
    const file=country!=='all'?`countries/${country.toLowerCase()}.m3u`:'index.m3u';
    tvLoadController?.abort();const controller=new AbortController();tvLoadController=controller;
    tvLoading=true;tvFilterTouched=true;showingTVFavorites=false;showingTVTopPicks=false;
    const button=$('load-tv');button.disabled=true;button.textContent='Loading…';
    tvStations=[];$('tv-channels').innerHTML=`<div class="channel-list skeleton-grid">${skeletonCards(8)}</div>`;
    $('tv-channel-count').textContent='…';renderHomeTV();
    try{
      const response=await fetch(IPTV_BASE+file,{cache:'no-cache',signal:controller.signal});if(!response.ok)throw new Error(`Playlist could not be fetched (${response.status}).`);
      tvStations=await samplePlaylist(response,20,count=>{if(!showingTVFavorites)$('tv-channel-count').textContent=count?`${count.toLocaleString()} scanned`:'…';});
      tvLoading=false;
      renderTV();toast(`Loaded ${tvStations.length} random channels from across the playlist`);
    }catch(error){if(error.name==='AbortError')return;tvLoading=false;tvStations=[];$('tv-channel-count').textContent='0';$('tv-channels').innerHTML=`<div class="empty-state">${safe(error.message)} Check the connection or select another playlist.</div>`;renderHomeTV();}
    finally{if(tvLoadController===controller){tvLoading=false;tvLoadController=null;button.disabled=false;button.textContent='Load channels';}}
  }
  function filteredTV() {
    if(showingTVTopPicks)return CURATED_TV;
    const rows=showingTVFavorites?Object.values(tvFavorites).filter(item=>!isRadioFavoriteEntry(item)):tvStations.filter(item=>!isRadioFavoriteEntry(item));
    return showingTVFavorites?rows:rows.slice(0,120);
  }
  function renderTVScreenRail(rows){
    const rail=$('tv-screen-rail'),track=$('tv-screen-track');if(!rail||!track)return;
    if(!track.dataset.mouseDragReady){
      let dragState=null;
      track.addEventListener('pointerdown',event=>{if(event.pointerType!=='mouse'||event.button!==0)return;dragState={id:event.pointerId,x:event.clientX,scroll:track.scrollLeft,moved:false};track.setPointerCapture(event.pointerId);track.classList.add('is-dragging');});
      track.addEventListener('pointermove',event=>{if(!dragState||event.pointerId!==dragState.id)return;const delta=event.clientX-dragState.x;if(Math.abs(delta)>4)dragState.moved=true;if(dragState.moved){track.scrollLeft=dragState.scroll-delta;event.preventDefault();}});
      const finishDrag=event=>{if(!dragState||event.pointerId!==dragState.id)return;if(dragState.moved){track.dataset.dragged='true';setTimeout(()=>delete track.dataset.dragged,120);}if(track.hasPointerCapture(event.pointerId))track.releasePointerCapture(event.pointerId);dragState=null;track.classList.remove('is-dragging');};
      track.addEventListener('pointerup',finishDrag);track.addEventListener('pointercancel',finishDrag);
      track.addEventListener('click',event=>{if(track.dataset.dragged==='true'){event.preventDefault();event.stopPropagation();delete track.dataset.dragged;}},true);
      track.dataset.mouseDragReady='true';
    }
    if(!rows.length){rail.hidden=true;track.innerHTML='';return;}
    rail.hidden=false;
    track.innerHTML=rows.slice(0,40).map(row=>`<button class="tv-rail-card ${currentTV?.url===row.url?'is-playing':''}" type="button" data-tv-rail-url="${safe(row.url)}" aria-pressed="${currentTV?.url===row.url?'true':'false'}"><span class="tv-rail-art">${row.logo?`<img src="${safe(row.logo)}" loading="lazy" alt="">`:'<b>TV</b>'}</span><span class="tv-rail-copy"><b>${safe(row.name||'TV channel')}</b><small>${safe(row.country||row.group||'Live TV')}</small></span></button>`).join('');
    track.querySelectorAll('[data-tv-rail-url]').forEach(card=>card.addEventListener('click',()=>{const station=rows.find(row=>row.url===card.dataset.tvRailUrl);if(station)playTV(station);}));
    const active=track.querySelector('.tv-rail-card.is-playing');
    if(active)track.scrollTo({left:Math.max(0,active.offsetLeft-(track.clientWidth-active.offsetWidth)/2),behavior:'smooth'});
  }
  function renderTV() {
    const available=filteredTV();const rows=showingTVTopPicks?available:sortStationRows(available,tvSortMode,'tv');const list=$('tv-channels');
    const favoritesFirst=showingTVFavorites;
    $('tv-channel-count').textContent=rows.length.toLocaleString();
    $('tv-view').classList.toggle('favorites-first',favoritesFirst&&!currentTV);
    $('tv-favorites-button').classList.toggle('active',showingTVFavorites);
    $('tv-top-picks-button').classList.toggle('curated-active',showingTVTopPicks);
    $('tv-favorites-button').innerHTML=`${showingTVFavorites?'★ Your favorites':'♡ Favorites'} <span class="count-pill" id="tv-favorite-count">${Object.keys(tvFavorites).length}</span>`;
    $('tv-list-eyebrow').textContent=showingTVTopPicks?'CURATED TOP PICKS':showingTVFavorites?'YOUR TV FAVORITES':'CHANNEL GUIDE';
    $('tv-list-title').textContent=showingTVTopPicks?'Recommended channels':showingTVFavorites?'Favorite channels':'Live TV';
    renderTVScreenRail(rows);
    if(!rows.length){list.innerHTML=showingTVTopPicks?'<div class="empty-state">The curated channel list is empty.</div>':showingTVFavorites?`<div class="empty-state">${sharedTVFavoritesLoaded?'No TV favorites saved yet. Star channels to keep them here.':'Loading your saved TV favorites…'}</div>`:'<div class="empty-state">No matching channels. Choose a playlist or adjust your search.</div>';renderHomeTV();renderFavorites();return;}
    list.innerHTML=rows.map(row=>`<article class="home-channel tv-channel ${currentTV&&currentTV.url===row.url?'active':''}" data-tv-url="${safe(row.url)}" tabindex="0" role="button"><div class="channel-art">${row.logo?`<img src="${safe(row.logo)}" loading="lazy" alt="" onerror="this.style.display='none'">`:'<span>▣</span>'}<i class="media-badge media-badge-tv" aria-label="TV live" title="TV live"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="6" width="18" height="14" rx="2"/><path d="m8 3 4 3 4-3M8 11h8M8 15h5"/></svg></i></div><button class="tile-star ${tvFavorites[tvKey(row)]?'is-favorite':''}" data-tv-star="${safe(row.url)}" aria-label="Toggle favorite">${tvFavorites[tvKey(row)]?'★':'☆'}</button><b>${safe(row.name)}</b><small>${safe(row.group||'Live television')}</small></article>`).join('');
    list.querySelectorAll('.tv-channel').forEach(item=>{const row=rows.find(candidate=>candidate.url===item.dataset.tvUrl);item.addEventListener('click',event=>{if(event.target.closest('[data-tv-star]'))return;playTV(row);});item.addEventListener('keydown',event=>{if(event.key==='Enter'){playTV(row);}});});
    list.querySelectorAll('[data-tv-star]').forEach(button=>button.addEventListener('click',event=>{event.stopPropagation();const row=rows.find(candidate=>candidate.url===button.dataset.tvStar);if(row)toggleTVFavorite(row);}));
    renderHomeTV();renderFavorites();
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
    if(!station?.url)return;stopHomePreview();recordRecent('tv',station);requestMobileTVLandscape();radioAudio.pause();radioAudio.removeAttribute('src');radioAudio.load();currentRadio=null;currentTV=station;
    updateFullscreenTVHeader();
    if(hls){hls.destroy();hls=null;}tvVideo.pause();tvVideo.removeAttribute('src');tvVideo.load();
    $('video-stage').querySelector('.video-placeholder').classList.add('hidden');$('tv-now-playing').textContent=station.name;
    $('playing-title').textContent=station.name;$('playing-subtitle').textContent=`LIVE TV · ${station.group}`;
    setMediaMetadata(station.name,station.group||'LIVE TV');syncTransport();
    tvVideo.volume=uiSettings.volumeLevel;tvVideo.muted=!uiSettings.volume;
    const isHls=/\.m3u8($|\?)/i.test(station.url);
    if(isHls&&window.Hls&&Hls.isSupported()){
      hls=new Hls({enableWorker:true,lowLatencyMode:false,maxBufferLength:18});hls.loadSource(station.url);hls.attachMedia(tvVideo);
      hls.on(Hls.Events.MANIFEST_PARSED,()=>tvVideo.play().then(syncTransport).catch(()=>toast('Press play on the video to start this channel.')));
      hls.on(Hls.Events.ERROR,(_event,data)=>{if(data.fatal)toast('This channel stream is unavailable or blocked by its host.');});
    }else{tvVideo.src=station.url;tvVideo.play().then(syncTransport).catch(()=>toast('This stream may not be supported in this browser.'));}
    currentRadio=null;renderTV();updateTVStar();scrollTVDisplayIntoView();
  }
  function stopTV(){if(hls){hls.destroy();hls=null;}if(tvVideo){tvVideo.pause();tvVideo.removeAttribute('src');tvVideo.load();}currentTV=null;updateFullscreenTVHeader();if($('tv-now-playing'))$('tv-now-playing').textContent='No channel selected';if($('video-stage'))$('video-stage').querySelector('.video-placeholder').classList.remove('hidden');if($('tv-current-favorite'))updateTVStar();syncTransport();}
  $('load-tv').addEventListener('click',loadTV);
  $('tv-country-select').addEventListener('change',loadTV);
  $('tv-sort-select').value=tvSortMode;
  $('tv-sort-select').addEventListener('change',()=>{tvSortMode=$('tv-sort-select').value;persist('coolmag.list.sort.v1',{radio:radioSortMode,tv:tvSortMode});renderTV();renderFavorites();});
  document.querySelectorAll('[data-tv-rail-scroll]').forEach(button=>button.addEventListener('click',()=>{$('tv-screen-track')?.scrollBy({left:Number(button.dataset.tvRailScroll)*230,behavior:'smooth'});}));
  $('tv-fullscreen').addEventListener('click',toggleTVFullView);
  $('tv-full-home').addEventListener('click',()=>{
    if(currentTV)stopTV();
    document.querySelector('.app-shell').classList.remove('cinema-mode');$('cinema-toggle').setAttribute('aria-pressed','false');
    setView('home');
    if(document.fullscreenElement)document.exitFullscreen?.().catch(()=>{});
  });
  $('tv-full-previous').addEventListener('click',()=>stepFavorite(-1));
  $('tv-full-toggle').addEventListener('click',playPauseActive);
  $('tv-full-next').addEventListener('click',()=>stepFavorite(1));
  $('tv-favorites-button').addEventListener('click',()=>{if(!Object.keys(tvFavorites).length){toast('Star a TV channel to save your first favorite.');return;}tvFilterTouched=true;showingTVTopPicks=false;showingTVFavorites=!showingTVFavorites;renderTV();if(showingTVFavorites)toast(`${Object.keys(tvFavorites).length} saved TV favorites`);});
  $('tv-top-picks-button').addEventListener('click',()=>{tvFilterTouched=true;showingTVFavorites=false;showingTVTopPicks=!showingTVTopPicks;renderTV();if(!showingTVTopPicks)loadTV();});
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
  [radioAudio,tvVideo,$('home-tv-preview')].forEach(media=>['play','pause','progress','loadedmetadata','durationchange','seeked','emptied','timeupdate'].forEach(event=>media.addEventListener(event,syncTransport)));
  document.querySelectorAll('[data-player-icon]').forEach(button=>{const name=button.dataset.playerIcon;if(name!=='play'&&name!=='volume')button.innerHTML=PLAYER_ICONS[name]||'';});
  setupMediaSession();syncTransport();
  $('volume').addEventListener('input',()=>{const value=Number($('volume').value);if(value>0)uiSettings.volumeLevel=value;uiSettings.volume=value>0;applyUserSettings();saveSettings();});
  $('add-stream').addEventListener('click',()=>{const url=prompt('Paste a direct radio stream URL (https:// or http://):');if(!url)return;const clean=url.trim();if(!/^https?:\/\//i.test(clean)){toast('Please enter a valid HTTP or HTTPS stream URL.');return;}const name=prompt('Station name:','My station')?.trim()||'My station';const station={stationuuid:`custom:${clean}`,name,url:clean,url_resolved:clean,country:'Custom stream',tags:'Added by you'};radioFavorites[radioKey(station)]=station;persist('coolmag.radio.favorites.v1',radioFavorites);updateFavoriteCounts();toast('Station saved to your favorites.');if(showingRadioFavorites)renderRadio();});

  function renderNews(){
    $('news-grid').innerHTML=NEWS.map(item=>`<a class="news-card" href="${safe(item.url)}" target="_blank" rel="noopener noreferrer"><div class="news-card-top"><span class="news-logo">${safe(item.initials)}</span><span class="eyebrow">${safe(item.region)}</span></div><div><h3>${safe(item.name)}</h3><p>${safe(item.detail)}</p></div><span class="news-open">OPEN PUBLISHER ↗</span></a>`).join('');
  }
  function updateClock(){try{$('local-time').textContent=new Intl.DateTimeFormat('en-GB',{timeZone:selectedTimezone,hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date());$('local-date').textContent=new Intl.DateTimeFormat('en',{timeZone:selectedTimezone,weekday:'short',day:'2-digit',month:'short'}).format(new Date()).toUpperCase();}catch{$('local-time').textContent=new Date().toLocaleTimeString();}}

  const HOME_NEWS_CACHE_KEY='coolmag.home.news-tickers.v2';
  const HOME_NEWS_TTL=5*60*1000;
  const CITY_NEWS=['Chennai','Kolkata','Delhi','Mumbai','Gangtok','Port Blair'];
  const THE_HINDU_NATIONAL_FEED='https://www.thehindu.com/news/national/feeder/default.rss';
  const GOOGLE_NEWS_FEED=(query,locale='en-IN',region='IN')=>query
    ?`https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=${locale}&gl=${region}&ceid=${region}:${locale.split('-')[0]}`
    :`https://news.google.com/rss/headlines/section/topic/WORLD?hl=${locale}&gl=${region}&ceid=${region}:${locale.split('-')[0]}`;
  function getHomeNewsCache(){try{const value=JSON.parse(localStorage.getItem(HOME_NEWS_CACHE_KEY)||'null');return value&&Date.now()-value.savedAt<HOME_NEWS_TTL?value:null;}catch{return null;}}
  function setHomeNewsCache(value){try{localStorage.setItem(HOME_NEWS_CACHE_KEY,JSON.stringify({...value,savedAt:Date.now()}));}catch{}}
  function tickerLink(item){
    let href='https://news.google.com/';try{const parsed=new URL(item.link||href);if(parsed.protocol==='https:')href=parsed.href;}catch{}
    return `<a class="ticker-headline" href="${safe(href)}" target="_blank" rel="noopener noreferrer">${safe(item.title||'Open latest headlines')}<span aria-hidden="true">↗</span></a>`;
  }
  function paintTicker(id,items,fallbackUrl,label){
    const target=$(id);if(!target)return;
    const visible=items.filter(item=>item&&item.title).slice(0,20);
    const itemsHTML=visible.length?visible.map(tickerLink).join('<i class="ticker-separator" aria-hidden="true"></i>'):`<a class="ticker-headline" href="${safe(fallbackUrl)}" target="_blank" rel="noopener noreferrer">Open latest ${safe(label)} headlines <span aria-hidden="true">↗</span></a>`;
    const estimatedWidth=visible.reduce((total,item)=>total+String(item.title||'').length*7,0)||230;
    const repetitions=Math.max(2,Math.min(6,Math.ceil(900/estimatedWidth)));
    const content=Array.from({length:repetitions},()=>itemsHTML).join('<i class="ticker-separator" aria-hidden="true"></i>');
    target.innerHTML=`<div class="ticker-content">${content}</div><div class="ticker-content" aria-hidden="true">${content}</div>`;
    const track=target.querySelector('.ticker-content');
    target.style.setProperty('--ticker-duration',`${Math.min(420,Math.max(75,(track?.scrollWidth||1800)/34))}s`);
    target.closest('.home-ticker-row')?.classList.toggle('ticker-is-live',visible.length>0);
  }
  async function fetchNewsFeed(url){
    const endpoint=new URL('https://api.rss2json.com/v1/api.json');endpoint.searchParams.set('rss_url',url);
    const response=await fetch(endpoint,{headers:{'Accept':'application/json'},cache:'no-store'});if(!response.ok)throw new Error(`News feed returned ${response.status}`);
    const payload=await response.json();if(payload.status!=='ok'||!Array.isArray(payload.items))throw new Error('News feed is not available');
    return payload.items.map(item=>({title:item.title,link:item.link}));
  }
  function renderHomeNews(data){
    const worldUrl=GOOGLE_NEWS_FEED(null,'en-US','US');
    const nationalUrl=THE_HINDU_NATIONAL_FEED;
    const cityStories=CITY_NEWS.flatMap(city=>{const stories=(data.cities?.[city]||[]).slice(0,1);return stories.length?stories.map(item=>({...item,title:`${city} · ${item.title}`})):[{title:`${city} · Latest headlines`,link:GOOGLE_NEWS_FEED(`${city} India news when:7d`,'en-IN','IN')}];});
    const worldStories=(data.world||[]).slice(0,4);
    const nationalStories=(data.national||[]).slice(0,4);
    const mixedStories=[
      ...(worldStories.length?worldStories.map(item=>({...item,title:`WORLD · ${item.title}`})):[{title:'WORLD · Latest headlines',link:worldUrl}]),
      ...(nationalStories.length?nationalStories.map(item=>({...item,title:`INDIA · ${item.title}`})):[{title:'INDIA · Latest headlines',link:nationalUrl}]),
      ...cityStories
    ];
    paintTicker('ticker-mixed',mixedStories,worldUrl,'breaking news');
  }
  async function loadHomeNewsTickers(){
    const cached=getHomeNewsCache();if(cached)renderHomeNews(cached);
    const feeds=[
      ['world',GOOGLE_NEWS_FEED(null,'en-US','US')],
      ['national',THE_HINDU_NATIONAL_FEED],
      ...CITY_NEWS.map(city=>[city,GOOGLE_NEWS_FEED(`${city} India news when:7d`,'en-IN','IN')])
    ];
    try{
      const results=await Promise.allSettled(feeds.map(([,url])=>fetchNewsFeed(url)));
      const data={...cached,cities:{...(cached?.cities||{})}};
      results.forEach((result,index)=>{if(result.status!=='fulfilled')return;const key=feeds[index][0];if(key==='world'||key==='national')data[key]=result.value;else data.cities[key]=result.value;});
      if(!data.world?.length&&!data.national?.length&&!Object.keys(data.cities).length){if(!cached)renderHomeNews({});return;}
      setHomeNewsCache(data);renderHomeNews(data);
    }catch{if(!cached)renderHomeNews({});}
  }

  function startLiveUserCounter(){
    const display=$('live-user-count');
    if(!PRESENCE_CONFIG.url||!PRESENCE_CONFIG.publishableKey||!window.supabase?.createClient)return;
    try{
      const client=window.supabase.createClient(PRESENCE_CONFIG.url,PRESENCE_CONFIG.publishableKey);
      const clientId=globalThis.crypto?.randomUUID?.()||`visitor-${Date.now()}-${Math.random().toString(36).slice(2)}`;
      const channel=client.channel('coolmag-live-users',{config:{presence:{key:clientId}}});
      const updateCount=()=>{const state=channel.presenceState();display.textContent=String(Object.values(state).filter(sessions=>Array.isArray(sessions)&&sessions.length).length);display.closest('.bento-live').hidden=false;document.body.classList.add('live-count-enabled');};
      channel.on('presence',{event:'sync'},updateCount).subscribe(status=>{
        display.closest('.bento-live')?.setAttribute('data-connected',String(status==='SUBSCRIBED'));
        if(status==='SUBSCRIBED')channel.track({online:true,joinedAt:new Date().toISOString()}).catch(()=>{});
      });
      window.addEventListener('pagehide',()=>channel.untrack().catch(()=>{}),{once:true});
    }catch{}
  }

  applyUserSettings();if(useVolumeDefaults)saveSettings();renderNews();renderRecent();renderHomeRadio();renderHomeTV();updateFavoriteCounts();updateClock();startLiveUserCounter();setInterval(updateClock,1000);loadHomeNewsTickers();setInterval(loadHomeNewsTickers,HOME_NEWS_TTL);startHomePreview();loadSharedFavorites();
  loadCountries().then(()=>{const name=$('country-select').selectedOptions[0]?.text||'India';loadWeather(name,$('country-select').value);searchRadio(true);});
})();
