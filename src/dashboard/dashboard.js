'use strict';
const $ = id => document.getElementById(id);
const titles = {needs_reply: 'Needs reply', review: 'To review', filtered: 'Filtered'};
let token = sessionStorage.getItem('reply-desk-token') || '';
let queue = null, category = 'needs_reply', selected = null;
let fetching = false, detailBusy = false, timer = null;
let pageToken = '', history = [];

function status(message) { $('status').textContent = message; }
async function api(path, body) {
  if (!token) throw new Error('Connect your local backend first.');
  const response = await fetch(path, {method:'POST',
    headers:{'Content-Type':'application/json', Authorization:'Bearer '+token},
    body:JSON.stringify(body), credentials:'omit', cache:'no-store',
    signal:AbortSignal.timeout(600000)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed.');
  return data;
}
function guard(operation) {
  return async event => {
    event?.preventDefault();
    try { await operation(); } catch (error) { status(error.message); }
  };
}
function dateLabel(timestamp) {
  const date = new Date(Number(timestamp));
  return Number.isFinite(date.getTime()) && Number(timestamp) > 0 ? date.toLocaleDateString(undefined,{month:'short',day:'numeric'}) : '';
}
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function render() {
  const search = $('search').value.toLowerCase();
  const items = (queue?.items || []).filter(item => item.category === category &&
    (item.sender+' '+item.subject+' '+item.preview).toLowerCase().includes(search));
  $('list').replaceChildren();
  $('queue-title').textContent = titles[category];
  for (const name of Object.keys(titles)) $('count-'+name).textContent = queue?.counts[name] || 0;
  for (const [id,name] of [['reply','needs_reply'],['review','review'],['filtered','filtered']]) $('metric-'+id).textContent = queue?.counts[name] ?? '—';
  document.querySelectorAll('[data-category]').forEach(button => button.classList.toggle('active', button.dataset.category === category));
  for (const item of items) {
    const button = element('button','message'+(selected?.message_id === item.message_id ? ' selected' : ''));
    const content = element('div','message-content');
    const sender = element('div','sender-row');
    sender.append(element('span','',item.sender || 'Unknown sender'),element('span','',dateLabel(item.timestamp)));
    content.append(sender,element('h3','',item.subject || '(No subject)'),element('p','',item.preview),
      element('p','classification',item.reason));
    button.append(element('span','avatar',(item.sender[0] || '?').toUpperCase()),content);
    button.addEventListener('click',guard(() => selectMessage(item)));
    $('list').append(button);
  }
  if (!items.length) {
    const empty = element('div','empty');
    empty.append(element('span','','✓'),element('h3','',search ? 'No matches on this page.' : category === 'needs_reply' ? 'A little breathing room.' : 'Nothing here right now.'),
      element('p','',search ? 'Try a different sender or subject.' : 'Check To review or browse older inbox pages for more conversations.'));
    $('list').append(empty);
  }
  $('older').disabled = !queue?.next_page_token || fetching || detailBusy;
  $('newer').disabled = !history.length || fetching || detailBusy;
  $('page-label').textContent = 'Inbox page '+(history.length+1);
}
async function refresh(force=false) {
  if (fetching || detailBusy || !token) return;
  fetching = true;
  $('refresh').disabled = true;
  $('live').textContent = 'Syncing';
  try {
    queue = await api('/queue',{refresh:force,page_token:pageToken});
    $('pairing').hidden = true;
    $('demo-mode').hidden = !queue.demo;
    $('live').textContent = 'Auto-sync on';
    $('sync').textContent = `${queue.scanned} messages scanned on this page · ${queue.failed_messages ? queue.failed_messages+' unavailable · ' : ''}Updates every ${queue.refresh_seconds}s`;
    status(queue.failed_messages ? 'Some messages could not be loaded. Refresh to try again.' : 'Inbox updated. Filtered messages remain available for review.');
    if (timer) clearInterval(timer);
    timer = setInterval(() => { if (!document.hidden) guard(() => refresh())(); },queue.refresh_seconds*1000);
  } catch (error) {
    $('live').textContent = 'Sync paused';
    $('pairing').hidden = false;
    throw error;
  } finally {
    fetching = false;
    $('refresh').disabled = false;
    render();
  }
}
async function selectMessage(item) {
  if (detailBusy) { status('Wait for the current summary or draft to finish.'); return; }
  detailBusy = true;
  selected = item;
  $('placeholder').hidden = true;
  $('detail').hidden = false;
  $('subject').textContent = item.subject || '(No subject)';
  $('recipients').textContent = 'From: '+item.sender;
  $('filter-reason').textContent = item.category === 'filtered' ? 'Filtered: '+item.reason : '';
  const gmailId = item.thread_id || item.message_id;
  $('gmail').href = 'https://mail.google.com/mail/u/0/#all/'+encodeURIComponent(gmailId);
  $('overview').textContent = 'Reading the conversation…';
  $('requests').replaceChildren();
  $('deadlines').textContent = '';
  $('original').textContent = '';
  $('intent').value = '';
  discard();
  $('generate').disabled = true;
  status('Preparing a summary with your local model…');
  render();
  if (item.sent_by_user) {
    $('overview').textContent = 'You sent the latest message. Open Gmail to review the conversation.';
    $('original').textContent = item.preview;
    detailBusy = false; render();
    status('Already replied. No new reply draft is needed.');
    return;
  }
  try {
    const data = await api('/message',{message_id:item.message_id});
    $('overview').textContent = data.summary.overview;
    for (const request of data.summary.requests) $('requests').append(element('li','',request));
    $('deadlines').textContent = data.summary.deadlines.length ? 'Deadlines: '+data.summary.deadlines.join('; ') : 'No explicit deadline identified.';
    $('recipients').textContent = 'Reply to: '+data.to.join(', ')+' · '+data.subject;
    $('original').textContent = data.body;
    $('generate').disabled = false;
    status('Summary ready. Add your intent to draft a reply.');
  } catch (error) {
    $('overview').textContent = 'Summary unavailable. Check Gmail authorization and your local model.';
    throw error;
  } finally { detailBusy = false; render(); }
}
function discard() {
  $('draft').value = '';
  $('draft-section').hidden = true;
  $('evaluation').textContent = '';
  $('issues').textContent = '';
}
$('connect').addEventListener('submit',guard(async () => {
  if (fetching || detailBusy) return;
  const nextToken = $('token').value.trim();
  if (nextToken.length < 32) throw new Error('Use the token from private/backend-token.');
  token = nextToken;
  sessionStorage.setItem('reply-desk-token',token);
  $('token').value = '';
  pageToken = ''; history = [];
  await refresh();
}));
$('refresh').addEventListener('click',guard(() => refresh(true)));
$('search').addEventListener('input',render);
for (const button of document.querySelectorAll('[data-category]')) button.addEventListener('click',() => { category = button.dataset.category; render(); });
$('older').addEventListener('click',guard(async () => {
  if (fetching || detailBusy || !queue?.next_page_token) return;
  const previous = pageToken;
  history.push(previous); pageToken = queue.next_page_token;
  try { await refresh(); } catch (error) { pageToken = previous; history.pop(); render(); throw error; }
}));
$('newer').addEventListener('click',guard(async () => {
  if (fetching || detailBusy || !history.length) return;
  const previous = pageToken;
  pageToken = history.pop();
  try { await refresh(); } catch (error) { history.push(pageToken); pageToken = previous; render(); throw error; }
}));
$('generate').addEventListener('click',guard(async () => {
  if (detailBusy || !selected) return;
  if (!$('intent').value.trim()) throw new Error('Add your reply intent first.');
  detailBusy = true;
  $('generate').disabled = true;
  discard();
  status('Drafting and checking your reply…');
  try {
    const result = await api('/generate',{message_id:selected.message_id,intent:$('intent').value});
    $('draft-section').hidden = false;
    $('draft').value = result.draft?.body || '';
    $('evaluation').textContent = result.evaluation_passed ? 'Evaluator passed · review required' : 'Needs your review';
    $('issues').textContent = [...new Set([...(result.issues || []),...(result.draft?.missing_information || [])])].join(' ');
    status(result.draft?.body ? 'Draft ready. Edit it, then copy it into your Gmail reply.' : 'More information is needed. Update your intent and regenerate.');
  } finally { detailBusy = false; $('generate').disabled = false; render(); }
}));
$('draft').addEventListener('input',() => { $('evaluation').textContent = 'Edited · review required'; });
$('copy').addEventListener('click',guard(async () => {
  const body = $('draft').value.trim();
  if (!body) throw new Error('There is no reply to copy.');
  await navigator.clipboard.writeText(body);
  status('Copied. Open Gmail, review recipients and body, then send using Gmail. Nothing was stored in memory.');
}));
$('reject').addEventListener('click',() => { discard(); status('Draft discarded. Nothing was sent or stored.'); });
$('remember').addEventListener('click',guard(async () => {
  await api('/confirm-sent',{message_id:$('sent-id').value.trim()});
  status('Gmail confirmed delivery. Your actual sent wording is now in memory.');
  $('sent-id').value = '';
  await refresh(true);
}));
$('disconnect').addEventListener('click',() => {
  if (detailBusy || fetching) { status('Wait for the current request to finish before disconnecting.'); return; }
  token = ''; sessionStorage.removeItem('reply-desk-token');
  if (timer) clearInterval(timer);
  queue = null; selected = null; pageToken = ''; history = [];
  discard(); $('detail').hidden = true; $('placeholder').hidden = false;
  for (const id of ['subject','overview','recipients','original','deadlines','filter-reason']) $(id).textContent = '';
  $('requests').replaceChildren(); $('intent').value = ''; $('sent-id').value = ''; $('gmail').removeAttribute('href');
  $('pairing').hidden = false; $('demo-mode').hidden = true; $('live').textContent = 'Paused';
  $('sync').textContent = 'Connect to load your inbox.';
  render(); status('Disconnected. Mail and drafts cleared from this dashboard.');
});
if (token) guard(() => refresh())();
