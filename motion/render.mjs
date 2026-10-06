// Render index.html with Playwright.
//
//   node render.mjs beats [--hud] [--at 0.4]   one still per beat (+ contact sheet) at beat + at*beat
//   node render.mjs at 3.2 5.05 ... [--hud]    stills at given seconds
//   node render.mjs full [--workers 4]         4 subframes/frame -> ffmpeg tmix -> 60 fps, muxed with out/soundtrack.wav
//   node render.mjs cues                       dump the page's sound cues to out/cues.json
import { createRequire } from "node:module";
import { spawn, execFileSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); } catch { ({ chromium } = require("/opt/node22/lib/node_modules/playwright")); }

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, "out");
const FPS = 60, SUB = 4, SHUTTER = 0.5; // 4 subframes spread over a 180° shutter
fs.mkdirSync(OUT, { recursive: true });

const args = process.argv.slice(2);
const mode = args[0] || "beats";
const flag = (n, d) => { const i = args.indexOf(n); return i < 0 ? d : (args[i + 1] && !args[i + 1].startsWith("--") ? args[i + 1] : true); };

const beats = JSON.parse(fs.readFileSync(path.join(OUT, "beats.json"), "utf8"));
const PERIOD = beats.period;

// tiny static server (fonts can't load from file://)
const TYPES = { ".html": "text/html", ".woff2": "font/woff2", ".js": "text/javascript", ".css": "text/css" };
const server = http.createServer((req, res) => {
  const p = path.join(HERE, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!p.startsWith(HERE) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": TYPES[path.extname(p)] || "application/octet-stream" });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, "127.0.0.1", r));
const URL0 = `http://127.0.0.1:${server.address().port}/index.html`;

const browser = await chromium.launch();
async function openPage(hud) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1440 }, deviceScaleFactor: 1 });
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  await page.addInitScript(p => { window.BEAT_PERIOD = p; }, PERIOD);
  await page.goto(URL0 + (hud ? "?hud" : ""));
  await page.waitForFunction(() => window.READY === true);
  const ok = await page.evaluate(() => document.fonts.check('500 20px "Geist"'));
  if (!ok) throw new Error("Geist did not load");
  return page;
}
const shot = async (page, t) => { await page.evaluate(t => window.seek(t), t); return page.screenshot({ type: "png" }); };

try {
  if (mode === "cues") {
    const page = await openPage(false);
    const cues = await page.evaluate(() => ({ loop: window.LOOP, beat: window.BEAT, cues: window.CUES }));
    fs.writeFileSync(path.join(OUT, "cues.json"), JSON.stringify(cues, null, 1));
    console.log(`${cues.cues.length} cues -> out/cues.json`);
  } else if (mode === "beats" || mode === "at") {
    const page = await openPage(flag("--hud", false));
    const dir = path.join(OUT, "stills"); fs.mkdirSync(dir, { recursive: true });
    const at = parseFloat(flag("--at", "0.4"));
    const times = mode === "beats"
      ? Array.from({ length: 28 }, (_, i) => (i + at) * PERIOD)
      : args.slice(1).filter(a => !a.startsWith("--") && !isNaN(parseFloat(a))).map(Number);
    const files = [];
    for (const [i, t] of times.entries()) {
      const f = path.join(dir, mode === "beats" ? `beat_${String(i + 1).padStart(2, "0")}.png` : `t_${t.toFixed(3)}.png`);
      fs.writeFileSync(f, await shot(page, t)); files.push(f);
    }
    if (mode === "beats") {
      execFileSync("ffmpeg", ["-v", "error", "-y", "-framerate", "1", "-i", path.join(dir, "beat_%02d.png"),
        "-vf", "scale=360:360,tile=7x4:padding=6:color=white", "-frames:v", "1", path.join(OUT, `contact_${at}.png`)]);
      console.log(`28 stills + out/contact_${at}.png`);
    } else console.log(files.join("\n"));
  } else if (mode === "full") {
    const frames = Math.round(beats.loop_seconds * FPS);
    const workers = parseInt(flag("--workers", "4"), 10);
    const per = Math.ceil(frames / workers);
    const t0 = Date.now(); let done = 0;
    const chunk = async w => {
      const a = w * per, z = Math.min(frames, a + per);
      if (a >= z) return null;
      const page = await openPage(false);
      const file = path.join(OUT, `chunk_${w}.mkv`);
      // tmix averages the 4 subframes ending at each 4th input frame; select keeps exactly those.
      const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS * SUB), "-i", "-",
        "-vf", `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/(${FPS}*TB)`,
        "-r", String(FPS), "-c:v", "libx264rgb", "-qp", "0", "-preset", "ultrafast", file], { stdio: ["pipe", "inherit", "inherit"] });
      for (let f = a; f < z; f++) {
        for (let j = 0; j < SUB; j++) {
          const t = (f + (j - (SUB - 1) / 2) * (SHUTTER / SUB)) / FPS;
          const buf = await shot(page, t);
          if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
        }
        if (++done % 60 === 0) process.stdout.write(`  ${done}/${frames} frames  ${((Date.now() - t0) / 1000).toFixed(0)}s\n`);
      }
      ff.stdin.end();
      await new Promise((r, j) => ff.on("close", c => c ? j(new Error("ffmpeg " + c)) : r()));
      await page.close();
      return file;
    };
    const parts = (await Promise.all(Array.from({ length: workers }, (_, w) => chunk(w)))).filter(Boolean);
    const list = path.join(OUT, "chunks.txt");
    fs.writeFileSync(list, parts.map(p => `file '${p}'`).join("\n"));
    const silent = path.join(OUT, "video_silent.mkv");
    execFileSync("ffmpeg", ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", list, "-c", "copy", silent]);
    const audio = path.join(OUT, "soundtrack.wav");
    const final = path.join(OUT, "one-shape.mp4");
    execFileSync("ffmpeg", ["-v", "error", "-y", "-i", silent, ...(fs.existsSync(audio) ? ["-i", audio] : []),
      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "12", "-preset", "slow", "-tune", "animation",
      "-movflags", "+faststart", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
      ...(fs.existsSync(audio) ? ["-c:a", "aac", "-b:a", "256k", "-shortest"] : []), "-frames:v", String(frames), final]);
    for (const p of parts) fs.unlinkSync(p);
    fs.unlinkSync(list);
    console.log(`${frames} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${final}`);
  }
} finally {
  await browser.close();
  server.close();
}
