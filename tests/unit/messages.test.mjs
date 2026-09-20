import test from 'node:test';
import assert from 'node:assert/strict';
import { userMessage } from '../../web/auth.js';

test('network failure gives an actionable Japanese message',()=>assert.match(userMessage(new TypeError('Failed to fetch')),/接続.*再|接続.*もう一度/));
test('unknown internal errors are not exposed in the UI',()=>assert.equal(userMessage(new Error('Cannot read properties of undefined')),'処理を完了できませんでした。接続を確認して、もう一度お試しください。'));
test('a specific application error remains useful',()=>assert.equal(userMessage(new Error('この短縮IDは使用済みです。')),'この短縮IDは使用済みです。'));
