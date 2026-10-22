// 提取实际Timeline.keepAwake方法，TypeScript转译后执行，不手写控制流。
const fs=require('fs'),vm=require('vm');
const ts=require(process.argv[2]);const source=fs.readFileSync(process.argv[3],'utf8');
const begin=source.indexOf('  static async keepAwake(');const end=source.indexOf('  static async focusExperiment()',begin);if(begin<0||end<0)throw Error('method missing');
let terminal=0;const events=[];const probe={terminalState:()=>terminal,terminalMark:(c)=>events.push(c)};
const method=source.slice(begin,end);const js=ts.transpileModule('class Timeline { static live=true;static record(...args:any[]){}\n'+method+'}\n globalThis.Subject=Timeline;', {compilerOptions:{target:ts.ScriptTarget.ES2020}}).outputText;
const ctx={probe,Event:new Proxy({},{get:(_,k)=>k})};vm.createContext(ctx);vm.runInContext(js,ctx);
(async()=>{
 let allow;let on=false;const calls=[];const w={setWindowKeepScreenOn(v){calls.push(v);if(v)return new Promise(resolve=>{allow=()=>{on=true;resolve();}});on=v;return Promise.resolve();},getWindowProperties(){return{isKeepScreenOn:on};}};
 const pending=ctx.Subject.keepAwake(w,1,true);terminal=1;allow();await pending;
 const passed=on===false&&calls.join(',')==='true,false';console.log(JSON.stringify({case:'inflight-enable-after-terminal',calls,actualKeepScreen:on,passed}));process.exit(passed?0:1);
})();
