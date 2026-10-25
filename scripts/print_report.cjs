/** Print the four-page canonical report and reject page overflow before export. */
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');

function playwright() {
  const roots = [process.cwd()];
  if (process.env.PLAYWRIGHT_NODE_MODULES) roots.push(process.env.PLAYWRIGHT_NODE_MODULES);
  try { return require(require.resolve('playwright', {paths: roots})); }
  catch { throw new Error('Install Playwright for the report build, or set PLAYWRIGHT_NODE_MODULES. See report/BUILD.md.'); }
}

(async () => {
  const [source, output] = process.argv.slice(2);
  if (!source || !output) throw new Error('Usage: node scripts/print_report.cjs SOURCE.html OUTPUT.pdf');
  const {chromium} = playwright();
  const options = {headless:true};
  if (process.env.REPORT_BROWSER_CHANNEL) options.channel = process.env.REPORT_BROWSER_CHANNEL;
  else if (fs.existsSync('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')) options.channel = 'chrome';
  const browser = await chromium.launch(options);
  try {
    const page = await browser.newPage({viewport:{width:1000,height:1300}});
    await page.goto(pathToFileURL(source).href);
    await page.emulateMedia({media:'print'});
    await page.evaluate(() => document.fonts.ready);
    const fonts = await page.evaluate(() => ({inter:document.fonts.check('400 12px Inter'),fraunces:document.fonts.check('600 24px Fraunces')}));
    if (!fonts.inter || !fonts.fraunces) throw new Error('Required report fonts failed to load: '+JSON.stringify(fonts));
    const layout = await page.evaluate(() => [...document.querySelectorAll('.page')].map((p,i) => {
      const c=p.querySelector('.content'), f=p.querySelector('footer');
      const r=p.getBoundingClientRect(), cr=c.getBoundingClientRect(), fr=f.getBoundingClientRect();
      const children=[...c.children].map(x=>x.getBoundingClientRect());
      return {page:i+1,contentHeight:c.clientHeight,contentScroll:c.scrollHeight,
        contentOverflow:c.scrollHeight>c.clientHeight+1,
        contentTouchesFooter:children.some(x=>x.bottom>fr.top-5),
        footerOutside:fr.bottom>r.bottom+1,
        horizontalOverflow:p.scrollWidth>p.clientWidth+1,
        usedHeight:Math.round(Math.max(...children.map(x=>x.bottom))-cr.top)};
    }));
    console.log(JSON.stringify({fonts,layout},null,2));
    if (layout.length!==4 || layout.some(x=>x.contentOverflow||x.contentTouchesFooter||x.footerOutside||x.horizontalOverflow)) throw new Error('Report layout does not fit four pages.');
    fs.mkdirSync(path.dirname(output),{recursive:true});
    await page.pdf({path:output,format:'A4',printBackground:true,preferCSSPageSize:true,displayHeaderFooter:false,tagged:true});
    console.log('Created '+output);
  } finally { await browser.close(); }
})().catch(e=>{console.error(e.message);process.exit(1)});
