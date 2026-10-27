'use strict';


const $ = id => document.getElementById(id);
const API = 'http://127.0.0.1:8765';
let selected = null;
let sourceTab = null;
let busy = false;
$('origin').textContent = chrome.runtime.getURL('').replace(/\/$/, '');

async function api(path, body) {
  const {pairingToken} = await chrome.storage.session.get('pairingToken');
  if (!pairingToken) throw new Error('Pair with your local backend first.');
  const response = await fetch(API + path, {
    method: 'POST', headers: {'Content-Type': 'application/json', Authorization: `Bearer ${pairingToken}`},
    body: JSON.stringify(body), credentials: 'omit', cache: 'no-store',
    //added a 1000 second time-out to keep in account for the worst case in /generate
    signal: AbortSignal.timeout(1000000)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Backend request failed.');
  return result;
}

function action(id, operation) {
  $(id).addEventListener('click', async () => {
    if (busy) return;
    busy = true;
    $('status').textContent = 'Working… Keep this popup open.';
    try { await operation(); }
    catch (error) { $('status').textContent = error.message; }
    finally { busy = false; }
  });
}

async function gmailTab() {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  if (!tab?.url?.startsWith('https://mail.google.com/')) throw new Error('Open a Gmail message first.');
  return tab;
}

function invalidate() {
  selected = null;
  $('generate').disabled = true;
  $('insert').disabled = true;
  $('approved').checked = false;
  $('summary').textContent = '';
  $('address').textContent = '';
  $('draft').value = '';
}
$('messages').addEventListener('change', invalidate);
$('manual').addEventListener('input', invalidate);
$('draft').addEventListener('input', () => { $('approved').checked = false; });
$('intent').addEventListener('input', () => { $('approved').checked = false; });

action('pair', async () => {
  const value = $('token').value.trim();
  if (value.length < 32) throw new Error('Use the token from the private backend token file.');
  await chrome.storage.session.setAccessLevel({accessLevel: 'TRUSTED_CONTEXTS'});
  await chrome.storage.session.set({pairingToken: value});
  $('token').value = '';
  $('status').textContent = 'Paired for this browser session. OAuth stays in the backend.';
});

action('select', async () => {
  invalidate();
  const tab = await gmailTab();
  sourceTab = tab.id;
  const [result] = await chrome.scripting.executeScript({target: {tabId: tab.id}, func: () => {
    // Gmail's DOM is undocumented. Fail closed unless legacy API IDs are present.
    return [...document.querySelectorAll('[data-legacy-message-id]')]
      .filter(node => node.getClientRects().length)
      .map(node => ({id: node.getAttribute('data-legacy-message-id'),
      label: (node.innerText || '').slice(0, 90)}))
      .filter(item => /^[a-f0-9]+$/i.test(item.id));
  }});
  const unique = [...new Map(result.result.map(item => [item.id, item])).values()];
  $('messages').replaceChildren(new Option('Select an incoming email', ''));
  for (const item of unique) $('messages').add(new Option(item.label || item.id, item.id));
  $('status').textContent = unique.length ? 'Choose the incoming email, then summarize it.' : 'No Gmail API IDs found. Use the manual ID fallback.';
});

action('summarize', async () => {
  const tab = await gmailTab();
  sourceTab = tab.id;
  const id = $('manual').value.trim() || $('messages').value;
  invalidate();
  const result = await api('/message', {message_id: id});
  selected = id;
  $('summary').textContent = JSON.stringify(result.summary, null, 2);
  $('address').textContent = `To: ${result.to.join(', ')} | Subject: ${result.subject}`;
  $('generate').disabled = false;
  $('status').textContent = 'Summary loaded from Gmail API. Check the selected message.';
});

action('generate', async () => {
  if (!selected) throw new Error('Summarize a selected email first.');
  $('approved').checked = false;
  $('insert').disabled = true;
  $('draft').value = '';
  const result = await api('/generate', {message_id: selected, intent: $('intent').value});
  $('draft').value = result.draft?.body || '';
  $('insert').disabled = !$('draft').value;
  $('status').textContent = (result.evaluation_passed ? 'Evaluator passed (heuristic). Review before insertion.' : 'Requires review: ' + result.issues.join(' ')) +
    (result.draft?.missing_information?.length ? ' ' + result.draft.missing_information.join(' ') : '');
});

action('insert', async () => {
  if (!$('approved').checked || !$('draft').value.trim()) throw new Error('Review and approve the final reply first.');
  const tab = await gmailTab();
  if (tab.id !== sourceTab) throw new Error('Return to the selected Gmail tab.');
  const [result] = await chrome.scripting.executeScript({target: {tabId: tab.id},
    args: [selected, $('draft').value], func: (messageId, body) => {
      const selectedNodes = [...document.querySelectorAll('[data-legacy-message-id]')]
        .filter(node => node.getAttribute('data-legacy-message-id') === messageId && node.getClientRects().length);
      if (!selectedNodes.length) return 'Selected email is no longer visible. Re-select it.';
      // Restrict to reply composers inside the selected conversation, excluding new compose windows.
      const containers = [...new Set(selectedNodes.map(node => node.closest('.nH') || node.parentElement))];
      const editors = [...new Set(containers.flatMap(node => [...node.querySelectorAll('[contenteditable="true"][role="textbox"]')]))]
        .filter(node => node.getClientRects().length && !node.closest('[role="dialog"]'));
      if (editors.length !== 1) return 'Open exactly one reply composer in this conversation.';
      const editor = editors[0];
      if (editor.innerText.trim()) return 'Reply composer is not empty. Clear it yourself before inserting.';
      editor.focus();
      editor.textContent = body; // Never interpret generated text as HTML.
      editor.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'insertText', data: body}));
      editor.dispatchEvent(new Event('change', {bubbles: true}));
      return '';
    }});
  if (result.result) throw new Error(result.result);
  $('approved').checked = false;
  $('status').textContent = 'Inserted. Check Gmail recipients and body, then use Gmail Send. Nothing was stored in memory.';
});

action('reject', async () => {
  $('draft').value = '';
  $('approved').checked = false;
  $('insert').disabled = true;
  $('status').textContent = 'Draft rejected; nothing was sent or stored.';
});

action('confirm', async () => {
  const result = await api('/confirm-sent', {message_id: $('sentId').value.trim()});
  $('status').textContent = result.stored ? 'Gmail verified SENT; actual sent content is now in memory.' : 'Not stored.';
});
