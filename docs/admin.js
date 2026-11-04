(() => {
  'use strict';

  const API_ROOT = 'https://api.github.com/repos/suppuone/RADIOtv/contents/';
  const FILES = { radio: 'map_favorites.json', tv: 'surak_home_tv_favorites.json' };
  const $ = id => document.getElementById(id);
  const safe = value => String(value ?? '').replace(/[&<>"']/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]));
  let token = '';
  let activeType = 'radio';
  let entries = [];
  let sha = null;
  let dirty = false;
  let nextId = 1;
  let savedJson = {};
  const listStates = {radio:null,tv:null};

  function setStatus(message, kind = '') {
    const el = $('status'); el.textContent = message; el.className = `status ${kind}`.trim();
  }
  function headers() {
    return { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' };
  }
  function decode(content) {
    const binary = atob(content.replace(/\s/g, ''));
    const bytes = Uint8Array.from(binary, ch => ch.charCodeAt(0));
    return new TextDecoder().decode(bytes);
  }
  function encode(value) {
    const bytes = new TextEncoder().encode(JSON.stringify(value, null, 2));
    let binary = ''; for (const byte of bytes) binary += String.fromCharCode(byte);
    return btoa(binary);
  }
  function logoOf(item) { return item.favicon || item.logo || item.image || item.artwork || ''; }
  function countLists() {
    $('radio-count').textContent = activeType === 'radio' ? entries.length : '—';
    $('tv-count').textContent = activeType === 'tv' ? entries.length : '—';
  }
  function markDirty() {
    dirty = true;
    $('publish').disabled = false;
    $('draft-label').textContent = 'Unpublished changes';
    $('publish-note').textContent = 'Your edits are only a draft until you publish them.';
  }
  function syncTypeUI() {
    const radio = activeType === 'radio';
    $('radio-tab').classList.toggle('active', radio); $('radio-tab').setAttribute('aria-selected', String(radio));
    $('tv-tab').classList.toggle('active', !radio); $('tv-tab').setAttribute('aria-selected', String(!radio));
    $('add-heading').textContent = radio ? 'Add radio station' : 'Add TV channel';
    $('name-label').textContent = radio ? 'Station name' : 'Channel name';
    $('country-label').textContent = 'Country';
    $('category-label').textContent = radio ? 'Genre / tags' : 'Category';
    $('new-name').placeholder = radio ? 'BBC World Service' : 'Channel name';
    $('new-url').placeholder = radio ? 'https://…radio stream' : 'https://…m3u8';
    $('new-category').placeholder = radio ? 'Music, News, Talk' : 'News, Entertainment';
    $('add-item').textContent = radio ? '＋ Add station' : '＋ Add channel';
    $('list-heading').textContent = radio ? 'Radio stations' : 'TV channels';
  }
  function filteredRows() {
    const term = $('search').value.trim().toLocaleLowerCase();
    return [...$('item-list').querySelectorAll('[data-row-id]')].filter(row => !term || row.dataset.search.includes(term) || [...row.querySelectorAll('input')].some(input => input.value.toLocaleLowerCase().includes(term)));
  }
  function render() {
    syncTypeUI(); countLists();
    const target = $('item-list');
    if (!entries.length) {
      target.innerHTML = `<div class="empty-state">No shared ${activeType === 'radio' ? 'radio stations' : 'TV channels'} yet. Add one above, or import a JSON list.</div>`;
      $('visible-count').textContent = '0 items'; return;
    }
    target.innerHTML = entries.map(entry => {
      const item = entry.item || {}, radio = activeType === 'radio';
      const logo = logoOf(item);
      const group = radio ? (item.tags || item.genre || '') : (item.group || item.category || '');
      const url = item.url_resolved || item.url || '';
      const haystack = [entry.key, item.name, item.country, group, url, logo].filter(Boolean).join(' ').toLocaleLowerCase();
      return `<article class="item-row" data-row-id="${entry.id}" data-search="${safe(haystack)}">
        <div class="item-row-head"><strong title="${safe(entry.key)}">${safe(item.name || (radio ? 'Radio station' : 'TV channel'))}</strong><button class="remove-button" type="button" data-remove="${entry.id}">Remove</button></div>
        <label class="field"><span>${radio ? 'Station' : 'Channel'} name</span><input data-field="name" value="${safe(item.name || '')}" aria-label="${radio ? 'Station' : 'Channel'} name"></label>
        <label class="field"><span>Country</span><input data-field="country" value="${safe(item.country || '')}" aria-label="Country"></label>
        <label class="field"><span>${radio ? 'Genre / tags' : 'Category'}</span><input data-field="group" value="${safe(group)}" aria-label="${radio ? 'Genre and tags' : 'Category'}"></label>
        <label class="field url-field"><span>Stream URL</span><input data-field="url" type="url" value="${safe(url)}" aria-label="Stream URL"></label>
        <label class="field logo-field"><span>Logo image URL</span><input data-field="logo" type="url" value="${safe(logo)}" aria-label="Logo image URL"></label>
      </article>`;
    }).join('');

    target.querySelectorAll('[data-field]').forEach(input => input.addEventListener('input', () => {
      const row = input.closest('[data-row-id]'), entry = entries.find(item => String(item.id) === row.dataset.rowId);
      if (!entry) return;
      const item = entry.item, value = input.value.trim(), field = input.dataset.field;
      if (field === 'name') item.name = value;
      if (field === 'country') item.country = value;
      if (field === 'group') { if (activeType === 'radio') item.tags = value; else item.group = value; }
      if (field === 'url') { item.url = value; if (activeType === 'radio') item.url_resolved = value; }
      if (field === 'logo') { if (activeType === 'radio') item.favicon = value; else item.logo = value; }
      const title = row.querySelector('.item-row-head strong'); title.textContent = item.name || (activeType === 'radio' ? 'Radio station' : 'TV channel');
      title.title = entry.key;
      row.dataset.search = [entry.key,item.name,item.country,item.tags,item.group,item.url,item.url_resolved,logoOf(item)].filter(Boolean).join(' ').toLocaleLowerCase();
      markDirty(); filterRows();
    }));
    target.querySelectorAll('[data-remove]').forEach(button => button.addEventListener('click', () => {
      const entry = entries.find(item => String(item.id) === button.dataset.remove);
      if (!entry || !window.confirm(`Remove “${entry.item.name || entry.key}” from the shared ${activeType === 'radio' ? 'radio' : 'TV'} list?`)) return;
      entries = entries.filter(item => item.id !== entry.id); markDirty(); render();
    }));
    filterRows();
  }
  function filterRows() {
    const rows = [...$('item-list').querySelectorAll('[data-row-id]')], visible = filteredRows();
    const shown = new Set(visible);
    rows.forEach(row => { row.hidden = !shown.has(row); });
    $('visible-count').textContent = `${visible.length} of ${rows.length} items`;
  }
  function objectFromEntries() {
    const result = {};
    entries.forEach(entry => {
      let key = String(entry.key || entry.item.url_resolved || entry.item.url || entry.item.name || `station-${entry.id}`);
      if (Object.prototype.hasOwnProperty.call(result, key)) { let suffix = 2; while (Object.prototype.hasOwnProperty.call(result, `${key}#${suffix}`)) suffix++; key = `${key}#${suffix}`; }
      result[key] = entry.item;
    });
    return result;
  }
  async function loadType(type) {
    if(type!==activeType&&token)rememberActiveList();
    activeType = type;
    if(listStates[type]){
      const state=listStates[type];entries=state.entries.map(entry=>({id:entry.id,key:entry.key,item:structuredClone(entry.item)}));sha=state.sha;dirty=state.dirty;savedJson=structuredClone(state.savedJson);
      render();$('search').value='';$('workspace').hidden=false;updateDraftState();
      setStatus(`Restored ${entries.length} ${type==='radio'?'radio stations':'TV channels'} from this tab’s draft.`,dirty?'':'success');return;
    }
    sha = null; savedJson = {}; entries=[]; dirty=false;
    render(); $('search').value = ''; $('workspace').hidden = false;
    setStatus(`Loading the shared ${type === 'radio' ? 'radio' : 'TV'} list…`);
    const response = await fetch(`${API_ROOT}${FILES[type]}?ref=main`, {headers: headers(), cache: 'no-store'});
    if (response.status === 404) {
      entries = []; dirty = false; rememberActiveList(); render(); updateDraftState();
      setStatus(`The ${FILES[type]} file is not in the repository yet. Add entries and publish to create it.`, 'success'); return;
    }
    if (!response.ok) {
      const message = response.status === 401 || response.status === 403 ? 'GitHub rejected this token. Confirm it has Contents read/write access to suppuone/RADIOtv.' : `GitHub could not load the list (${response.status}).`;
      throw new Error(message);
    }
    const file = await response.json(), value = JSON.parse(decode(file.content));
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('This JSON file must contain an object of stations or channels.');
    savedJson = value; sha = file.sha;
    entries = Object.entries(value).map(([key, item]) => ({id: nextId++, key, item: item && typeof item === 'object' && !Array.isArray(item) ? structuredClone(item) : {}}));
    dirty = false; rememberActiveList(); render(); updateDraftState();
    setStatus(`Loaded ${entries.length} shared ${type === 'radio' ? 'radio stations' : 'TV channels'}.`, 'success');
  }
  function updateDraftState() {
    $('publish').disabled = !dirty;
    $('draft-label').textContent = dirty ? 'Unpublished changes' : 'No unpublished changes';
    $('publish-note').textContent = dirty ? 'Review your edits, then publish them to GitHub.' : 'Changes are published only when you press Publish.';
  }
  function rememberActiveList() {
    listStates[activeType] = {entries:entries.map(entry=>({id:entry.id,key:entry.key,item:structuredClone(entry.item)})),sha,dirty,savedJson:structuredClone(savedJson)};
  }
  async function connect() {
    const candidate = $('token').value.trim();
    if (!candidate) { setStatus('Paste your GitHub token first.', 'error'); return; }
    token = candidate; $('connect').disabled = true; $('connect').textContent = 'Connecting…';
    try {
      const response = await fetch(`${API_ROOT}${FILES[activeType]}?ref=main`, {headers: headers(), cache: 'no-store'});
      if (!response.ok && response.status !== 404) {
        if (response.status === 401 || response.status === 403) throw new Error('GitHub rejected the token. Check its repository access and Contents read/write permission.');
        throw new Error(`Could not connect to GitHub (${response.status}).`);
      }
      await loadType(activeType);
    } catch (error) { token = ''; $('workspace').hidden = true; setStatus(error.message || 'Could not connect.', 'error'); }
    finally { $('connect').disabled = false; $('connect').textContent = 'Connect & load lists'; }
  }
  function addItem() {
    const name = $('new-name').value.trim(), url = $('new-url').value.trim(), country = $('new-country').value.trim(), group = $('new-category').value.trim(), logo = $('new-logo').value.trim();
    if (!name || !url) { setStatus('Enter both a name and a stream URL.', 'error'); return; }
    if (!/^https?:\/\//i.test(url)) { setStatus('The stream URL must begin with http:// or https://.', 'error'); return; }
    const radio = activeType === 'radio', key = radio ? `custom:${url}` : url;
    if (entries.some(entry => entry.key === key || (entry.item.url === url || entry.item.url_resolved === url))) { setStatus('That stream URL is already in this list.', 'error'); return; }
    const item = radio
      ? {stationuuid:key,name,url,url_resolved:url,country,favicon:logo,tags:group,codec:'',bitrate:0}
      : {name,url,country,group:group || 'Live TV',logo,options:[]};
    entries.unshift({id:nextId++,key,item});
    ['new-name','new-url','new-country','new-category','new-logo'].forEach(id => $(id).value = '');
    markDirty(); render(); setStatus(`${radio ? 'Station' : 'Channel'} added to this draft. Publish to share it.`, 'success');
  }
  function mergeImported(parsed) {
    const incoming = Array.isArray(parsed)
      ? parsed.map((item,index) => [item?.stationuuid || item?.url_resolved || item?.url || `import-${index}`,item])
      : parsed && typeof parsed === 'object' ? Object.entries(parsed) : null;
    if (!incoming) throw new Error('Choose a JSON object or list of stations/channels.');
    let added = 0, updated = 0, skipped = 0;
    incoming.forEach(([rawKey, rawItem]) => {
      if (!rawItem || typeof rawItem !== 'object' || Array.isArray(rawItem)) { skipped++; return; }
      const item = {...rawItem}, url = String(item.url_resolved || item.url || '').trim();
      const existing = entries.find(entry => (url && (entry.item.url === url || entry.item.url_resolved === url)) || (item.name && String(entry.item.name || '').toLocaleLowerCase() === String(item.name).toLocaleLowerCase() && (!item.country || !entry.item.country || String(entry.item.country).toLocaleLowerCase() === String(item.country).toLocaleLowerCase())));
      if (existing) { existing.item = {...existing.item,...item}; if (logoOf(item)) { if (activeType === 'radio') existing.item.favicon = logoOf(item); else existing.item.logo = logoOf(item); } updated++; }
      else { const key = String(rawKey || url || item.name || `import-${nextId}`); entries.push({id:nextId++,key,item}); added++; }
    });
    markDirty(); render(); setStatus(`Imported ${added} new and merged ${updated} existing entries${skipped ? `; skipped ${skipped} invalid rows` : ''}. Publish to save.`, 'success');
  }
  async function importFile(event) {
    const input = event.currentTarget, file = input.files?.[0]; if (!file) return;
    try { mergeImported(JSON.parse(await file.text())); }
    catch (error) { setStatus(error.message || 'Could not import this JSON file.', 'error'); }
    finally { input.value = ''; }
  }
  function importBrowserFavorites() {
    const key = activeType === 'radio' ? 'coolmag.radio.favorites.v1' : 'coolmag.tv.favorites.v1';
    let parsed;
    try { parsed = JSON.parse(localStorage.getItem(key) || '{}'); }
    catch { parsed = {}; }
    if (!parsed || typeof parsed !== 'object') { setStatus('No compatible browser favorites were found.', 'error'); return; }
    try { mergeImported(parsed); }
    catch (error) { setStatus(error.message || 'Could not import browser favorites.', 'error'); }
  }
  function downloadBackup() {
    const blob = new Blob([JSON.stringify(objectFromEntries(), null, 2)], {type:'application/json'});
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = FILES[activeType]; link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }
  async function publish() {
    if (!token) { setStatus('Connect to GitHub before publishing.', 'error'); return; }
    if (!dirty) { setStatus('There are no unpublished edits.', 'success'); return; }
    const button = $('publish'); button.disabled = true; button.textContent = 'Publishing…';
    setStatus(`Publishing ${activeType === 'radio' ? 'radio stations' : 'TV channels'} to GitHub…`);
    try {
      const body = {message:`Update shared ${activeType === 'radio' ? 'radio stations' : 'TV channels'} from COOLmagRaTv Admin`,content:encode(objectFromEntries()),branch:'main'};
      if (sha) body.sha = sha;
      const response = await fetch(`${API_ROOT}${FILES[activeType]}`, {method:'PUT',headers:{...headers(),'Content-Type':'application/json'},body:JSON.stringify(body)});
      const result = await response.json();
      if (!response.ok) {
        if (response.status === 409 || response.status === 422) throw new Error('GitHub reports that this list changed after loading. Reload the list and reapply your edits before publishing.');
        throw new Error(result.message || `Publish failed (${response.status}).`);
      }
      sha = result.content.sha; savedJson = objectFromEntries(); dirty = false; rememberActiveList(); updateDraftState();
      setStatus(`Published ${entries.length} ${activeType === 'radio' ? 'radio stations' : 'TV channels'} to the shared repository.`, 'success');
    } catch (error) { setStatus(error.message || 'Could not publish this list.', 'error'); }
    finally { button.textContent = 'Publish shared list'; button.disabled = !dirty; }
  }
  function disconnect() {
    token = ''; entries = []; sha = null; dirty = false; savedJson = {}; listStates.radio=null;listStates.tv=null;$('token').value = ''; $('workspace').hidden = true; $('item-list').replaceChildren(); updateDraftState(); setStatus('Disconnected. The token was cleared from this tab.');
  }

  $('connect').addEventListener('click', connect);
  $('token').addEventListener('keydown', event => { if (event.key === 'Enter') connect(); });
  $('radio-tab').addEventListener('click', async () => { if (activeType === 'radio' || !token) return; try { await loadType('radio'); } catch (error) { setStatus(error.message || 'Could not load radio stations.', 'error'); } });
  $('tv-tab').addEventListener('click', async () => { if (activeType === 'tv' || !token) return; try { await loadType('tv'); } catch (error) { setStatus(error.message || 'Could not load TV channels.', 'error'); } });
  $('add-item').addEventListener('click', addItem);
  $('search').addEventListener('input', filterRows);
  $('import-browser').addEventListener('click', importBrowserFavorites);
  $('import-json').addEventListener('click', () => $('json-file').click());
  $('json-file').addEventListener('change', importFile);
  $('export-json').addEventListener('click', downloadBackup);
  $('publish').addEventListener('click', publish);
  $('disconnect').addEventListener('click', disconnect);
  window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
})();
