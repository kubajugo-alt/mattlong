#!/usr/bin/env node
// Generate one image with the Gemini image API and save it as a file.
//
//   GEMINI_API_KEY=... node tools/gen-image.mjs --out path.png --prompt "..." \
//     [--ref ref1.png --ref ref2.png] [--aspect 16:9] [--size 2K] [--model gemini-3-pro-image]
//
// --prompt-file reads the prompt from a file instead. Reference images guide
// style and character consistency. Writes the image plus a .json sidecar with
// the prompt, model and references, for assets/SOURCES.md.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, extname } from 'node:path';

const args = process.argv.slice(2);
const opt = { ref: [] };
for (let i = 0; i < args.length; i++) {
  const k = args[i].replace(/^--/, '');
  const v = args[++i];
  if (k === 'ref') opt.ref.push(v);
  else opt[k] = v;
}
if (opt['prompt-file']) opt.prompt = readFileSync(opt['prompt-file'], 'utf8').trim();
if (!opt.out || !opt.prompt) {
  console.error('usage: gen-image.mjs --out file.png --prompt "..." [--ref img]... [--aspect 16:9] [--size 2K]');
  process.exit(2);
}
const key = process.env.GEMINI_API_KEY;
if (!key) { console.error('GEMINI_API_KEY is not set'); process.exit(2); }

const model = opt.model || 'gemini-3-pro-image';
const mime = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp' };
const parts = [
  ...opt.ref.map((p) => ({
    inline_data: { mime_type: mime[extname(p).toLowerCase()] || 'image/png', data: readFileSync(p).toString('base64') },
  })),
  { text: opt.prompt },
];
const body = {
  contents: [{ role: 'user', parts }],
  generationConfig: {
    responseModalities: ['IMAGE'],
    imageConfig: { aspectRatio: opt.aspect || '16:9', imageSize: opt.size || '2K' },
  },
};

const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
  method: 'POST',
  headers: { 'content-type': 'application/json', 'x-goog-api-key': key },
  body: JSON.stringify(body),
});
const json = await res.json();
if (!res.ok) { console.error(res.status, JSON.stringify(json.error || json)); process.exit(1); }
const img = json.candidates?.[0]?.content?.parts?.find((p) => p.inlineData || p.inline_data);
if (!img) { console.error('no image in response:', JSON.stringify(json).slice(0, 800)); process.exit(1); }
const data = (img.inlineData || img.inline_data).data;
mkdirSync(dirname(opt.out), { recursive: true });
writeFileSync(opt.out, Buffer.from(data, 'base64'));
writeFileSync(opt.out.replace(/\.[a-z]+$/i, '.json'), JSON.stringify({
  model, prompt: opt.prompt, refs: opt.ref, aspect: opt.aspect || '16:9', size: opt.size || '2K',
  created: new Date().toISOString(), usage: json.usageMetadata,
}, null, 2));
console.log('wrote', opt.out);
