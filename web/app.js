import { initialize, isSignedIn, authorization, login, logout, userMessage } from './auth.js';
const $ = (id) => document.getElementById(id);
const root = new URL('../', import.meta.url);
let items = [],
  cursor = null,
  editing = null,
  loading = false;
function notify(message, error = false) {
  $('status').textContent = message;
  $('status').className = error ? 'error' : '';
}
function el(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}
function state(item) {
  return !item.is_active
    ? 'stopped'
    : item.expires_at && item.expires_at <= Date.now() / 1000
      ? 'expired'
      : 'active';
}
const statusNames = { active: '公開中', stopped: '停止中', expired: '期限切れ' };
const shortUrl = (item) => new URL(item.short_id, root).href;
const date = (seconds) =>
  new Intl.DateTimeFormat('ja-JP', { dateStyle: 'short', timeStyle: 'short' }).format(
    seconds * 1000,
  );
async function api(path, options = {}) {
  const response = await fetch(new URL(path, root), {
    ...options,
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
      Authorization: authorization(),
      ...options.headers,
    },
  });
  const data = await response.json().catch(() => ({}));
  if (response.status === 401) {
    $('login').hidden = false;
    throw new Error('ログインの有効期限が切れました。再ログインしてください。');
  }
  if (!response.ok)
    throw new Error(data.error || '処理できませんでした。少し待って再試行してください。');
  return data;
}
async function copy(value) {
  try {
    await navigator.clipboard.writeText(value);
    notify('短縮リンクをコピーしました。');
  } catch {
    $('created').hidden = false;
    $('created-url').value = value;
    $('created-url').focus();
    $('created-url').select();
    notify('コピーできませんでした。選択したリンクを手動でコピーしてください。', true);
  }
}
function render() {
  $('metric-total').textContent = items.length.toLocaleString();
  $('metric-active').textContent = items
    .filter((x) => state(x) === 'active')
    .length.toLocaleString();
  $('metric-clicks').textContent = items.reduce((n, x) => n + x.click_count, 0).toLocaleString();
  const search = $('search').value.toLocaleLowerCase(),
    filter = $('filter').value;
  const shown = items.filter(
    (item) =>
      (filter === 'all' || state(item) === filter) &&
      `${item.title} ${item.short_id} ${item.original_url}`.toLocaleLowerCase().includes(search),
  );
  const fragment = document.createDocumentFragment();
  for (const item of shown) {
    const card = el('article', 'link-card'),
      info = el('div', 'link-info'),
      title = el('h3', 'link-title', item.title || item.short_id),
      badge = el('span', `badge ${state(item)}`, statusNames[state(item)]);
    info.append(title);
    const link = el('a', 'short-link', shortUrl(item).replace(/^https?:\/\//, ''));
    link.href = shortUrl(item);
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    const destination = el('span', 'destination', item.original_url);
    destination.title = item.original_url;
    info.append(link, destination);
    const status = el('div', 'link-state');
    status.append(
      badge,
      el('span', 'link-expiry', item.expires_at ? `期限 ${date(item.expires_at)}` : '期限なし'),
    );
    const count = el('div', 'link-count', item.click_count.toLocaleString());
    count.setAttribute('aria-label', `転送アクセス数 ${item.click_count.toLocaleString()} 回`);
    count.append(el('span', 'count-label', '回'));
    card.append(info, status, count);
    const actions = el('div', 'link-actions');
    const copyButton = el('button', 'quiet', 'コピー');
    copyButton.setAttribute('aria-label', `${item.title || item.short_id}のリンクをコピー`);
    copyButton.onclick = () => copy(shortUrl(item));
    const edit = el('button', 'quiet', '編集');
    edit.setAttribute('aria-label', `${item.title || item.short_id}を編集`);
    edit.onclick = () => openEditor(item);
    const toggle = el('button', 'quiet', item.is_active ? '公開を停止' : '公開を再開');
    toggle.setAttribute(
      'aria-label',
      `${item.title || item.short_id}の${item.is_active ? '公開を停止' : '公開を再開'}`,
    );
    toggle.onclick = async () => {
      if (item.is_active && !confirm('このリンクの公開を停止しますか？ あとから再開できます。'))
        return;
      toggle.disabled = true;
      try {
        const updated = await api(`urls/${item.short_id}`, {
          method: 'PATCH',
          body: JSON.stringify({ version: item.version, is_active: !item.is_active }),
        });
        items = items.map((x) => (x.short_id === updated.short_id ? updated : x));
        render();
        notify(
          updated.is_active
            ? '公開を再開しました。期限切れの場合は期限も変更してください。'
            : 'リンクの公開を停止しました。',
        );
      } catch (error) {
        notify(userMessage(error), true);
        toggle.disabled = false;
      }
    };
    actions.append(copyButton, edit, toggle);
    card.append(actions);
    fragment.append(card);
  }
  if (!shown.length) {
    const empty = el('div', 'empty');
    empty.append(
      el('strong', '', items.length ? '条件に合うリンクがありません' : 'まだリンクがありません'),
      document.createTextNode(
        items.length
          ? '検索条件を変更してください。'
          : '共有したいURLから、最初のリンクを作成できます。',
      ),
    );
    if (!items.length) {
      const createLink = el('a', '', 'リンクを作成');
      createLink.href = '#url';
      empty.append(createLink);
    }
    fragment.append(empty);
  }
  $('links').replaceChildren(fragment);
  $('more').hidden = !cursor;
}
async function load(reset = false) {
  if (loading) return;
  loading = true;
  $('refresh').disabled = true;
  $('more').disabled = true;
  try {
    const page = await api(
      `urls?limit=50${!reset && cursor ? '&cursor=' + encodeURIComponent(cursor) : ''}`,
    );
    const combined = reset ? page.items : [...items, ...page.items];
    items = [...new Map(combined.map((x) => [x.short_id, x])).values()].sort(
      (a, b) => b.created_at - a.created_at || a.short_id.localeCompare(b.short_id),
    );
    cursor = page.next_cursor;
    render();
  } catch (error) {
    notify(userMessage(error), true);
  } finally {
    loading = false;
    $('refresh').disabled = false;
    $('more').disabled = false;
  }
}
$('create-form').onsubmit = async (event) => {
  event.preventDefault();
  const button = $('create-button');
  button.disabled = true;
  try {
    const body = { url: $('url').value, title: $('title').value };
    if ($('alias').value) body.custom_alias = $('alias').value;
    if ($('expiry').value)
      body.expires_at = Math.floor(new Date($('expiry').value).getTime() / 1000);
    const item = await api('urls', { method: 'POST', body: JSON.stringify(body) });
    $('created-url').value = shortUrl(item);
    $('created').hidden = false;
    $('create-form').reset();
    items = [item, ...items.filter((x) => x.short_id !== item.short_id)];
    render();
    notify('短縮リンクを作成しました。');
    $('created-url').focus();
  } catch (error) {
    notify(userMessage(error), true);
    $('status').focus();
  } finally {
    button.disabled = false;
  }
};
function localDate(seconds) {
  if (!seconds) return '';
  const d = new Date(seconds * 1000);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}
function openEditor(item) {
  editing = item;
  $('edit-id').textContent = shortUrl(item);
  $('edit-url').value = item.original_url;
  $('edit-title').value = item.title;
  $('edit-expiry').value = localDate(item.expires_at);
  $('edit-error').textContent = '';
  $('editor').showModal();
}
$('close-editor').onclick = () => $('editor').close();
$('edit-form').onsubmit = async (event) => {
  event.preventDefault();
  $('save-edit').disabled = true;
  try {
    const body = {
      version: editing.version,
      url: $('edit-url').value,
      title: $('edit-title').value,
      expires_at: $('edit-expiry').value
        ? Math.floor(new Date($('edit-expiry').value).getTime() / 1000)
        : null,
    };
    const updated = await api(`urls/${editing.short_id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
    items = items.map((x) => (x.short_id === updated.short_id ? updated : x));
    render();
    $('editor').close();
    notify('リンクを更新しました。');
  } catch (error) {
    $('edit-error').textContent = userMessage(error);
  } finally {
    $('save-edit').disabled = false;
  }
};
$('copy-created').onclick = () => copy($('created-url').value);
$('search').oninput = render;
$('filter').onchange = render;
$('refresh').onclick = () => load(true);
$('more').onclick = () => load();
for (const id of ['login', 'login-main'])
  $(id).onclick = () => login().catch((error) => notify(userMessage(error), true));
$('logout').onclick = logout;
try {
  const config = await initialize(),
    signedIn = isSignedIn();
  $('environment').textContent = config.mode === 'local' ? 'ローカルデモ' : '管理者用';
  $('demo-note').hidden = config.mode !== 'local';
  $('workspace').hidden = !signedIn;
  $('signed-out').hidden = signedIn;
  $('login').hidden = signedIn;
  $('logout').hidden = !signedIn || config.mode === 'local';
  if (signedIn) await load(true);
} catch (error) {
  notify(userMessage(error), true);
  $('signed-out').hidden = false;
  $('login').hidden = false;
}
