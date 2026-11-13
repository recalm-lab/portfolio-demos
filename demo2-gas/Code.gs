/**
 * Demo 2: Google Apps Script — Sales sheet automation
 *
 * Sheet layout (sheet name: "Sales")
 *   A: date (yyyy/MM/dd)  B: customer  C: item  D: amount (JPY)  E: status
 *   Status values: pending / completed / cancelled (Japanese labels also accepted)
 *
 * What it does:
 *   1. Daily + monthly aggregation into a "Summary" sheet (by status and by month)
 *   2. Status auto-update: rows older than 30 days still "pending" are flagged
 *      in column F ("needs follow-up") instead of being silently changed
 *   3. Error / run logging into a "Log" sheet; optional email notification
 *
 * Setup:
 *   - Paste into Extensions > Apps Script, save
 *   - Run setupTriggers() once to install a daily 09:00 trigger
 *   - (Optional) set NOTIFY_EMAIL to receive a run report
 */
const NOTIFY_EMAIL = ""; // e.g. "you@example.com"
const SALES_SHEET = "Sales";
const SUMMARY_SHEET = "Summary";
const LOG_SHEET = "Log";

function setupTriggers() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger("dailySalesJob").timeBased().everyDays(1).atHour(9).create();
  log_("triggers installed");
}

function dailySalesJob() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sales = ss.getSheetByName(SALES_SHEET);
    if (!sales) throw new Error(`sheet not found: ${SALES_SHEET}`);
    const values = sales.getDataRange().getValues();
    const header = values.shift();

    const byStatus = {};
    const byMonth = {};
    const today = new Date();
    let flagged = 0;

    values.forEach((row, i) => {
      const [date, , , amount, statusRaw] = row;
      const status = normalizeStatus_(statusRaw);
      const amt = Number(amount) || 0;
      byStatus[status] = byStatus[status] || { count: 0, total: 0 };
      byStatus[status].count += 1;
      byStatus[status].total += amt;
      if (date instanceof Date) {
        const key = Utilities.formatDate(date, Session.getScriptTimeZone(), "yyyy-MM");
        byMonth[key] = (byMonth[key] || 0) + amt;
        const ageDays = (today - date) / 86400000;
        if (status === "pending" && ageDays > 30) {
          sales.getRange(i + 2, 6).setValue("needs follow-up");
          flagged += 1;
        }
      }
    });

    writeSummary_(ss, byStatus, byMonth);
    log_(`dailySalesJob ok: rows=${values.length}, flagged=${flagged}`);
    if (NOTIFY_EMAIL) {
      MailApp.sendEmail(NOTIFY_EMAIL, "[Sales sheet] daily job report",
        `Rows: ${values.length}\nFlagged (pending > 30d): ${flagged}\nBy status: ${JSON.stringify(byStatus)}`);
    }
  } catch (e) {
    log_(`dailySalesJob ERROR: ${e.message}`);
    if (NOTIFY_EMAIL) MailApp.sendEmail(NOTIFY_EMAIL, "[Sales sheet] job FAILED", String(e.stack || e));
    throw e;
  }
}

function normalizeStatus_(raw) {
  const s = String(raw || "").trim().toLowerCase();
  if (["completed", "完了", "done"].includes(s)) return "completed";
  if (["cancelled", "キャンセル", "cancel"].includes(s)) return "cancelled";
  return "pending";
}

function writeSummary_(ss, byStatus, byMonth) {
  let sheet = ss.getSheetByName(SUMMARY_SHEET) || ss.insertSheet(SUMMARY_SHEET);
  sheet.clearContents();
  sheet.getRange(1, 1, 1, 3).setValues([["status", "count", "total_jpy"]]);
  const rows = Object.entries(byStatus).map(([k, v]) => [k, v.count, v.total]);
  if (rows.length) sheet.getRange(2, 1, rows.length, 3).setValues(rows);
  const startRow = rows.length + 3;
  sheet.getRange(startRow, 1, 1, 2).setValues([["month", "total_jpy"]]);
  const mrows = Object.entries(byMonth).sort().map(([k, v]) => [k, v]);
  if (mrows.length) sheet.getRange(startRow + 1, 1, mrows.length, 2).setValues(mrows);
}

function log_(message) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(LOG_SHEET) || ss.insertSheet(LOG_SHEET);
  sheet.appendRow([new Date(), message]);
}
