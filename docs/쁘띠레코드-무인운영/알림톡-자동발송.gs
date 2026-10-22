/**
 * 쁘띠레코드 알림톡 자동 발송 (Google Apps Script + 솔라피 API)
 *
 * 시트 이름: 예약  (1행은 제목, 2행부터 데이터)
 *  A 예약자명 | B 전화 | C 이용일 | D 시작 | E 종료 | F 상품 | G 비밀번호 | H 상태 | I ①발송 | J ②발송 | K 비고
 *
 * 상태 값과 동작 (10분마다 run 실행)
 *  입금확인  → ① 확정·비번 알림톡 발송 → 상태 '확정', I열에 발송 시각
 *  확정      → 종료 시각이 지나면 ② 퇴실 안내 발송 → 상태 '이용완료', J열에 발송 시각
 *  취소      → 아무것도 보내지 않음 (취소되면 상태만 '취소'로 바꾸면 됨)
 *  오류는 K열 비고에 남음
 *
 * 처음 쓸 때
 *  1. 시트 메뉴 확장 프로그램 > Apps Script 에 이 파일을 붙여 넣고 CONFIG 를 채운다.
 *  2. 프로젝트 설정 > 시간대 = Asia/Seoul 확인.
 *  3. setup() 을 한 번 실행해 10분 트리거를 만든다 (권한 허용 창이 뜸).
 *  4. testMode: true 인 동안은 모든 알림톡이 testPhone 으로만 간다. 템플릿 변수명이 승인된 템플릿과
 *     글자 하나까지 같은지 확인한 뒤 false 로 바꾼다.
 */

const CONFIG = {
  apiKey: 'SOLAPI_API_KEY',          // 솔라피 콘솔 > API Key
  apiSecret: 'SOLAPI_API_SECRET',
  pfId: 'KAKAO_PF_ID',               // 솔라피 > 카카오 발신프로필 ID
  tplConfirm: 'TEMPLATE_ID_1',       // ① 확정·비번 템플릿 ID
  tplCheckout: 'TEMPLATE_ID_2',      // ② 퇴실 안내 템플릿 ID
  sheetName: '예약',
  entryLeadMin: 15,                  // 입장 가능 = 시작 15분 전
  testMode: true,                    // true: 전부 testPhone 으로만 발송
  testPhone: '010XXXXXXXX',          // 대표 번호
};

const COL = { name: 1, phone: 2, date: 3, start: 4, end: 5, product: 6, code: 7, status: 8, sent1: 9, sent2: 10, note: 11 };

function setup() {
  ScriptApp.getProjectTriggers().forEach(t => { if (t.getHandlerFunction() === 'run') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('run').timeBased().everyMinutes(10).create();
}

function run() {
  const sh = SpreadsheetApp.getActive().getSheetByName(CONFIG.sheetName);
  if (!sh) throw new Error('시트 "' + CONFIG.sheetName + '" 없음');
  const rows = sh.getDataRange().getValues();
  const now = new Date();

  for (let r = 1; r < rows.length; r++) {
    const row = rows[r];
    const name = row[COL.name - 1], phone = row[COL.phone - 1], date = row[COL.date - 1];
    const start = row[COL.start - 1], end = row[COL.end - 1], code = row[COL.code - 1];
    const status = String(row[COL.status - 1] || '').trim();
    const sent1 = row[COL.sent1 - 1], sent2 = row[COL.sent2 - 1];
    if (!name || !phone || !date) continue;
    const rowNo = r + 1;

    try {
      if (status === '입금확인' && !sent1) {
        if (!code) { sh.getRange(rowNo, COL.note).setValue('비밀번호가 비어 있어 ① 보류'); continue; }
        const startAt = toDate(date, start), endAt = toDate(date, end);
        sendAlimtalk(phone, CONFIG.tplConfirm, {
          '#{고객명}': String(name),
          '#{이용일}': fmtDate(date),
          '#{시작시간}': fmtTime(startAt),
          '#{종료시간}': fmtTime(endAt),
          '#{비밀번호}': String(code),
          '#{입장시간}': fmtTime(addMin(startAt, -CONFIG.entryLeadMin)),
        });
        sh.getRange(rowNo, COL.status).setValue('확정');
        sh.getRange(rowNo, COL.sent1).setValue(now);
        sh.getRange(rowNo, COL.note).setValue('');
      } else if (status === '확정' && !sent2 && now >= toDate(date, end)) {
        sendAlimtalk(phone, CONFIG.tplCheckout, { '#{고객명}': String(name) });
        sh.getRange(rowNo, COL.status).setValue('이용완료');
        sh.getRange(rowNo, COL.sent2).setValue(now);
        sh.getRange(rowNo, COL.note).setValue('');
      }
    } catch (e) {
      sh.getRange(rowNo, COL.note).setValue('오류 ' + fmtTime(now) + ': ' + e.message);
    }
  }
}

function sendAlimtalk(to, templateId, variables) {
  const dest = CONFIG.testMode ? CONFIG.testPhone : String(to).replace(/\D/g, '');
  const body = {
    messages: [{
      to: dest,
      kakaoOptions: { pfId: CONFIG.pfId, templateId: templateId, variables: variables, disableSms: true },
    }],
  };
  const res = UrlFetchApp.fetch('https://api.solapi.com/messages/v4/send-many/detail', {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: authHeader() },
    payload: JSON.stringify(body),
    muteHttpExceptions: true,
  });
  const status = res.getResponseCode();
  if (status >= 300) throw new Error('솔라피 응답 ' + status + ' ' + res.getContentText().slice(0, 200));
  return JSON.parse(res.getContentText());
}

function authHeader() {
  const date = new Date().toISOString();
  const salt = Utilities.getUuid().replace(/-/g, '');
  const sig = Utilities.computeHmacSha256Signature(date + salt, CONFIG.apiSecret)
    .map(b => ('0' + (b & 0xff).toString(16)).slice(-2)).join('');
  return 'HMAC-SHA256 apiKey=' + CONFIG.apiKey + ', date=' + date + ', salt=' + salt + ', signature=' + sig;
}

// ---- 날짜·시간 도우미 (시트 셀이 날짜형이든 "2026-10-25" / "10:00" 글자든 모두 처리) ----
function parseYmd(s) {
  const p = String(s).trim().replace(/[./]/g, '-').split('-').map(Number);
  return new Date(p[0], p[1] - 1, p[2]);
}
function toDate(d, t) {
  const day = (d instanceof Date) ? new Date(d.getFullYear(), d.getMonth(), d.getDate()) : parseYmd(d);
  let h = 0, m = 0;
  if (t instanceof Date) { h = t.getHours(); m = t.getMinutes(); }
  else if (t) { const p = String(t).trim().split(':'); h = Number(p[0]); m = Number(p[1] || 0); }
  day.setHours(h, m, 0, 0);
  return day;
}
function fmtDate(d) {
  const x = (d instanceof Date) ? d : parseYmd(d);
  return (x.getMonth() + 1) + '월 ' + x.getDate() + '일(' + '일월화수목금토'[x.getDay()] + ')';
}
function fmtTime(x) { return Utilities.formatDate(x, 'Asia/Seoul', 'HH:mm'); }
function addMin(x, n) { return new Date(x.getTime() + n * 60000); }
