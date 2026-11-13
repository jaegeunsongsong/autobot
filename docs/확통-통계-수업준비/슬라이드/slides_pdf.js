// 슬라이드 HTML(16:9, 1280x720)을 PDF로 변환. 사용: node slides_pdf.js <html> <pdf>
const { chromium } = require('playwright');
(async () => {
  const [,, htmlPath, pdfPath] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto('file://' + htmlPath, { waitUntil: 'load' });
  await page.evaluate(async () => { if (window.MathJax && MathJax.startup) await MathJax.startup.promise; });
  await page.waitForTimeout(600);
  const report = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('.slide').forEach((s, i) => {
      const body = s.querySelector('.body');
      const foot = s.querySelector('.foot');
      const over = body.getBoundingClientRect().bottom - foot.getBoundingClientRect().top;
      if (over > -4) out.push({ slide: i + 1, overflowPx: Math.round(over + 4) });
    });
    return out;
  });
  await page.pdf({ path: pdfPath, width: '13.333in', height: '7.5in', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  console.log(JSON.stringify({ pdf: pdfPath, overflow: report, pageErrors: errors }));
  await browser.close();
})();
