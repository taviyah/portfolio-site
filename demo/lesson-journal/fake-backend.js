/*
 * Demo backend for Lesson Journal.
 * The real app runs on Google Apps Script (Calendar + Sheets + Drive in the teacher's own account).
 * This file stands in for `google.script.run` so the same UI runs in any browser with made-up
 * students. Nothing is saved: a page reload starts again from the sample data.
 */
(function () {
  'use strict';

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function ymd(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function parse(s) { var p = s.split('-').map(Number); return new Date(p[0], p[1] - 1, p[2]); }
  function addDays(s, n) { var d = parse(s); d.setDate(d.getDate() + n); return ymd(d); }
  function startMs(date, time) { var t = time.split(':').map(Number); var d = parse(date); d.setHours(t[0], t[1]); return d.getTime(); }
  var LESSON_MS = 45 * 60000;

  var today = new Date();
  var thisSunday = ymd(new Date(today.getFullYear(), today.getMonth(), today.getDate() - today.getDay()));

  var students = [
    { id: 's1', name: 'נועה לוי', hidden: [] },
    { id: 's2', name: 'איתי כהן', hidden: [] },
    { id: 's3', name: 'מאיה אברהם', hidden: [] },
    { id: 's4', name: 'יונתן מזרחי', hidden: [] },
    { id: 's5', name: 'שירה פרץ', hidden: [] },
    { id: 's6', name: 'דניאל ביטון', hidden: [] }
  ];
  // Weekly slot per student: [weekday 0=Sunday, time]
  var slots = { s1: [0, '16:00'], s2: [0, '17:00'], s3: [1, '15:30'], s4: [2, '18:00'], s5: [3, '16:30'], s6: [4, '17:15'] };
  var repertoire = {
    s1: ['Valerie', 'Jolene', 'שיר לשלום'],
    s2: ['Hallelujah', 'אהבת נעוריי'],
    s3: ['Someone Like You', 'Fly Me to the Moon', 'ירושלים של זהב'],
    s4: ['Yesterday', 'Imagine'],
    s5: ['Rolling in the Deep', 'Halo', 'אני ואתה'],
    s6: ['Stand by Me', 'הפרח בגני']
  };
  var notes = [
    'חימום: ליפ טריל וסירנות, 10 דקות.\nעבדנו על נשימה סרעפתית בפראזות ארוכות.\nלבית הבא: לתרגל את הפזמון בקצב איטי, עם הקלטה.',
    'שמענו את ההקלטה מהשבוע. האינטונציה בבית השני השתפרה מאוד.\nעבודה על מעבר לקול ראש בצלילים הגבוהים, בלי לדחוף.\nלבית: תרגיל "נג" על סולם מז׳ורי.',
    'חימום קצר. עבודה על הגייה ברורה של סופי מילים.\nניסינו את השיר טון אחד למטה; נוח יותר. נשאר בטון הזה.\nלבית: לשיר עם הליווי פעמיים ביום.',
    'עבודה על דינמיקה: הבית בשקט, הפזמון מלא.\nתרגול תמיכה בצלילים ארוכים בסוף משפט.\nמוכנים לנסות את השיר מול קהל קטן.'
  ];

  var lessons = {}; // key -> record
  function key(sid, date) { return sid + '|' + date; }

  // Six weeks back and one forward. Older lessons have summaries; last week leaves two missing.
  for (var w = -6; w <= 1; w++) {
    students.forEach(function (s, i) {
      var slot = slots[s.id];
      var date = addDays(thisSunday, w * 7 + slot[0]);
      var k = key(s.id, date);
      var rec = { key: k, studentId: s.id, date: date, time: slot[1], summary: '', absent: false, songs: [], files: [] };
      var past = startMs(date, slot[1]) + LESSON_MS < today.getTime();
      var rep = repertoire[s.id];
      if (past) {
        var missing = (w === 0 && i % 2 === 1) || (w === -1 && i === 2);
        if (w === -3 && i === 4) rec.absent = true;
        else if (!missing) {
          rec.summary = notes[(w + 6 + i) % notes.length];
          rec.songs = [rep[(w + 6) % rep.length]];
          if ((w + i) % 3 === 0) rec.files = [{ id: 'f' + k, name: 'תווים - ' + rec.songs[0] + '.pdf', url: '#', mime: 'application/pdf', size: 120000 }];
        }
      }
      lessons[k] = rec;
    });
  }

  function status(r) {
    if (r.absent) return 'absent';
    if (String(r.summary).trim()) return 'done';
    return startMs(r.date, r.time) + LESSON_MS < Date.now() ? 'missing' : 'planned';
  }
  function student(id) { return students.filter(function (s) { return s.id === id; })[0]; }
  function item(r) {
    var s = student(r.studentId);
    return { key: r.key, studentId: r.studentId, name: s ? s.name : '', date: r.date, time: r.time,
      status: status(r), absent: r.absent, summary: r.summary, songs: r.songs.slice(), files: r.files.slice() };
  }
  function all() { return Object.keys(lessons).map(function (k) { return lessons[k]; }); }
  function byTimeDesc(a, b) { var x = a.date + a.time, y = b.date + b.time; return x < y ? 1 : x > y ? -1 : 0; }
  function songsOf(s) {
    var map = {};
    all().filter(function (r) { return r.studentId === s.id; }).forEach(function (r) {
      r.songs.forEach(function (n) {
        if (s.hidden.indexOf(n) !== -1) return;
        if (!map[n]) map[n] = { name: n, count: 0, last: '' };
        map[n].count++;
        if (r.date > map[n].last) map[n].last = r.date;
      });
    });
    return Object.keys(map).map(function (k) { return map[k]; }).sort(function (a, b) { return a.last < b.last ? 1 : -1; });
  }
  function ensureStudent(name) {
    name = String(name || '').replace(/\s+/g, ' ').trim();
    if (!name) return null;
    var s = students.filter(function (x) { return x.name === name; })[0];
    if (!s) { s = { id: 's' + (students.length + 1) + '_' + Date.now(), name: name, hidden: [] }; students.push(s); }
    return s;
  }
  function upsert(base, changes) {
    var r = lessons[base.key];
    if (!r) { r = lessons[base.key] = { key: base.key, studentId: base.studentId, date: base.date, time: base.time, summary: '', absent: false, songs: [], files: [] }; }
    Object.keys(changes).forEach(function (k) { r[k] = changes[k]; });
    return r;
  }

  var api = {
    getWeek: function (ws) {
      var days = [];
      for (var d = 0; d < 7; d++) {
        var date = addDays(ws, d);
        days.push({ date: date, lessons: all().filter(function (r) { return r.date === date; })
          .sort(function (a, b) { return a.time < b.time ? -1 : 1; }).map(item) });
      }
      return { start: ws, today: ymd(new Date()), days: days };
    },
    getStudents: function () {
      return students.map(function (s) {
        var mine = all().filter(function (r) { return r.studentId === s.id; }).map(item);
        var past = mine.filter(function (it) { return it.status === 'done' || it.status === 'missing'; }).sort(byTimeDesc);
        return { id: s.id, name: s.name, count: past.length, last: past.length ? past[0].date : '',
          missing: mine.filter(function (it) { return it.status === 'missing'; }).length };
      }).sort(function (a, b) { return a.name.localeCompare(b.name, 'he'); });
    },
    getStudent: function (id) {
      var s = student(id);
      if (!s) throw new Error('התלמיד/ה לא נמצא/ה');
      return { id: s.id, name: s.name, history: all().filter(function (r) { return r.studentId === id; }).map(item).sort(byTimeDesc), songs: songsOf(s) };
    },
    getLesson: function (base) {
      var r = lessons[base.key];
      var s = student(base.studentId);
      return { key: base.key, studentId: base.studentId, name: s ? s.name : '', date: base.date, time: base.time,
        summary: r ? r.summary : '', absent: r ? r.absent : false, songs: r ? r.songs.slice() : [], files: r ? r.files.slice() : [],
        prevSongs: s ? songsOf(s).map(function (x) { return x.name; }) : [] };
    },
    saveLesson: function (p) {
      var s = student(p.studentId);
      var songs = (p.songs || []).map(function (x) { return String(x).trim(); }).filter(Boolean);
      if (s) s.hidden = s.hidden.filter(function (h) { return songs.indexOf(h) === -1; });
      var ch = { summary: String(p.summary || ''), songs: songs };
      if (p.absent !== undefined && p.absent !== null) ch.absent = !!p.absent;
      upsert(p, ch);
      return { ok: true };
    },
    hideSong: function (studentId, song) {
      var s = student(studentId);
      if (s && s.hidden.indexOf(song) === -1) s.hidden.push(song);
      return { ok: true };
    },
    uploadFile: function (base, fileName, mimeType) {
      var r = upsert(base, {});
      r.files = r.files.concat([{ id: 'u' + Date.now(), name: fileName, url: '#', mime: mimeType || '', size: 0 }]);
      return r.files.slice();
    },
    removeFile: function (base, fileId) {
      var r = upsert(base, {});
      r.files = r.files.filter(function (f) { return f.id !== fileId; });
      return r.files.slice();
    },
    addLesson: function (p) {
      var s = ensureStudent(p.name);
      if (!s) throw new Error('חסר שם תלמיד/ה');
      var k = s.id + '|' + p.date + '|' + p.time;
      lessons[k] = { key: k, studentId: s.id, date: p.date, time: p.time, summary: '', absent: false, songs: [], files: [] };
      return { ok: true, name: s.name };
    },
    addStudent: function (name) {
      var s = ensureStudent(name);
      if (!s) throw new Error('חסר שם');
      return { id: s.id, name: s.name };
    }
  };

  function runner() {
    var ok = function () {}, ko = function () {};
    var r = new Proxy({}, {
      get: function (_, k) {
        if (k === 'withSuccessHandler') return function (f) { ok = f; return r; };
        if (k === 'withFailureHandler') return function (f) { ko = f; return r; };
        return function () {
          var args = arguments;
          setTimeout(function () {
            try { ok(JSON.parse(JSON.stringify(api[k].apply(null, args)))); }
            catch (e) { ko(e); }
          }, 120);
        };
      }
    });
    return r;
  }
  window.google = { script: { get run() { return runner(); } } };

  // Deep links for screenshots: #lesson opens a finished lesson, #student opens a student page.
  window.addEventListener('load', function () {
    var want = location.hash.slice(1);
    if (want !== 'lesson' && want !== 'student') return;
    function click(el) { if (el) el.dispatchEvent(new MouseEvent('click', { bubbles: true })); }
    function find(sel, text) {
      return Array.prototype.filter.call(document.querySelectorAll(sel), function (e) { return e.textContent.indexOf(text) !== -1; })[0];
    }
    setTimeout(function () {
      if (want === 'lesson') click(find('.chip', 'נועה'));
      else {
        click(document.getElementById('tabStu'));
        setTimeout(function () { click(find('.stu', 'נועה')); }, 400);
      }
    }, 400);
  });
})();
