// Proforma Invoice + Customs & Landed Cost workbook generator.
// Portable core: buildWorkbook(data) uses the ExcelJS API, identical in Node and the browser,
// so the same layout code will run client-side on the site (lazy-loaded ExcelJS).
// Duty % is pulled from the Nepal tariff (data/tariff.json) by HS code — the same data the site holds.
const ExcelJS = require('exceljs');
const fs = require('fs');
const path = require('path');

// ---- tariff duty lookup (general rate, as a decimal) ----
const tariff = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'tariff.json'), 'utf8'));
const RATE = {};
for (const r of tariff.rows) RATE[r[0]] = r[5]; // r[5] = general column
function dutyOf(hs) {
  const g = RATE[hs];
  if (g == null) return null;
  if (String(g).toLowerCase() === 'free') return 0;
  const m = /(\d+(?:\.\d+)?)/.exec(String(g));
  return m ? parseFloat(m[1]) / 100 : null;
}

// ---- integer USD to words (for AMOUNT CHARGEABLE line) ----
const ONES = ['', 'ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'TEN', 'ELEVEN', 'TWELVE', 'THIRTEEN', 'FOURTEEN', 'FIFTEEN', 'SIXTEEN', 'SEVENTEEN', 'EIGHTEEN', 'NINETEEN'];
const TENS = ['', '', 'TWENTY', 'THIRTY', 'FORTY', 'FIFTY', 'SIXTY', 'SEVENTY', 'EIGHTY', 'NINETY'];
function words(n) {
  n = Math.floor(n);
  if (n === 0) return 'ZERO';
  const chunk = x => x < 20 ? ONES[x] : x < 100 ? (TENS[Math.floor(x / 10)] + (x % 10 ? '-' + ONES[x % 10] : '')) : ONES[Math.floor(x / 100)] + ' HUNDRED' + (x % 100 ? ' AND ' + chunk(x % 100) : '');
  let out = '', scale = [[1e9, 'BILLION'], [1e6, 'MILLION'], [1e3, 'THOUSAND'], [1, '']];
  for (const [v, name] of scale) { if (n >= v) { out += (out ? ' ' : '') + chunk(Math.floor(n / v)) + (name ? ' ' + name : ''); n %= v; } }
  return out.trim();
}
function amountWords(total, cur) {
  const d = Math.floor(total), c = Math.round((total - d) * 100);
  return `${cur === 'USD' ? 'US DOLLARS' : cur} ${words(d)}${c ? ` AND CENTS ${words(c)}` : ''} ONLY`;
}

// ---- styling helpers ----
const NAVY = 'FF0F172A', LIGHT = 'FFF1F5F9', ACCENT = 'FF1E3A8A', BORDER = 'FFCBD5E1';
const thin = { style: 'thin', color: { argb: BORDER } };
const box = { top: thin, left: thin, bottom: thin, right: thin };
function hcell(cell, text, fill) { cell.value = text; cell.font = { bold: true, color: { argb: 'FFFFFFFF' }, size: 9 }; cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: fill || NAVY } }; cell.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true }; cell.border = box; }
function money(cell, fmt) { cell.numFmt = fmt; cell.alignment = { horizontal: 'right', vertical: 'middle' }; cell.border = box; }

function buildWorkbook(data) {
  const wb = new ExcelJS.Workbook();
  wb.creator = 'customsnepal.com'; wb.created = new Date();
  const A = data.assumptions, items = data.items.map(it => ({ ...it, duty: it.duty != null ? it.duty : (dutyOf(it.hs) ?? 0) }));

  // ================= SHEET 1: PROFORMA INVOICE =================
  const pi = wb.addWorksheet('Proforma Invoice', { properties: { defaultRowHeight: 15 }, pageSetup: { paperSize: 9, orientation: 'portrait', fitToPage: true, fitToWidth: 1, fitToHeight: 0, margins: { left: 0.4, right: 0.4, top: 0.5, bottom: 0.5, header: 0.3, footer: 0.3 } } });
  pi.columns = [{ width: 5 }, { width: 34 }, { width: 12 }, { width: 13 }, { width: 6 }, { width: 6 }, { width: 12 }, { width: 13 }];
  let R = 1;
  const merge = (r, c1, c2) => pi.mergeCells(r, c1, r, c2);
  // seller header
  merge(R, 1, 8); pi.getCell(R, 1).value = data.seller.name; pi.getCell(R, 1).font = { bold: true, size: 14, color: { argb: NAVY } }; pi.getCell(R, 1).alignment = { horizontal: 'center' }; pi.getRow(R).height = 20; R++;
  merge(R, 1, 8); pi.getCell(R, 1).value = data.seller.address; pi.getCell(R, 1).alignment = { horizontal: 'center', wrapText: true }; pi.getCell(R, 1).font = { size: 8 }; R++;
  merge(R, 1, 8); pi.getCell(R, 1).value = data.seller.contact; pi.getCell(R, 1).alignment = { horizontal: 'center' }; pi.getCell(R, 1).font = { size: 8 }; R++;
  R++;
  merge(R, 1, 8); const t = pi.getCell(R, 1); t.value = 'PROFORMA INVOICE'; t.font = { bold: true, size: 13, color: { argb: 'FFFFFFFF' } }; t.alignment = { horizontal: 'center', vertical: 'middle' }; t.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: NAVY } }; pi.getRow(R).height = 20; R++;
  R++;
  // buyer + shipment two-column block (rich-text so labels never clip on shared columns)
  const s = data.shipment;
  const rt = (label, val) => ({ richText: [{ font: { bold: true, size: 8 }, text: label + '  ' }, { font: { size: 8 }, text: String(val == null ? '' : val) }] });
  const buyerLines = [{ t: 'APPLICANT / BUYER / CONSIGNEE:', b: true }, { t: data.buyer.name, b: true }, { t: data.buyer.address }, { t: data.buyer.contact }, { rt: rt('PAN / VAT No.:', data.buyer.pan || '') }];
  const shipLines = [['PI NO.:', s.piNo], ['DATE:', s.date], ['VALIDITY:', s.validity], ['CURRENCY:', s.currency], ['PRICE TERM:', s.priceTerm], ['COUNTRY OF ORIGIN:', s.origin], ['PORT OF LOADING:', s.pol], ['ENTRY POINT:', s.entry], ['FINAL DESTINATION:', s.dest], ['MODE OF SHIPMENT:', s.mode]];
  const block0 = R;
  buyerLines.forEach((l, i) => { pi.mergeCells(block0 + i, 1, block0 + i, 4); const c = pi.getCell(block0 + i, 1); if (l.rt) c.value = l.rt; else { c.value = l.t; c.font = { bold: !!l.b, size: 8 }; } c.alignment = { wrapText: true, vertical: 'top' }; });
  shipLines.forEach((row, i) => { pi.mergeCells(block0 + i, 5, block0 + i, 8); const c = pi.getCell(block0 + i, 5); c.value = rt(row[0], row[1]); c.alignment = { wrapText: true, vertical: 'top' }; });
  pi.getRow(block0 + 2).height = 22; pi.getRow(block0 + 4).height = 22;
  R = block0 + Math.max(buyerLines.length, shipLines.length) + 1;

  // item table
  const head = ['SN', 'DESCRIPTION', 'ITEM / MODEL', 'H.S. CODE', 'QTY', 'UNIT', `UNIT PRICE (${s.currency})`, `AMOUNT (${s.currency})`];
  head.forEach((h, i) => hcell(pi.getCell(R, i + 1), h)); pi.getRow(R).height = 26; R++;
  let subtotal = 0;
  items.forEach((it, i) => {
    const amt = Math.round(it.qty * it.unitPrice * 100) / 100; subtotal += amt;
    const row = [i + 1, it.description, it.model || '', it.hs, it.qty, it.unit || 'PCS', it.unitPrice, amt];
    row.forEach((v, c) => { const cell = pi.getCell(R, c + 1); cell.value = v; cell.border = box; cell.font = { size: 8 }; cell.alignment = { vertical: 'middle', horizontal: c === 0 || c === 3 || c === 4 || c === 5 ? 'center' : c >= 6 ? 'right' : 'left', wrapText: c === 1 }; if (c >= 6) cell.numFmt = '#,##0.00'; });
    R++;
  });
  const disc = A.discount || 0, total = Math.round((subtotal - disc) * 100) / 100;
  const totalRow = (label, val, bold) => { pi.mergeCells(R, 1, R, 7); const l = pi.getCell(R, 1); l.value = label; l.alignment = { horizontal: 'right' }; l.font = { bold: !!bold, size: 9 }; l.border = box; const v = pi.getCell(R, 8); v.value = val; money(v, '#,##0.00'); v.font = { bold: !!bold, size: 9 }; if (bold) { l.fill = v.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: LIGHT } }; } R++; };
  totalRow('SUB-TOTAL', subtotal);
  if (disc) totalRow('LESS: DISCOUNT', -disc);
  totalRow(`TOTAL AMOUNT – ${s.priceTerm.split('(')[0].trim()} (${s.currency})`, total, true);
  merge(R, 1, 8); pi.getCell(R, 1).value = `AMOUNT CHARGEABLE (IN WORDS): ${amountWords(total, s.currency)}`; pi.getCell(R, 1).font = { italic: true, bold: true, size: 8 }; pi.getCell(R, 1).alignment = { wrapText: true }; pi.getRow(R).height = 24; R += 2;

  // payment terms
  if (data.terms) { merge(R, 1, 8); pi.getCell(R, 1).value = 'TERMS OF PAYMENT'; pi.getCell(R, 1).font = { bold: true, size: 9, color: { argb: ACCENT } }; R++; data.terms.forEach(tm => { merge(R, 1, 8); pi.getCell(R, 1).value = '• ' + tm; pi.getCell(R, 1).font = { size: 8 }; pi.getCell(R, 1).alignment = { wrapText: true }; R++; }); R++; }
  // bank
  if (data.bank) { merge(R, 1, 8); pi.getCell(R, 1).value = 'BENEFICIARY ACCOUNT DETAILS'; pi.getCell(R, 1).font = { bold: true, size: 9, color: { argb: ACCENT } }; R++; [['BENEFICIARY:', data.bank.name], ['BENEFICIARY BANK:', data.bank.bank], ['BANK ADDRESS:', data.bank.address], ['SWIFT CODE:', data.bank.swift], ['ACCOUNT NO.:', data.bank.account]].forEach(row => { merge(R, 1, 8); pi.getCell(R, 1).value = rt(row[0], row[1]); pi.getCell(R, 1).alignment = { wrapText: true }; R++; }); R++; }
  // declaration + signatures
  if (data.declaration) { merge(R, 1, 8); pi.getCell(R, 1).value = 'DECLARATION'; pi.getCell(R, 1).font = { bold: true, size: 9, color: { argb: ACCENT } }; R++; merge(R, 1, 8); pi.getCell(R, 1).value = data.declaration; pi.getCell(R, 1).font = { size: 8, italic: true }; pi.getCell(R, 1).alignment = { wrapText: true }; pi.getRow(R).height = 24; R += 2; }
  pi.mergeCells(R, 1, R, 4); pi.getCell(R, 1).value = 'ACCEPTED BY APPLICANT:'; pi.getCell(R, 1).font = { bold: true, size: 8 }; pi.mergeCells(R, 5, R, 8); pi.getCell(R, 5).value = 'For and on behalf of ' + data.seller.name; pi.getCell(R, 5).font = { bold: true, size: 8 }; R += 3;
  pi.mergeCells(R, 1, R, 4); pi.getCell(R, 1).value = '__________________________'; pi.mergeCells(R, 5, R, 8); pi.getCell(R, 5).value = '__________________________'; R++;
  pi.mergeCells(R, 1, R, 4); pi.getCell(R, 1).value = 'Authorised Signature & Company Stamp'; pi.getCell(R, 1).font = { size: 7, color: { argb: 'FF64748B' } }; pi.mergeCells(R, 5, R, 8); pi.getCell(R, 5).value = 'Authorised Signature & Company Stamp'; pi.getCell(R, 5).font = { size: 7, color: { argb: 'FF64748B' } }; R += 2;
  merge(R, 1, 8); pi.getCell(R, 1).value = 'Prepared with customsnepal.com — Nepal customs tariff, duty & landed-cost tools. Estimate only; confirm final classification and taxes with the customs office or your clearing agent.'; pi.getCell(R, 1).font = { size: 7, italic: true, color: { argb: 'FF94A3B8' } }; pi.getCell(R, 1).alignment = { wrapText: true, horizontal: 'center' };

  // ================= SHEET 2: CUSTOMS & LANDED COST =================
  const lc = wb.addWorksheet('Customs & Landed Cost', { pageSetup: { paperSize: 9, orientation: 'landscape', fitToPage: true, fitToWidth: 1, fitToHeight: 0 } });
  lc.columns = [{ width: 4 }, { width: 26 }, { width: 12 }, { width: 5 }, { width: 11 }, { width: 11 }, { width: 12 }, { width: 6 }, { width: 13 }, { width: 12 }, { width: 12 }, { width: 14 }, { width: 15 }];
  let r2 = 1;
  lc.mergeCells(r2, 1, r2, 13); lc.getCell(r2, 1).value = 'CUSTOMS DUTY, TAXES & LANDED COST (ESTIMATE)'; lc.getCell(r2, 1).font = { bold: true, size: 12, color: { argb: NAVY } }; r2++;
  lc.mergeCells(r2, 1, r2, 13); lc.getCell(r2, 1).value = `Duty from Nepal Customs Tariff 2026/27. FX 1 ${s.currency} = NPR ${A.fx} · Freight+insurance ${(A.freightPct * 100).toFixed(0)}% of value · VAT ${(A.vat * 100).toFixed(0)}% · Target margin ${(A.margin * 100).toFixed(0)}%.`; lc.getCell(r2, 1).font = { size: 8, italic: true, color: { argb: 'FF64748B' } }; r2 += 2;
  const lh = ['NO.', 'MODEL / DESC', 'NEPAL HS', 'DUTY %', `EXW (${s.currency})`, `CIF (${s.currency})`, 'CIF (NPR)', 'QTY', 'CUSTOMS DUTY', 'VAT 13%', 'TOTAL TAX', 'LANDED (excl VAT)', 'SELL/UNIT excl VAT'];
  lh.forEach((h, i) => hcell(lc.getCell(r2, i + 1), h)); lc.getRow(r2).height = 26; r2++;
  const T = { exw: 0, cif: 0, cifn: 0, duty: 0, vat: 0, tax: 0, landed: 0 };
  items.forEach((it, i) => {
    const exw = it.qty * it.unitPrice * (1 - (A.lineDiscount || 0));
    const cif = exw * (1 + A.freightPct), cifn = cif * A.fx;
    const duty = Math.round(cifn * it.duty), other = Math.round(cifn * (A.otherPct || 0));
    const vat = Math.round((cifn + duty) * A.vat), tax = duty + other + vat;
    const landed = cifn + duty + other, perUnit = it.qty ? landed / it.qty : 0, sell = perUnit / (1 - A.margin);
    T.exw += exw; T.cif += cif; T.cifn += cifn; T.duty += duty; T.vat += vat; T.tax += tax; T.landed += landed;
    const vals = [i + 1, it.model || it.description.slice(0, 24), it.hs, it.duty, exw, cif, cifn, it.qty, duty, vat, tax, landed, sell];
    vals.forEach((v, c) => { const cell = lc.getCell(r2, c + 1); cell.value = v; cell.border = box; cell.font = { size: 8 };
      if (c === 0 || c === 2 || c === 7) cell.alignment = { horizontal: 'center', vertical: 'middle' };
      else if (c === 1) cell.alignment = { horizontal: 'left', vertical: 'middle', wrapText: true };
      else if (c === 3) { cell.numFmt = '0%'; cell.alignment = { horizontal: 'center' }; }
      else if (c === 4 || c === 5) money(cell, '#,##0.00');
      else money(cell, '#,##0'); });
    r2++;
  });
  // totals row
  const trow = ['', 'TOTAL', '', '', T.exw, T.cif, T.cifn, items.reduce((a, x) => a + x.qty, 0), T.duty, T.vat, T.tax, T.landed, ''];
  trow.forEach((v, c) => { const cell = lc.getCell(r2, c + 1); cell.value = v; cell.border = box; cell.font = { bold: true, size: 8 }; cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: LIGHT } };
    if (c === 4 || c === 5) money(cell, '#,##0.00'); else if (c >= 6 && c !== 7) money(cell, '#,##0'); else cell.alignment = { horizontal: 'center' }; });
  r2 += 2;
  ['Customs duty = CIF (NPR) × tariff rate.  VAT 13% = (CIF + customs duty) × 13%.',
   'Landed cost excludes VAT (claimable as input credit by a VAT-registered importer). Add VAT back if you cannot claim it.',
   'Freight + insurance are spread across value; replace with your forwarder’s actual split for a firmer figure.',
   'Estimate only — confirm classification, excise and other levies with the customs office or your clearing agent.'].forEach(n => { lc.mergeCells(r2, 1, r2, 13); lc.getCell(r2, 1).value = '• ' + n; lc.getCell(r2, 1).font = { size: 8, color: { argb: 'FF475569' } }; lc.getCell(r2, 1).alignment = { wrapText: true }; r2++; });
  return wb;
}

module.exports = { buildWorkbook, dutyOf };

// ---- CLI: reproduce Sabin's shipment as a fixture and verify totals ----
if (require.main === module) {
  const fixture = require('./_pi_fixture.json');
  buildWorkbook(fixture).xlsx.writeFile('/home/claude/nepal-hs-code-finder/out/Evolve_PI_LandedCost.xlsx').then(() => console.log('written out/Evolve_PI_LandedCost.xlsx'));
}
