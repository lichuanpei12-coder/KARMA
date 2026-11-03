import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const out=path.dirname(fileURLToPath(import.meta.url));
let marked;
try {({marked}=await import('marked'));}
catch {({marked}=await import(pathToFileURL(path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js'))));}
const css=await fs.readFile(path.join(out,'../../tools/prompt_docs/prompt_docs.css'),'utf8');
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
for(const file of (await fs.readdir(out)).filter(n=>n.endsWith('.md'))){
 const md=await fs.readFile(path.join(out,file),'utf8'),headings=[],renderer=new marked.Renderer();
 renderer.heading=function({tokens,depth}){
  const content=this.parser.parseInline(tokens),id='section-'+headings.length;
  headings.push({id,depth,text:tokens.map(t=>t.text??t.raw??'').join('')});
  return `<h${depth} id="${id}">${content}</h${depth}>\n`;
 };
 const title=md.split('\n')[0].slice(2);
 let body=marked.parse(md,{gfm:true,renderer}).replaceAll('<table>','<div class="table-wrap"><table>').replaceAll('</table>','</table></div>');
 body=body.replace(/href="([^"#]+)\.md"/g,'href="$1.html"');
 const nav=headings.filter(h=>h.depth===2||h.depth===3).map(h=>`<a href="#${h.id}">${esc(h.text)}</a>`).join('\n');
 const html=`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)}</title><style>${css}</style></head><body><header><div class="label">${esc(title)}</div><p>2026-11-03 · 设计草案，尚未接入运行</p></header><div class="layout"><aside><h2>目录</h2><input id="toc-filter" type="search" placeholder="搜索规则、案例、Agent"><a href="反馈Prompt分配与案例核查.html">分配与案例核查</a>${nav}</aside><main><a href="${encodeURIComponent(file)}">Markdown 原文</a>${body}</main></div><script>document.getElementById('toc-filter').addEventListener('input',function(){const q=this.value.toLowerCase();document.querySelectorAll('aside a[href^="#"]').forEach(a=>a.hidden=!a.textContent.toLowerCase().includes(q));});</script></body></html>`;
 await fs.writeFile(path.join(out,file.replace(/\.md$/,'.html')),html.replace(/\r/g,''),'utf8');
 console.log(JSON.stringify({file,headings:headings.length}));
}
