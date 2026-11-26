const {chromium}=require('playwright');(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});const p=await b.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1.5});
await p.addInitScript(()=>{ const rn=performance.now.bind(performance), rr=window.requestAnimationFrame.bind(window); let virt=false, vt=0, q=[];
  performance.now=()=>virt?vt:rn(); window.requestAnimationFrame=(cb)=>{ if(virt){q.push(cb);return 0;} return rr((t)=>cb(virt?vt:t)); };
  window.__virt=()=>{ vt=rn(); virt=true; }; window.__adv=(ms)=>{ vt+=ms; const c=q; q=[]; c.forEach(f=>f(vt)); }; });
const errs=[];p.on('pageerror',e=>errs.push(e.message));await p.goto('http://localhost:8765/');
await p.waitForSelector('.gcard.open .cardbtn');await p.click('.gcard.open .cardbtn');await p.waitForSelector('.gcard.open .cardbtn');await p.click('.gcard.open .cardbtn');await p.waitForTimeout(800);
const S=async()=>{for(let i=0;i<80;i++){if(!await p.evaluate(()=>GAME.busy))return;await p.evaluate(()=>ENGINE.hooks.click(0,0));await p.waitForTimeout(200);}};await S();
await p.evaluate(()=>ENGINE.enter('pete-kate-flat','corridor'));await p.waitForTimeout(3500);await S();
await p.evaluate(()=>{ENGINE.M.x=560;ENGINE.M.y=1420;ENGINE.M.dir='side';ENGINE.M.flip=false;}); await p.waitForTimeout(1500);
await p.evaluate(()=>{ window.__virt(); for(let i=0;i<3;i++) window.__adv(16);
  const A=ENGINE.scene().sc.actors.kate; window.__ph='stand';
  (async()=>{ await ENGINE.anim('kate-at-table','leave'); window.__ph='side'; const w=ENGINE.actorWalk('kate','side',A.start,A.turn,null,A.secs_side); ENGINE.STORY.kateGone=true; await w;
    window.__ph='back'; await ENGINE.actorWalk('kate','back',A.turn,A.door,'out',A.secs_back); window.__ph='gone'; })(); });
const D='/tmp/claude-0/-home-user/0f7a7501-1f63-5427-950d-2107e85f38a7/scratchpad/kateboard/fr/'; const meta=[]; let gone=0;
for(let k=0;k<200 && gone<6;k++){ await p.evaluate(()=>window.__adv(1000/12)); await p.evaluate(()=>new Promise(r=>setTimeout(r,0)));
  const st=await p.evaluate(()=>({ph:window.__ph, w:ENGINE.walking(), t:performance.now()}));
  const f='f'+String(k).padStart(3,'0')+'.jpg'; await p.screenshot({path:D+f,type:'jpeg',quality:72,clip:{x:240,y:110,width:680,height:600}});
  meta.push({f, ph:st.ph, w:st.w}); if(st.ph==='gone') gone++; }
require('fs').writeFileSync(D+'meta.json',JSON.stringify(meta)); console.log(meta.length, meta.map(m=>m.ph[0]).join(''), errs); await b.close()})();
