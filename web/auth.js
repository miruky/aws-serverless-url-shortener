// Tokens stay in memory. Only the one-use PKCE challenge survives the login redirect.
let config,
  token = null,
  expiresAt = 0;
const key = 'shortener.pkce';
const callback = new URL('./', import.meta.url).href;
const encode = (bytes) =>
  btoa(String.fromCharCode(...bytes))
    .replaceAll('+', '-')
    .replaceAll('/', '_')
    .replaceAll('=', '');
const random = () => encode(crypto.getRandomValues(new Uint8Array(32)));

export async function initialize() {
  const response = await fetch(new URL('config', import.meta.url), { cache: 'no-store' });
  if (!response.ok) throw new Error('ログイン設定を取得できません。');
  config = await response.json();
  if (config.mode === 'local') {
    token = config.token;
    expiresAt = Infinity;
    return config;
  }
  const query = new URL(location.href).searchParams;
  if (query.has('error')) {
    history.replaceState(null, '', callback);
    sessionStorage.removeItem(key);
    throw new Error('ログインが完了しませんでした。もう一度お試しください。');
  }
  if (query.has('code')) {
    const saved = JSON.parse(sessionStorage.getItem(key) || 'null');
    sessionStorage.removeItem(key);
    history.replaceState(null, '', callback);
    if (!saved || saved.state !== query.get('state') || Date.now() - saved.at > 10 * 60 * 1000)
      throw new Error('ログインの確認に失敗しました。やり直してください。');
    const result = await fetch(new URL('/oauth2/token', config.domain), {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        client_id: config.client_id,
        code: query.get('code'),
        redirect_uri: callback,
        code_verifier: saved.verifier,
      }),
    });
    if (!result.ok) throw new Error('ログインを完了できませんでした。');
    const data = await result.json();
    const claims = JSON.parse(
      atob(data.id_token.split('.')[1].replaceAll('-', '+').replaceAll('_', '/')),
    );
    if (
      claims.nonce !== saved.nonce ||
      claims.aud !== config.client_id ||
      claims.token_use !== 'id'
    )
      throw new Error('ログイン応答が一致しません。');
    token = data.id_token;
    expiresAt = Math.min(Number(claims.exp) * 1000, Date.now() + Number(data.expires_in) * 1000);
    // Signature, issuer, expiry and audience are validated by API Gateway, not this display code.
  }
  return config;
}
export function isSignedIn() {
  return Boolean(token) && Date.now() < expiresAt;
}
export function authorization() {
  if (!isSignedIn()) throw new Error('ログインの有効期限が切れました。再ログインしてください。');
  return config.mode === 'local' ? `Bearer ${token}` : token;
}
export async function login() {
  if (!config?.domain || !config.client_id) throw new Error('管理者用ログインの設定がありません。');
  const endpoint = new URL('/oauth2/authorize', config.domain);
  if (endpoint.protocol !== 'https:') throw new Error('ログイン先の設定が不正です。');
  const verifier = random(),
    state = random(),
    nonce = random();
  const challenge = encode(
    new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))),
  );
  sessionStorage.setItem(key, JSON.stringify({ verifier, state, nonce, at: Date.now() }));
  endpoint.search = new URLSearchParams({
    client_id: config.client_id,
    response_type: 'code',
    scope: 'openid',
    redirect_uri: callback,
    state,
    nonce,
    code_challenge: challenge,
    code_challenge_method: 'S256',
  });
  location.assign(endpoint);
}
export function logout() {
  token = null;
  expiresAt = 0;
  sessionStorage.removeItem(key);
  if (config.mode === 'local') {
    location.reload();
    return;
  }
  const endpoint = new URL('/logout', config.domain);
  endpoint.search = new URLSearchParams({ client_id: config.client_id, logout_uri: callback });
  location.assign(endpoint);
}

// Shared UI boundary for errors from sign-in and API requests.
export function userMessage(error) {
  const message = typeof error?.message === 'string' ? error.message : '';
  return /[ぁ-んァ-ン一-龯]/.test(message)
    ? message
    : '処理を完了できませんでした。接続を確認して、もう一度お試しください。';
}
