import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const out=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(out,'../..');
let marked;
try { ({marked}=await import('marked')); }
catch { ({marked}=await import(pathToFileURL(path.join(process.env.USERPROFILE || process.env.HOME,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js')))); }
const manifest=JSON.parse(await fs.readFile(path.join(out,'全Agent导出与行号核验.json'),'utf8'));
const css=await fs.readFile(path.join(out,'prompt_docs.css'),'utf8');
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
for(const doc of manifest.documents){
 const target=path.join(root,doc),text=await fs.readFile(target,'utf8');
 const headings=[],renderer=new marked.Renderer();
 renderer.heading=function({tokens,depth}){
  const content=this.parser.parseInline(tokens),id='section-'+headings.length;
  headings.push({id,depth,text:tokens.map(t=>t.text??t.raw??'').join('')});
  return `<h${depth} id="${id}">${content}</h${depth}>\n`;
 };
 let body=marked.parse(text,{gfm:true,renderer}).replaceAll('<table>','<div class="table-wrap"><table>').replaceAll('</table>','</table></div>');
 // Same-folder Markdown links in the index also have colocated HTML versions.
 for(const other of manifest.documents){
  const abs=path.join(root,other).replaceAll('\\','/');
  const relative=path.relative(path.dirname(target),path.join(root,other.replace(/\.md$/,'.html'))).replaceAll('\\','/');
  body=body.replaceAll(`href="${abs}"`,`href="${relative.split('/').map(encodeURIComponent).join('/')}"`);
 }
 body=body.replace(/href="([^"#]+)\.md"/g,'href="$1.html"');
 const title=text.split('\n')[0].replace(/^# /,''),nav=headings.filter(h=>h.depth===2||h.depth===3).map(h=>`<a class="${h.depth===3?'sub':''}" href="#${h.id}">${esc(h.text)}</a>`).join('\n');
 const index=path.relative(path.dirname(target),path.join(root,'karma/agents/Prompt总览.html')).replaceAll('\\','/');
 const html=`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)}</title><style>${css}</style></head><body><header><div class="label">${esc(title)}</div><p>源码行号与实际调用分支 · 2026-11-03 · ${manifest.git_head.slice(0,7)}</p></header><div class="layout"><aside><h2>目录</h2><input id="toc-filter" type="search" placeholder="搜索轮次、System、User"><a href="${encodeURI(index)}">全部Agent总览</a>${nav}</aside><main><a href="${encodeURIComponent(path.basename(target))}">Markdown原文</a>${body}</main></div><script>document.getElementById('toc-filter').addEventListener('input',function(){const q=this.value.toLowerCase();document.querySelectorAll('aside a[href^="#"]').forEach(a=>a.hidden=!a.textContent.toLowerCase().includes(q));});</script></body></html>`;
 await fs.writeFile(target.replace(/\.md$/,'.html'),html.replace(/\r\n/g,'\n').replace(/\r/g,''),'utf8');
 console.log(JSON.stringify({file:doc,headings:headings.length}));
}
