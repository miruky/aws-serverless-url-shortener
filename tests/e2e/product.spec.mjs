import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('create, follow, edit, stop and resume a link from the browser',async({page,request})=>{
  await page.goto('/app/');
  await expect(page.getByRole('heading',{name:'短縮リンクを作る'})).toBeVisible();
  await page.getByLabel('リンク先URL',{exact:false}).first().fill('https://example.com?from=browser');
  await page.getByLabel('タイトル',{exact:true}).first().fill('ブラウザ検証');
  await page.getByLabel('短縮ID',{exact:true}).fill('browserDemo');
  await page.getByRole('button',{name:'短縮リンクを作成'}).click();
  await expect(page.getByLabel('作成したリンク')).toHaveValue(/\/browserDemo$/);
  const redirected=await request.get('/browserDemo',{maxRedirects:0});
  expect(redirected.status()).toBe(302);expect(redirected.headers().location).toBe('https://example.com?from=browser');
  await page.getByRole('button',{name:'ブラウザ検証を編集',exact:true}).click();
  await page.getByRole('dialog').getByLabel('タイトル',{exact:true}).fill('編集したリンク');
  await page.getByRole('button',{name:'変更を保存'}).click();
  await expect(page.getByRole('heading',{name:'編集したリンク'})).toBeVisible();
  page.once('dialog',d=>d.accept());
  await page.getByRole('button',{name:'編集したリンクの公開を停止',exact:true}).click();
  await expect(page.getByRole('button',{name:'編集したリンクの公開を再開',exact:true})).toBeVisible();
  expect((await request.get('/browserDemo',{maxRedirects:0})).status()).toBe(404);
  await page.getByRole('button',{name:'編集したリンクの公開を再開',exact:true}).click();
  await expect(page.getByRole('button',{name:'編集したリンクの公開を停止',exact:true})).toBeVisible();
  expect((await request.get('/browserDemo',{maxRedirects:0})).status()).toBe(302);
});

test('anonymous API access and cross-origin writes are rejected',async({request})=>{
  expect((await request.get('/urls')).status()).toBe(401);
  expect((await request.post('/urls',{headers:{Origin:'https://untrusted.example.com'},data:{url:'https://example.com'}})).status()).toBe(403);
  expect((await request.get('/app/config',{headers:{Host:'untrusted.example.com'}})).status()).toBe(403);
});

test('search, status filtering and mobile navigation preserve the current draft',async({page})=>{
  await page.goto('/app/');
  await expect(page.locator('#workspace')).toBeVisible();
  for (const [title, alias, url] of [
    ['プロジェクトのREADME','readme','https://github.com/miruky/aws-serverless-url-shortener'],
    ['公開ドキュメント','guide','https://docs.aws.amazon.com/lambda/'],
    ['以前の案内ページ','archive','https://example.com/previous-guide'],
  ]) {
    await page.getByLabel('リンク先URL',{exact:false}).first().fill(url);
    await page.getByLabel('タイトル',{exact:true}).first().fill(title);
    await page.getByLabel('短縮ID',{exact:true}).fill(alias);
    await page.getByRole('button',{name:'短縮リンクを作成'}).click();
    await expect(page.getByLabel('作成したリンク')).toHaveValue(new RegExp(`/${alias}$`));
  }
  page.once('dialog',d=>d.accept());
  await page.getByRole('button',{name:'以前の案内ページの公開を停止',exact:true}).click();
  await expect(page.getByRole('button',{name:'以前の案内ページの公開を再開',exact:true})).toBeVisible();
  await page.getByLabel('読み込んだリンクを検索').fill('ドキュメント');
  await expect(page.locator('#links article')).toHaveCount(1);
  await expect(page.getByRole('heading',{name:'公開ドキュメント',exact:true})).toBeVisible();
  await page.getByLabel('リンクの状態').selectOption('stopped');
  await expect(page.getByText('条件に合うリンクがありません')).toBeVisible();
  await page.getByLabel('読み込んだリンクを検索').fill('');
  await expect(page.locator('#links article')).toHaveCount(1);
  await expect(page.getByRole('heading',{name:'以前の案内ページ',exact:true})).toBeVisible();
  await page.getByLabel('リンクの状態').selectOption('all');
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('link',{name:'新規リンク'}).click();
  await expect(page.locator('#url')).toBeFocused();
  await expect(page.locator('#url')).toBeInViewport();
  await page.getByLabel('タイトル',{exact:true}).first().fill('未保存のリンク');
  await page.getByRole('link',{name:'一覧に戻る'}).click();
  await expect(page.locator('#library-heading')).toBeInViewport();
  await page.getByRole('button',{name:'公開ドキュメントを編集',exact:true}).click();
  await expect(page.getByRole('dialog',{name:'リンクを編集'})).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toBeHidden();
  await page.getByRole('link',{name:'新規リンク'}).click();
  await expect(page.getByLabel('タイトル',{exact:true}).first()).toHaveValue('未保存のリンク');
});

test('desktop and mobile layout have no serious accessibility findings',async({page})=>{
  await page.goto('/app/');await expect(page.locator('#workspace')).toBeVisible();
  const accessibility=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(accessibility.violations).toEqual([]);
  await page.screenshot({path:'.harness/product-desktop.png',fullPage:true});
  for (const width of [320,768,1024]) {
    await page.setViewportSize({width,height:844});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await expect(page.getByRole('button',{name:'短縮リンクを作成'})).toBeVisible();
  const mobileAccessibility=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(mobileAccessibility.violations).toEqual([]);
  await page.screenshot({path:'.harness/product-mobile.png',fullPage:true});
});

test('stored titles are rendered as text',async({page})=>{
  await page.goto('/app/');await expect(page.locator('#workspace')).toBeVisible();
  const title='<img src=x onerror="window.injected=true">';
  await page.getByLabel('リンク先URL',{exact:false}).first().fill('https://example.com');
  await page.getByLabel('タイトル',{exact:true}).first().fill(title);
  await page.getByLabel('短縮ID',{exact:true}).fill('textOnly');
  await page.getByRole('button',{name:'短縮リンクを作成'}).click();
  await expect(page.getByRole('heading',{name:title,exact:true})).toBeVisible();
  await expect(page.locator('#links img')).toHaveCount(0);
  expect(await page.evaluate(()=>window.injected)).toBeUndefined();
});

test('OAuth callback without matching state never exchanges a code',async({page})=>{
  let exchanges=0;
  await page.route('**/app/config',route=>route.fulfill({json:{mode:'cognito',domain:'https://login.example.com',client_id:'test-client'}}));
  await page.route('https://login.example.com/**',route=>{exchanges++;return route.fulfill({status:400,json:{error:'invalid_grant'}});});
  await page.goto('/app/?code=untrusted&state=wrong');
  await expect(page.locator('#status')).toContainText('ログインの確認に失敗');
  await expect(page.locator('#workspace')).toBeHidden();expect(exchanges).toBe(0);
});

test('OAuth code exchange is one-use and tokens are not persisted',async({page})=>{
  let exchanges=0,exchangeBody='';
  const claims={nonce:'expected-nonce',aud:'test-client',token_use:'id',exp:Math.floor(Date.now()/1000)+900};
  const fakeToken=`header.${Buffer.from(JSON.stringify(claims)).toString('base64url')}.test-signature`;
  await page.route('**/app/config',route=>route.fulfill({json:{mode:'cognito',domain:'https://login.example.com',client_id:'test-client'}}));
  await page.route('https://login.example.com/oauth2/token',route=>{exchanges++;exchangeBody=route.request().postData();return route.fulfill({headers:{'Access-Control-Allow-Origin':'http://127.0.0.1:4311'},json:{id_token:fakeToken,expires_in:900,refresh_token:'not-to-be-stored'}});});
  await page.route('**/urls?*',route=>route.fulfill({json:{items:[],count:0,next_cursor:null}}));
  await page.goto('/app/');
  await page.evaluate(()=>sessionStorage.setItem('shortener.pkce',JSON.stringify({state:'expected-state',nonce:'expected-nonce',verifier:'test-verifier',at:Date.now()})));
  await page.goto('/app/?code=test-code&state=expected-state');
  await expect(page.locator('#workspace')).toBeVisible();
  expect(new URLSearchParams(exchangeBody).get('code_verifier')).toBe('test-verifier');
  expect(await page.evaluate(()=>sessionStorage.length+localStorage.length)).toBe(0);
  await page.goto('/app/?code=test-code&state=expected-state');
  await expect(page.locator('#status')).toContainText('ログインの確認に失敗');expect(exchanges).toBe(1);
});

test('network errors are actionable and the create button becomes usable again',async({page})=>{
  await page.goto('/app/');await expect(page.locator('#workspace')).toBeVisible();
  await page.route('**/urls',route=>route.request().method()==='POST'?route.abort('failed'):route.continue());
  await page.getByLabel('リンク先URL',{exact:false}).first().fill('https://example.com');
  await page.getByRole('button',{name:'短縮リンクを作成'}).click();
  await expect(page.locator('#status')).toContainText('接続を確認');
  await expect(page.getByRole('button',{name:'短縮リンクを作成'})).toBeEnabled();
});
