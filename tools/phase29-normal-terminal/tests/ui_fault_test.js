// 执行实际Index.checkTerminal，验证mark3与终止之间有异步投递机会。
const fs=require('fs'),vm=require('vm'),ts=require(process.argv[2]);const s=fs.readFileSync(process.argv[3],'utf8');
const a=s.indexOf('  private async checkTerminal('),b=s.indexOf('  private write(',a);if(a<0||b<0)throw Error('missing');
const events=[];let tick=0;const probe={terminalState:()=>1,terminalMark:c=>events.push({kind:'mark',c,tick})};const context={getApplicationContext:()=>({killAllProcesses:()=>{events.push({kind:'kill',tick});return Promise.resolve();}})};
const ctx={probe,window:{getLastWindow:async()=>({setWindowKeepScreenOn:async()=>{},getWindowProperties:()=>({isKeepScreenOn:false})})},setTimeout:f=>{tick++;f();}};vm.createContext(ctx);
const code='class Subject {terminating=false;currentMode="vk-inject-wait";getUIContext(){return {getHostContext:()=>context};}\n'+s.slice(a,b)+'}\nglobalThis.Subject=Subject;';ctx.context=context;vm.runInContext(ts.transpileModule(code,{compilerOptions:{target:ts.ScriptTarget.ES2020}}).outputText,ctx);
(async()=>{await new ctx.Subject().checkTerminal();const m=events.find(e=>e.c===3),k=events.find(e=>e.kind==='kill');const passed=!!m&&!!k&&k.tick>m.tick;console.log(JSON.stringify({events,passed}));process.exit(passed?0:1);})();
