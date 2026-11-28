// 북실북실 · 실제 사람끼리 교류 (Firebase 구글 로그인 + Firestore lite)
// The app (app.html) talks to this file only through window.SOC.
import { initializeApp } from 'firebase/app';
import {
  initializeAuth, indexedDBLocalPersistence, browserLocalPersistence, GoogleAuthProvider,
  signInWithCredential, signOut, deleteUser, connectAuthEmulator, onAuthStateChanged,
} from 'firebase/auth';
import {
  getFirestore, connectFirestoreEmulator, collection, doc, getDoc, getDocs, setDoc, addDoc, updateDoc,
  deleteDoc, deleteField, query, where, orderBy, limit, serverTimestamp, runTransaction, writeBatch,
} from 'firebase/firestore/lite';

const CFG = window.SOC_CFG || {};
const on = !!(CFG.apiKey && CFG.projectId);
let app, auth, db, me = null, prof = null;
const listeners = new Set();
const emit = () => listeners.forEach(f => { try { f(me, prof) } catch (e) {} });

if (on) {
  app = initializeApp(CFG);
  auth = initializeAuth(app, { persistence: [indexedDBLocalPersistence, browserLocalPersistence] });
  db = getFirestore(app);
  if (CFG.emu) {
    connectAuthEmulator(auth, 'http://' + CFG.emu + ':9099', { disableWarnings: true });
    connectFirestoreEmulator(db, CFG.emu, 8080);
  }
  onAuthStateChanged(auth, async u => {
    me = u;
    prof = null;
    if (u) { try { const s = await getDoc(doc(db, 'users', u.uid)); prof = s.exists() ? s.data() : null } catch (e) {} }
    emit();
  });
}

const HANDLE = /^[a-z0-9_]{2,16}$/;
const native = () => window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform() && window.Capacitor.Plugins && window.Capacitor.Plugins.FirebaseAuthentication;
const errMsg = e => {
  const c = (e && e.code) || '';
  if (/cancel|12501|popup-closed/i.test(c + (e && e.message))) return 'cancel';
  if (/network|unavailable|offline/i.test(c)) return 'net';
  if (/permission-denied/.test(c)) return 'denied';
  return c || 'fail';
};

async function idToken() {
  const P = native();
  if (P) {
    const r = await P.signInWithGoogle({ skipNativeAuth: true });
    const t = r && r.credential && r.credential.idToken;
    if (!t) throw Object.assign(new Error('no token'), { code: 'cancel' });
    return t;
  }
  if (CFG.emu && window.SOC_TEST_USER) return JSON.stringify(window.SOC_TEST_USER);
  throw Object.assign(new Error('google sign-in needs the app'), { code: 'web' });
}

// ---------- account ----------
async function login() {
  if (!on) return { ok: false, err: 'off' };
  try {
    const cred = GoogleAuthProvider.credential(await idToken());
    const r = await signInWithCredential(auth, cred);
    me = r.user;
    const s = await getDoc(doc(db, 'users', me.uid));
    prof = s.exists() ? s.data() : null;
    emit();
    return { ok: true, fresh: !prof };
  } catch (e) { return { ok: false, err: errMsg(e) } }
}

// first time only: claim a handle (unique) and write the public profile
async function setup(p) {
  if (!me) return { ok: false, err: 'login' };
  const handle = String(p.handle || '').toLowerCase();
  if (!HANDLE.test(handle)) return { ok: false, err: 'handle' };
  if (p.age14 !== true) return { ok: false, err: 'age' };
  const data = { name: String(p.name || '').slice(0, 20) || handle, handle, bio: String(p.bio || '').slice(0, 160), color: /^#[0-9a-f]{6}$/i.test(p.color || '') ? p.color : '#a89a88', ts: serverTimestamp(), age14: true };
  try {
    await runTransaction(db, async t => {
      const hr = doc(db, 'handles', handle), hs = await t.get(hr);
      if (hs.exists() && hs.data().uid !== me.uid) throw Object.assign(new Error('taken'), { code: 'taken' });
      const old = prof && prof.handle;
      if (old && old !== handle) t.delete(doc(db, 'handles', old));
      if (!hs.exists()) t.set(hr, { uid: me.uid });
      t.set(doc(db, 'users', me.uid), data);
    });
    prof = Object.assign({}, data, { ts: Date.now() });
    emit();
    return { ok: true };
  } catch (e) { return { ok: false, err: e.code === 'taken' ? 'taken' : errMsg(e) } }
}

async function logout() {
  if (!on || !me) return;
  try { const P = native(); if (P) await P.signOut() } catch (e) {}
  await signOut(auth);
  me = null; prof = null; emit();
}

// deletes everything this person put on the server, then the login itself
async function wipe() {
  if (!me) return { ok: false, err: 'login' };
  const uid = me.uid;
  try {
    const mine = await getDocs(query(collection(db, 'posts'), where('uid', '==', uid), limit(500)));
    let b = writeBatch(db), n = 0;
    for (const d of mine.docs) { b.delete(d.ref); if (++n % 400 === 0) { await b.commit(); b = writeBatch(db) } }
    if (prof && prof.handle) b.delete(doc(db, 'handles', prof.handle));
    b.delete(doc(db, 'users', uid));
    await b.commit();
    try { await deleteUser(me) } catch (e) {
      if (e.code === 'auth/requires-recent-login') { await login(); await deleteUser(auth.currentUser) } else throw e;
    }
    try { const P = native(); if (P) await P.signOut() } catch (e) {}
    me = null; prof = null; emit();
    return { ok: true };
  } catch (e) { return { ok: false, err: errMsg(e) } }
}

// ---------- posts ----------
const tsOf = v => v && v.toMillis ? v.toMillis() : (+v || Date.now());
const shape = d => { const x = d.data(); return { id: d.id, uid: x.uid, x: x.x, ts: tsOf(x.ts), r: x.r || '', pu: x.pu || '', q: x.q || null, lk: Object.keys(x.lk || {}), rp: Object.keys(x.rp || {}) } };

async function publish(p) {
  if (!me || !prof) return { ok: false, err: 'login' };
  const x = String(p.x || '').trim().slice(0, 500);
  if (!x) return { ok: false, err: 'empty' };
  const data = { uid: me.uid, x, ts: serverTimestamp(), r: String(p.r || ''), pu: String(p.pu || ''), lk: {}, rp: {} };
  if (p.q && typeof p.q.b === 'string' && p.q.at >= 0) data.q = { b: p.q.b.slice(0, 40), at: +p.q.at | 0 };
  try { const r = await addDoc(collection(db, 'posts'), data); return { ok: true, id: r.id, ts: Date.now() } } catch (e) { return { ok: false, err: errMsg(e) } }
}

async function remove(id) {
  if (!me) return { ok: false };
  try { await deleteDoc(doc(db, 'posts', id)); return { ok: true } } catch (e) { return { ok: false, err: errMsg(e) } }
}

async function like(id, v) {
  if (!me) return { ok: false, err: 'login' };
  try { await updateDoc(doc(db, 'posts', id), { ['lk.' + me.uid]: v ? true : deleteField() }); return { ok: true } } catch (e) { return { ok: false, err: errMsg(e) } }
}

async function report(id, why) {
  if (!me) return { ok: false, err: 'login' };
  try { await updateDoc(doc(db, 'posts', id), { ['rp.' + me.uid]: String(why || '신고').slice(0, 40) }); return { ok: true } } catch (e) { return { ok: false, err: errMsg(e) } }
}

const ucache = {};
async function people(uids) {
  const need = [...new Set(uids)].filter(u => u && !ucache[u]);
  await Promise.all(need.map(async u => { try { const s = await getDoc(doc(db, 'users', u)); ucache[u] = s.exists() ? Object.assign({ uid: u }, s.data(), { ts: 0 }) : { uid: u, gone: 1 } } catch (e) {} }));
  const o = {};
  for (const u of uids) if (ucache[u] && !ucache[u].gone) o[u] = ucache[u];
  return o;
}

// the newest posts plus every reply to my posts, with the people who wrote them
async function pull() {
  if (!me || !prof) return { ok: false, err: 'login' };
  try {
    const [a, b] = await Promise.all([
      getDocs(query(collection(db, 'posts'), orderBy('ts', 'desc'), limit(80))),
      getDocs(query(collection(db, 'posts'), where('pu', '==', me.uid), limit(100))),
    ]);
    const m = new Map();
    for (const d of [...a.docs, ...b.docs]) m.set(d.id, shape(d));
    const posts = [...m.values()];
    const users = await people(posts.map(p => p.uid));
    return { ok: true, me: me.uid, posts, users };
  } catch (e) { return { ok: false, err: errMsg(e) } }
}

async function thread(id) {
  if (!me || !prof) return { ok: false, err: 'login' };
  try {
    const s = await getDocs(query(collection(db, 'posts'), where('r', '==', id), limit(100)));
    const posts = s.docs.map(shape);
    return { ok: true, posts, users: await people(posts.map(p => p.uid)) };
  } catch (e) { return { ok: false, err: errMsg(e) } }
}

async function byUser(uid) {
  if (!me || !prof) return { ok: false, err: 'login' };
  try {
    const s = await getDocs(query(collection(db, 'posts'), where('uid', '==', uid), limit(60)));
    const posts = s.docs.map(shape);
    return { ok: true, posts, users: await people([uid]) };
  } catch (e) { return { ok: false, err: errMsg(e) } }
}

window.SOC = {
  on, login, setup, logout, wipe, publish, remove, like, report, pull, thread, byUser,
  get me() { return me ? { uid: me.uid, email: me.email || '' } : null },
  get prof() { return prof },
  sub(f) { listeners.add(f); return () => listeners.delete(f) },
};
window.dispatchEvent(new Event('soc'));
