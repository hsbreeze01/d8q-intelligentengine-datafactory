/* d8q-factor-console module for D8QPro main site
   Injected via loadFactorConsole(el)
   All CSS classes prefixed .fc-; all JS functions prefixed fc_ */
function loadFactorConsole(el) {
document.querySelectorAll('#nav a[data-fc-page]').forEach(a=>a.remove());
el.innerHTML=`<style>
.fc-wrap{font-family:-apple-system,"PingFang SC","Hiragino Sans GB",sans-serif;background:#f0f2f5;color:#333;font-size:14px;line-height:1.65;min-height:100vh}
.fc-wrap *{box-sizing:border-box;margin:0;padding:0}
.fc-wrap a{color:#1890ff;text-decoration:none;cursor:pointer}
.fc-wrap a:hover{color:#40a9ff}
.fc-wrap button{font-family:inherit}
.fc-topbar{height:48px;background:#fff;border-bottom:1px solid #e8e8e8;display:flex;align-items:center;gap:12px;padding:0 20px;flex-shrink:0}
.fc-topbar .fc-title{font-size:15px;font-weight:600;white-space:nowrap}
.fc-topbar .fc-search{flex:0 1 260px;padding:6px 12px;border:1px solid #d9d9d9;border-radius:6px;font-size:13px;outline:none}
.fc-topbar .fc-search:focus{border-color:#1890ff}
.fc-tabs{display:flex;gap:4px;padding:8px 20px;background:#fff;border-bottom:1px solid #e8e8e8;overflow-x:auto}
.fc-tabs a{display:inline-flex;align-items:center;gap:4px;padding:6px 12px;border-radius:6px;color:#666;white-space:nowrap;font-size:12.5px}
.fc-tabs a:hover{background:#f0f7ff;color:#1890ff}
.fc-tabs a.fc-active{background:#e6f7ff;color:#1890ff;font-weight:600}
.fc-tabs .fc-cnt{display:inline-block;min-width:18px;padding:0 5px;border-radius:9px;background:#ff4d4f;color:#fff;text-align:center;font-size:10px}
.fc-topbar .fc-spacer{flex:1}
.fc-src-badge{font-size:11px;padding:2px 10px;border-radius:10px;white-space:nowrap}
.fc-src-live{background:#f6ffed;color:#52c41a;border:1px solid #b7eb8f}
.fc-src-demo{background:#fff7e6;color:#fa8c16;border:1px solid #ffd591}
.fc-btn-manual{padding:6px 14px;border:1px solid #1890ff;color:#1890ff;background:#fff;border-radius:6px;font-size:12.5px;cursor:pointer;white-space:nowrap}
.fc-btn-manual:hover{background:#e6f7ff}
.fc-content{padding:20px 24px 90px}
.fc-page{display:none}.fc-page.fc-active{display:block}
.fc-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px}
.fc-mc{background:#fff;border-radius:8px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,.06);border-left:4px solid #1890ff;cursor:pointer;transition:box-shadow .2s}
.fc-mc:hover{box-shadow:0 4px 12px rgba(0,0,0,.1)}
.fc-mc .fc-label{font-size:12px;color:#999;margin-bottom:4px}
.fc-mc .fc-value{font-size:22px;font-weight:700;color:#1890ff}
.fc-mc .fc-value.fc-na{color:#999;font-size:15px;font-weight:500}
.fc-mc .fc-sub{font-size:11.5px;margin-top:3px;color:#666}
.fc-mc.fc-ok{border-left-color:#52c41a}.fc-mc.fc-ok .fc-value{color:#52c41a}
.fc-mc.fc-warn{border-left-color:#faad14}.fc-mc.fc-warn .fc-value{color:#faad14}
.fc-mc.fc-bad{border-left-color:#ff4d4f}.fc-mc.fc-bad .fc-value{color:#ff4d4f}
.fc-mc.fc-gray{border-left-color:#bfbfbf}
.fc-stepper{display:flex;gap:6px;margin:10px 0 4px}
.fc-stepper .fc-st{flex:1;text-align:center;padding:8px 4px;border-radius:6px;background:#f5f5f5;color:#999;font-size:12px;transition:all .2s}
.fc-stepper .fc-st b{display:block;font-size:13px}
.fc-stepper .fc-st.fc-past{background:#e6f7ff;color:#1890ff}
.fc-stepper .fc-st.fc-cur{background:#1890ff;color:#fff;box-shadow:0 2px 8px rgba(24,144,255,.4)}
.fc-stepper .fc-st.fc-term.fc-cur{background:#ff4d4f;box-shadow:0 2px 8px rgba(255,77,79,.4)}
.fc-stepper .fc-st.fc-term.fc-past{background:#fff2f0;color:#ff4d4f}
.fc-barrow{display:flex;align-items:center;gap:10px;margin:9px 0;font-size:12.5px}
.fc-barrow .fc-bl{width:130px;color:#666;flex-shrink:0}
.fc-barrow .fc-track{flex:1;height:8px;background:#f0f0f0;border-radius:4px;overflow:hidden}
.fc-barrow .fc-fill{height:100%;border-radius:4px;background:#1890ff;transition:width .4s ease}
.fc-barrow .fc-fill.fc-over{background:#ff4d4f}
.fc-barrow .fc-fill.fc-full{background:#52c41a}
.fc-barrow .fc-bv{width:210px;color:#666;flex-shrink:0;text-align:right}
.fc-barrow .fc-bv b{color:#333}
.fc-failed-banner{background:#fff2f0;border:1px solid #ffccc7;border-radius:8px;padding:14px 18px;margin-bottom:16px;display:none}
.fc-failed-banner.fc-show{display:flex;gap:14px;align-items:flex-start}
.fc-failed-banner .fc-ic{font-size:22px}
.fc-failed-banner b{color:#ff4d4f;font-size:15px}
.fc-failed-banner p{font-size:12.5px;color:#666;margin-top:4px}
.fc-card{background:#fff;border-radius:8px;padding:18px 20px;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:16px}
.fc-card h3{font-size:15px;font-weight:600;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;gap:10px}
.fc-card h3 .fc-more{font-size:12px;color:#1890ff;font-weight:400;cursor:pointer}
.fc-et{width:100%;border-collapse:collapse;font-size:13px}
.fc-et th{text-align:left;padding:10px 12px;background:#fafafa;color:#666;font-weight:500;border-bottom:1px solid #f0f0f0;white-space:nowrap}
.fc-et td{padding:10px 12px;border-bottom:1px solid #f5f5f5;vertical-align:middle}
.fc-et tbody tr{cursor:pointer;transition:background .12s}
.fc-et tbody tr:hover{background:rgba(24,144,255,.04)}
.fc-fname{font-weight:500}
.fc-fdesc{color:#999;font-size:12px;max-width:380px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fc-fval{font-weight:600;color:#1890ff;white-space:nowrap}
.fc-fval.fc-changed{color:#fa8c16}
.fc-fval.fc-ro{color:#666;font-weight:500}
.fc-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500;white-space:nowrap;margin-right:4px}
.fc-b-adj{background:#e6f7ff;color:#1890ff}
.fc-b-ro{background:#f0f0f0;color:#666}
.fc-b-sys{background:#f9f0ff;color:#722ed1}
.fc-b-high{background:#fff2f0;color:#ff4d4f}
.fc-b-warn2{background:#fff7e6;color:#fa8c16}
.fc-filters{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.fc-fb{padding:5px 14px;border:1px solid #d9d9d9;border-radius:16px;font-size:12px;cursor:pointer;background:#fff;transition:all .15s}
.fc-fb:hover{border-color:#1890ff;color:#1890ff}
.fc-fb.fc-active{background:#1890ff;color:#fff;border-color:#1890ff}
.fc-filters[data-cat]{display:inline-flex;align-items:center;gap:3px;padding:3px;background:#f5f7fa;border:1px solid #e5e9f0;border-radius:9px;margin-bottom:16px}
.fc-filters[data-cat] .fc-fb{display:inline-flex;align-items:center;justify-content:center;min-width:112px;height:34px;padding:0 16px;border:0;border-radius:6px;background:transparent;color:#666;font-size:13px;font-weight:500;line-height:34px}
.fc-filters[data-cat] .fc-fb:hover{background:#fff;color:#1890ff;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.fc-filters[data-cat] .fc-fb.fc-active{background:#fff;color:#1890ff;box-shadow:0 1px 4px rgba(0,0,0,.12)}
@media(max-width:520px){.fc-filters[data-cat]{display:flex;width:100%}.fc-filters[data-cat] .fc-fb{flex:1;min-width:0;padding:0 8px}}
.fc-drawer-mask{position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:80;opacity:0;pointer-events:none;transition:opacity .2s}
.fc-drawer-mask.fc-show{opacity:1;pointer-events:auto}
.fc-drawer{position:fixed;top:0;right:0;bottom:0;width:min(600px,94vw);background:#fff;z-index:81;transform:translateX(100%);transition:transform .24s ease-out;box-shadow:-6px 0 24px rgba(0,0,0,.12);display:flex;flex-direction:column}
.fc-drawer.fc-show{transform:none}
.fc-drawer .fc-dhead{padding:16px 22px;border-bottom:1px solid #e8e8e8;display:flex;align-items:center;gap:10px}
.fc-drawer .fc-dhead .fc-t{font-size:16px;font-weight:600;flex:1}
.fc-drawer .fc-dclose{border:none;background:none;font-size:20px;color:#999;cursor:pointer;padding:4px 8px;border-radius:4px}
.fc-drawer .fc-dclose:hover{background:#f5f5f5;color:#333}
.fc-drawer .fc-dbody{flex:1;overflow-y:auto;padding:18px 22px}
.fc-dsec{margin-bottom:18px}
.fc-dsec .fc-dh{font-size:13px;font-weight:600;margin-bottom:6px;display:flex;align-items:center;gap:8px}
.fc-dsec .fc-dh::before{content:"";width:3px;height:12px;background:#1890ff;border-radius:2px}
.fc-dsec p{font-size:13px;color:#666}
.fc-dsec .fc-kv{font-size:12.5px;color:#666;background:#fafafa;border-radius:6px;padding:8px 12px}
.fc-updown{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.fc-updown>div{border-radius:6px;padding:10px 12px;font-size:12.5px}
.fc-updown .fc-u{background:#fff7e6;border:1px solid #ffd591}
.fc-updown .fc-d{background:#e6f7ff;border:1px solid #91d5ff}
.fc-updown b{display:block;font-size:12px;margin-bottom:3px}
.fc-linkline{display:flex;flex-wrap:wrap;gap:6px}
.fc-linkline .fc-lk{font-size:12px;background:#f5f5f5;border-radius:4px;padding:2px 10px;cursor:pointer;color:#666}
.fc-linkline .fc-lk:hover{background:#e6f7ff;color:#1890ff}
.fc-editbox{background:#fafafa;border:1px solid #f5f5f5;border-radius:8px;padding:14px 16px;margin-top:6px}
.fc-editbox label{font-size:12px;color:#666;display:block;margin-bottom:6px}
.fc-editbox .fc-inrow{display:flex;align-items:center;gap:8px}
.fc-editbox input[type=text],.fc-editbox input[type=number],.fc-editbox select{flex:0 1 180px;padding:8px 10px;border:1px solid #d9d9d9;border-radius:6px;font-size:14px;outline:none}
.fc-editbox input:focus{border-color:#1890ff}
.fc-editbox .fc-unit{font-size:12.5px;color:#999}
.fc-editbox .fc-err{color:#ff4d4f;font-size:12px;margin-top:6px;display:none}
.fc-editbox .fc-err.fc-show{display:block}
.fc-editbox .fc-types{display:flex;gap:14px;margin:4px 0}
.fc-editbox .fc-types label{display:flex;align-items:center;gap:6px;margin:0;font-size:13px;color:#333;cursor:pointer}
.fc-dfoot{padding:14px 22px;border-top:1px solid #e8e8e8;display:flex;gap:10px}
.fc-btn{padding:9px 20px;background:#1890ff;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13.5px;transition:background .15s}
.fc-btn:hover{background:#40a9ff}
.fc-btn:disabled{background:#b3d9ff;cursor:not-allowed}
.fc-btn-ghost{background:#fff;color:#1890ff;border:1px solid #1890ff}
.fc-btn-ghost:hover{background:#e6f7ff}
.fc-btn-danger{background:#ff4d4f}.fc-btn-danger:hover{background:#ff7875}
.fc-draftbar{position:fixed;left:0;right:0;bottom:0;background:#001529;color:#fff;z-index:70;transform:translateY(100%);transition:transform .25s ease-out;padding:10px 24px;display:flex;align-items:center;gap:14px}
.fc-draftbar.fc-show{transform:none}
.fc-draftbar .fc-dc{font-size:13px}
.fc-draftbar .fc-dc b{color:#69c0ff}
.fc-modal-mask{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:90;display:none;align-items:center;justify-content:center;padding:20px}
.fc-modal-mask.fc-show{display:flex}
.fc-modal{background:#fff;border-radius:10px;width:min(680px,96vw);max-height:88vh;display:flex;flex-direction:column;box-shadow:0 12px 40px rgba(0,0,0,.2)}
.fc-modal .fc-mhead{padding:16px 22px;border-bottom:1px solid #e8e8e8;font-size:15px;font-weight:600;display:flex;justify-content:space-between;align-items:center}
.fc-modal .fc-mbody{padding:18px 22px;overflow-y:auto;font-size:13px}
.fc-modal .fc-mfoot{padding:14px 22px;border-top:1px solid #e8e8e8;display:flex;gap:10px;justify-content:flex-end}
.fc-conflict{background:#fff2f0;border:1px solid #ffccc7;border-radius:6px;padding:10px 14px;margin-bottom:10px;font-size:12.5px}
.fc-conflict b{color:#ff4d4f}
textarea.fc-reason{width:100%;min-height:70px;padding:10px;border:1px solid #d9d9d9;border-radius:6px;font-size:13px;resize:vertical;outline:none;font-family:inherit}
textarea.fc-reason:focus{border-color:#1890ff}
.fc-co-md{width:100%;min-height:180px;font-family:Menlo,Consolas,monospace;font-size:12px;padding:10px;border:1px solid #f5f5f5;border-radius:6px;background:#fafafa;resize:vertical}
.fc-hist-item{background:#fff;border-radius:8px;padding:14px 18px;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:12px;border-left:4px solid #1890ff}
.fc-hist-item.fc-error{border-left-color:#ff4d4f}
.fc-hist-item.fc-discarded{border-left-color:#999}
.fc-hist-item.fc-applied{border-left-color:#52c41a}
.fc-hist-item .fc-ht{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
.fc-hist-item .fc-ht b{font-size:13.5px}
.fc-hist-item .fc-hmeta{font-size:12px;color:#999;margin-top:4px}
.fc-hist-item .fc-hitems{font-size:12.5px;color:#666;margin-top:8px;line-height:1.8}
.fc-status-pill{font-size:11px;padding:2px 10px;border-radius:10px}
.fc-st-exported{background:#e6f7ff;color:#1890ff}
.fc-st-applied{background:#f6ffed;color:#52c41a}
.fc-st-error{background:#fff2f0;color:#ff4d4f}
.fc-st-discarded{background:#f0f0f0;color:#666}
.fc-manual-mask{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:95;display:none;flex-direction:column;padding:24px}
.fc-manual-mask.fc-show{display:flex}
.fc-manual-box{background:#fff;border-radius:10px;flex:1;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 16px 48px rgba(0,0,0,.25)}
.fc-manual-box .fc-mh{padding:12px 20px;border-bottom:1px solid #e8e8e8;display:flex;justify-content:space-between;align-items:center}
.fc-manual-box .fc-mh b{font-size:14.5px}
.fc-manual-box iframe{flex:1;border:none;width:100%}
.fc-manual-box .fc-mfail{flex:1;display:none;align-items:center;justify-content:center;color:#999;font-size:13.5px;text-align:center;padding:30px;line-height:2}
.fc-toast{position:fixed;top:18px;left:50%;transform:translateX(-50%) translateY(-8px);padding:10px 26px;border-radius:6px;font-size:13.5px;z-index:99;opacity:0;transition:all .25s;background:#f6ffed;color:#52c41a;border:1px solid #b7eb8f;pointer-events:none}
.fc-toast.fc-show{opacity:1;transform:translateX(-50%)}
.fc-toast.fc-err{background:#fff2f0;color:#ff4d4f;border-color:#ffccc7}
.fc-empty{text-align:center;padding:44px;color:#999;font-size:13.5px}
@media(max-width:900px){.fc-metrics{grid-template-columns:repeat(2,1fr)}}
@media(max-width:768px){.fc-content{padding:14px}.fc-topbar .fc-search{flex:1}.fc-barrow .fc-bv{width:150px}}
</style>
<div class="fc-wrap" id="fcWrap">
<div class="fc-topbar">
  <div class="fc-title" id="fcPageTitle">概览</div>
  <input class="fc-search" id="fcSearch" type="text" placeholder="搜索配置项名称或说明…">
  <div class="fc-spacer"></div>
  <span class="fc-src-badge fc-src-demo" id="fcSrcBadge">演示数据</span>
  <button class="fc-btn-manual" id="fcManualBtn">📘 使用手册</button>
</div>
<div class="fc-tabs" id="fcNav"></div>
<div class="fc-content" id="fcContent">
  <div class="fc-failed-banner" id="fcFailedBanner"><div class="fc-ic">🚨</div><div><b>策略已进入终局止损（不可自动恢复）</b><p id="fcFailedDetail"></p><p>需人工开启新一轮资金周期后方可恢复。请按<a id="fcManualLink2" style="font-weight:600">使用手册 · 场景七</a>操作。</p></div></div>
  <div class="fc-page" id="fcPage-overview"></div>
  <div class="fc-page" id="fcPage-entry"></div>
  <div class="fc-page" id="fcPage-risk"></div>
  <div class="fc-page" id="fcPage-exit"></div>
  <div class="fc-page" id="fcPage-signal"></div>
  <div class="fc-page" id="fcPage-strategy"></div>
  <div class="fc-page" id="fcPage-history"></div>
  <div class="fc-page" id="fcPage-search"></div>
</div>
</div>
<div class="fc-drawer-mask" id="fcDrawerMask"></div>
<div class="fc-drawer" id="fcDrawer" role="dialog" aria-modal="true">
  <div class="fc-dhead"><div class="fc-t" id="fcDTitle"></div><button class="fc-dclose" id="fcDClose">✕</button></div>
  <div class="fc-dbody" id="fcDBody"></div>
  <div class="fc-dfoot" id="fcDFoot"></div>
</div>
<div class="fc-draftbar" id="fcDraftbar">
  <div class="fc-dc">📝 调整草稿 <b id="fcDraftCount">0</b> 项待提交</div>
  <div class="fc-spacer"></div>
  <button class="fc-btn fc-btn-ghost" id="fcDraftClear">清空</button>
  <button class="fc-btn" id="fcDraftReview">提交并生成调整单 →</button>
</div>
<div class="fc-modal-mask" id="fcModalMask"><div class="fc-modal">
  <div class="fc-mhead"><span id="fcMTitle"></span><button class="fc-dclose" id="fcMClose">✕</button></div>
  <div class="fc-mbody" id="fcMBody"></div>
  <div class="fc-mfoot" id="fcMFoot"></div>
</div></div>
<div class="fc-manual-mask" id="fcManualMask"><div class="fc-manual-box">
  <div class="fc-mh"><b>📘 因子中心 · 配置管理指南</b><button class="fc-dclose" id="fcManualClose">✕</button></div>
  <iframe id="fcManualFrame" src="/static/d8q-factor-console-guide.html" title="使用手册"></iframe>
  <div class="fc-mfail" id="fcManualFail">手册文件加载失败。</div>
</div></div>
<div class="fc-toast" id="fcToast"></div>

`;

/* ================= 数据层 ================= */
const LS_DRAFT='d8q_fc_drafts', LS_CO='d8q_fc_cos', LS_SEQ='d8q_fc_seq';
const fc_store={
  get(k,f){try{return JSON.parse(localStorage.getItem(k))??f}catch(e){return f}},
  set(k,v){localStorage.setItem(k,JSON.stringify(v))}
};
let fc_drafts=fc_store.get(LS_DRAFT,[]);
let fc_cos=fc_store.get(LS_CO,[]);

/* 账户快照：优先实时只读接口，失败回退演示数据 */
const fc_API_BASE=new URLSearchParams(location.search).get('api')||'http://127.0.0.1:8090/api/account/status';
const fc_DEMO={demo:true,generated_at:'2026-09-10 14:36',
  A:50000,R:1042,U:-132.5,E:49909.5,D:50521,H:50000,SR:0.99819,DD:0.00181,
  status:'ACTIVE',state:'NORMAL',M:1.0,quote_complete:true,hits:0,confirms:2,
  gross:24335,max_gross:50521,open_risk:1350,max_open_risk:1515.6,
  industry:{'汽车':24335},industry_limit:12630.25,
  stocks:2,max_stocks:5,cash:26707,cash_buffer:5052.1};
let fc_acct={...fc_DEMO};

function fmtMoney(v){return v==null?'—':Number(v).toLocaleString('zh-CN',{maximumFractionDigits:0})}
function fmtPct(v,d=2){return v==null?'—':(v*100).toFixed(d)+'%'}

/* ================= 因子注册表（口径：配置管理指南 v2.0） ================= */
const FC_CATS=[
  {id:'overview',icon:'📊',name:'概览',title:'风险与资金概览'},
  {id:'entry',icon:'⚖️',name:'买入与仓位',title:'买入与仓位 · 配置'},
  {id:'risk',icon:'🛡️',name:'资金与风险',title:'资金与风险 · 配置'},
  {id:'exit',icon:'💰',name:'卖出纪律',title:'卖出纪律 · 配置'},
  {id:'signal',icon:'🎚️',name:'信号准入',title:'信号准入 · 配置'},
  {id:'strategy',icon:'🧪',name:'策略因子',title:'策略因子（只读展示）'},
  {id:'history',icon:'🕘',name:'调整历史',title:'调整历史'}
];
const FC_F=[]; const fc_reg=o=>FC_F.push(o);
/* ---- 买入与仓位 ---- */
fc_reg({id:'budget',cat:'entry',icon:'💴',name:'单笔买入预算',type:'money',def:20000,min:1000,max:50000,step:1000,unit:'元',
 desc:'单只新仓的资金上限。实际买入金额还会被行业额度、现金余量、风险余量进一步压缩，取其中最小值。',
 formula:'实际金额 = min(单笔预算, 行业余量, 现金余量, 风险余量换算额)',
 check:'必须为正数，建议不超过可运营资金的一半',
 up:'单股集中度上升，组合趋于"重仓少股"，单票失误的伤害变大',down:'每注更轻，但高价股可能凑不够最少手数（预算÷200 股价上限）',
 timing:'下一次买入评估生效；已持仓不受影响',example:'预算 2 万、股价 50 元 → 最多买 4 手（400 股）',
 links:['min_lots','trade_risk']});
fc_reg({id:'daily_new',cat:'entry',icon:'🌅',name:'每日最多新开仓',type:'int',def:5,min:1,max:10,unit:'只',
 desc:'每个交易日早晨最多新开几只股票，超出的候选按信号质量（评分＞盈亏比＞买点类型）择优淘汰。',
 check:'≥1',up:'开仓节奏更快，资金占用更急',down:'更克制，但可能错过当日机会',
 timing:'次日开盘生效',example:'候选 8 只、上限 5 → 只有排名前 5 进入买入流程',links:['max_stocks']});
fc_reg({id:'max_stocks',cat:'entry',icon:'🧺',name:'组合最多持仓',type:'int',def:5,min:1,max:10,unit:'只',
 desc:'同时在场的不同股票数量上限（含已挂单未成交的占位）。',
 check:'≥1，建议与"每日最多新开仓"配套规划',up:'更分散，跟踪负担变大',down:'更集中，单票波动对净值影响变大',
 timing:'下一次买入评估生效',example:'当前 2/5 → 还可再开 3 只新股票',links:['daily_new','ind_norm']});
fc_reg({id:'lots_per_stock',cat:'entry',icon:'🧷',name:'单股最多仓位份数',type:'int',def:2,min:1,max:5,unit:'份',
 desc:'同一只股票最多分几次建仓（首仓+补仓），每份仓位携带独立的止损与目标。',
 check:'≥1',up:'允许更多次补仓摊低成本，也可能越补越深',down:'基本失去补仓能力，止损更干脆',
 timing:'下一次买入评估生效',example:'上限 2 → 首仓后仅可在新信号出现时再补 1 份',links:[]});
fc_reg({id:'min_lots',cat:'entry',icon:'🔢',name:'最少买入手数',type:'int',def:2,min:1,max:10,unit:'手',
 desc:'单笔买入至少要买几手（1手=100股），保证仓位可拆分、能分批止盈——高价股的"颗粒度闸门"。',
 check:'≥1；隐含约束：股价 ≤ 单笔预算÷(手数×100)',up:'更严，高价股被大量拦下',down:'放宽后 1 手也允许，失去分批能力',
 timing:'下一次买入评估生效',example:'预算 2 万、最少 2 手 → 股价高于 100 元的信号被跳过',links:['budget']});
fc_reg({id:'buy_deadline',cat:'entry',icon:'⏰',name:'买入截止时间',type:'time',def:'10:00',unit:'',
 desc:'开盘后超过该时间不再新开仓，避免尾盘冲动买入。注意：当前系统处于宽松模式，此截止暂不生效。',
 check:'格式 HH:MM',up:'（严格模式下）窗口更长',down:'（严格模式下）只在开盘初段买入',
 timing:'次日开盘生效（宽松模式下不生效）',example:'设为 10:00 → 严格模式下 10:01 后的候选全部跳过',links:[]});
/* ---- 资金与风险 ---- */
fc_reg({id:'trade_risk',cat:'risk',icon:'🎯',name:'单笔风险上限',type:'pct',def:0.0075,min:0.0001,max:0.05,unit:'（占资金池）',
 desc:'单次买入允许承担的最大在险金额：若该笔买入后立刻跌到止损价，损失不得超过资金池的这一比例。止损越宽的信号，能买的股数越少。',
 formula:'在险金额 = (买入价 − 止损价) × 数量 ≤ 上限 × 可运营资金 × 状态系数',
 check:'0–5%；不得超过组合风险上限',up:'单笔容忍损失变大，仓位可以更重',down:'单笔更安全，宽止损信号会被大量拦下',
 timing:'下一次买入评估生效',example:'资金池 5 万、上限 0.75% → 单笔最多亏 378 元；止损距离 5% 的股票最多买约 700 股',
 links:['portfolio_risk']});
fc_reg({id:'portfolio_risk',cat:'risk',icon:'🛡️',name:'组合风险上限',type:'pct',def:0.03,min:0.001,max:0.2,unit:'（占资金池）',
 desc:'全部持仓同时跌到各自止损价时的合计损失上限——"最坏情况总共亏多少"的总闸门。',
 formula:'Σ(买入价 − 止损价) × 持有数量 ≤ 上限 × 可运营资金 × 状态系数',
 check:'0–20%；不得低于单笔风险上限',up:'整体防线更宽',down:'最坏情况损失更可控，满仓能力下降',
 timing:'下一次买入评估生效',example:'上限 3% ÷ 单笔 0.75% ≈ 同时最多持有 4 份"满风险"仓位',links:['trade_risk']});
fc_reg({id:'ind_norm',cat:'risk',icon:'🏭',name:'行业上限 · 正常档',type:'pct',def:0.25,min:0.05,max:0.6,unit:'（占资金池）',
 desc:'风险状态"正常"时，同一申万一级行业的持仓市值合计不得超过的比例。分子用当前市值——股价上涨会被动抬高占比。',
 check:'5–60%；不得低于警惕档',up:'允许更集中的行业押注',down:'强制更分散',
 timing:'下一次买入评估生效',example:'资金池 5 万、上限 25% → 汽车行业最多 1.25 万市值',links:['ind_cau','ind_def']});
fc_reg({id:'ind_cau',cat:'risk',icon:'🏭',name:'行业上限 · 警惕档',type:'pct',def:0.20,min:0.05,max:0.6,unit:'（占资金池）',
 desc:'风险状态"警惕"时的行业集中度上限。',check:'5–60%；不得高于正常档、不得低于防守档',
 up:'',down:'',timing:'下一次买入评估生效',example:'警惕档 20% → 同上口径收紧至 1 万',links:['ind_norm','ind_def']});
fc_reg({id:'ind_def',cat:'risk',icon:'🏭',name:'行业上限 · 防守档',type:'pct',def:0.15,min:0.05,max:0.6,unit:'（占资金池）',
 desc:'风险状态"防守"时的行业集中度上限。进入"只减仓"后行业新增额度为 0。',
 check:'5–60%；不得高于警惕档',up:'',down:'',timing:'下一次买入评估生效',example:'防守档 15%',links:['ind_norm','ind_cau']});
fc_reg({id:'cash_buffer',cat:'risk',icon:'🧾',name:'现金缓冲',type:'pct',def:0.10,min:0,max:0.5,unit:'（占资金池）',
 desc:'始终留在手上、不用于开新仓的现金垫，覆盖费用、滑点与突发流动性需求。',
 check:'0–50%',up:'更保守，资金利用率下降',down:'资金利用率升，应对意外的余量变薄',
 timing:'下一次买入评估生效',example:'资金池 5 万、缓冲 10% → 始终留 5 千现金',links:[]});
fc_reg({id:'dd_cau',cat:'risk',icon:'📉',name:'回撤警戒线 · 警惕',type:'pct',def:0.10,min:0.02,max:0.9,unit:'回撤',
 desc:'回撤（距离历史净值高点的回落幅度）达到该值时进入"警惕"状态：各类上限自动打对应折扣。',
 check:'三档警戒线必须依次增大且都在 2%–90% 之间',up:'更晚降档、波动容忍更大',down:'更早刹车',
 timing:'下一轮状态评估生效',example:'10% → 净值从高点回落 10%（如 5.2万→4.68万）即降档',links:['dd_def','dd_ro','mult_cau']});
fc_reg({id:'dd_def',cat:'risk',icon:'📉',name:'回撤警戒线 · 防守',type:'pct',def:0.20,min:0.02,max:0.9,unit:'回撤',
 desc:'回撤达到该值时进入"防守"状态，收缩力度更大。',check:'必须大于警惕档、小于只减仓档',
 up:'',down:'',timing:'下一轮状态评估生效',example:'20%',links:['dd_cau','dd_ro','mult_def']});
fc_reg({id:'dd_ro',cat:'risk',icon:'🚧',name:'回撤警戒线 · 只减仓',type:'pct',def:0.30,min:0.02,max:0.95,unit:'回撤',
 desc:'回撤达到该值时进入"只减仓"：禁止一切新买入，只允许按纪律卖出。行情数据异常时也会临时进入该状态。',
 check:'必须大于防守档',up:'',down:'',timing:'下一轮状态评估生效',example:'30%',links:['dd_cau','dd_def']});
fc_reg({id:'mult_cau',cat:'risk',icon:'🗜️',name:'风险收缩力度 · 警惕档',type:'pct',def:0.75,min:0,max:1,unit:'折扣',
 desc:'进入"警惕"后，总敞口、单笔/组合风险等所有上限共同乘以的折扣系数。',
 check:'0–100%；不得小于防守档折扣',up:'降档后仍较激进',down:'降档后收缩更狠',
 timing:'下一轮状态评估生效',example:'0.75 → 警惕档下 0.75% 单笔上限实为 0.5625%',links:['mult_def','dd_cau']});
fc_reg({id:'mult_def',cat:'risk',icon:'🗜️',name:'风险收缩力度 · 防守档',type:'pct',def:0.50,min:0,max:1,unit:'折扣',
 desc:'进入"防守"后所有上限共同乘以的折扣系数。',check:'0–100%；不得大于警惕档折扣',
 up:'',down:'',timing:'下一轮状态评估生效',example:'0.50 → 防守档下上限全部减半',links:['mult_cau','dd_def']});
fc_reg({id:'reinvest',cat:'risk',icon:'♻️',name:'盈利再投入比例',type:'pct',def:0.50,min:0,max:1,unit:'',high:true,
 desc:'赚到的钱拿多少继续滚动进可运营资金池（其余作为保护储备）。亏损则全额扣减资金池。',
 formula:'可运营资金 = 本金 + min(盈亏,0) + 比例 × max(盈亏,0)',
 check:'0–100%；建议积累约 30 笔完整交易后再评估调整',
 up:'进攻性增强，但回撤基数随之放大',down:'更多利润沉淀为储备，滚动变慢',
 timing:'下一轮资金计算生效；对本金无影响',example:'赚 1000、比例 50% → 资金池只增加 500',links:[]});
fc_reg({id:'survival',cat:'risk',icon:'🧯',name:'生存底线',type:'pct',def:0.60,min:0.1,max:1,unit:'（占本金）',high:true,
 desc:'最终保险丝：家底（生存净值）亏到本金的这一比例即触发终局止损——停止开新仓、按纪律有序清仓、不可自动恢复。',
 check:'10–100%；调高=更早熔断，调低=容忍更深亏损',
 up:'更早触发终局止损',down:'容忍更深亏损才熔断',
 timing:'下一轮状态评估生效',example:'底线 60%、本金 5 万 → 净值 3 万触发，最大容忍总亏损 2 万',links:['confirms']});
fc_reg({id:'confirms',cat:'risk',icon:'🔁',name:'底线确认次数',type:'int',def:2,min:2,max:5,unit:'次',
 desc:'生存净值触及底线后，需要连续多少次相互独立的行情观测都确认，才真正触发终局止损——防止单次行情毛刺误伤。',
 check:'≥2（系统最低要求）',up:'更抗毛刺，也可能更晚熔断',down:'反应更快，误伤风险上升',
 timing:'下一轮状态评估生效',example:'2 次 → 第一次触及先进入"只减仓"，第二次独立观测仍触及才终局',links:['survival']});
fc_reg({id:'quote_age',cat:'risk',icon:'📡',name:'行情时效要求',type:'int',def:120,min:10,max:600,unit:'秒',
 desc:'持仓股行情超过该时长未更新即视为不可信：相关估值显示"不可用"、风险状态临时降为只减仓，行情恢复自动回升。',
 check:'10–600 秒',up:'容忍更陈旧的行情（不建议）',down:'对数据新鲜度更敏感，降级更频繁',
 timing:'下一轮行情评估生效',example:'120 秒 → 停牌或数据中断 2 分钟后进入保护性降级',links:[]});
/* ---- 卖出纪律 ---- */
fc_reg({id:'time_stop_days',cat:'exit',icon:'⏳',name:'持仓时间上限',type:'int',def:10,min:1,max:60,unit:'自然日',
 desc:'买入后一直没有盈利（从未触发首批止盈）的仓位，最多持有这么多天后主动全量退出——治理"占着资金不干活"的僵尸仓。已止盈过的仓位豁免。',
 check:'≥1',up:'更有耐心，僵尸仓资金占用更久',down:'出清更快，但可能错过慢热股的主升',
 timing:'下一轮卖出检查生效，从生效时点起重新计算已持有天数',example:'10 天 → 9月1日买入且未止盈，9月11日强制退出',links:['breakeven_on']});
fc_reg({id:'breakeven_on',cat:'exit',icon:'🧷',name:'保本止损',type:'bool',def:true,unit:'',
 desc:'首批止盈成交后，剩余仓位的止损自动上移到成本价上方（只上移不下移），确保"赢过的仓不再亏钱出场"。',
 check:'—',up:'（开启）锁住已到手的安全垫',down:'（关闭）盈利转亏损的最坏情形回归',
 timing:'下一次止盈成交后生效',example:'成本 20 元 → 首批止盈后止损上移至约 20.1 元',links:['breakeven_buf','staged_on']});
fc_reg({id:'breakeven_buf',cat:'exit',icon:'🧷',name:'保本止损缓冲',type:'pct',def:0.005,min:0,max:0.03,unit:'（成本上浮）',
 desc:'保本止损上移到成本价上方的幅度，覆盖买卖双边费用。',check:'0–3%',
 up:'',down:'',timing:'下一次止盈成交后生效',example:'0.5% → 成本 20 元时止损 20.10 元',links:['breakeven_on']});
fc_reg({id:'staged_on',cat:'exit',icon:'🪜',name:'阶梯止盈',type:'bool',def:true,unit:'',
 desc:'达目标价不一次清仓：先卖一部分并上移保本止损，再涨到二档目标再卖一部分，尾仓交给止损/卖点跟踪。',
 check:'—',up:'（开启）强势股能吃更多趋势',down:'（关闭）回到"到目标价一次清仓"',
 timing:'下一次达目标时生效',example:'开启 → 达 +6% 卖 1/3，达 +6%×1.06 再卖剩余一半',links:['stage2_mult','staged_min_lots']});
fc_reg({id:'staged_min_lots',cat:'exit',icon:'🪜',name:'阶梯最小手数',type:'int',def:3,min:1,max:20,unit:'手',
 desc:'仓位至少多少手才启用三段式分批；不足时自动退化为两段（对半卖）。',
 check:'≥1',up:'更多仓位享受三段节奏',down:'更多仓位只分两段',
 timing:'下一次分批时生效',example:'3 手 → 600 股分三批各约 200 股',links:['staged_on']});
fc_reg({id:'stage2_mult',cat:'exit',icon:'🪜',name:'二档目标倍数',type:'float',def:1.06,min:1.01,max:2,unit:'倍',
 desc:'第二笔止盈在"目标价 × 该倍数"时触发。',check:'>1',
 up:'给趋势更大空间',down:'更快落袋',timing:'下一次二档判定生效',example:'1.06 → 目标 21 元时二档 22.26 元',links:['staged_on']});
fc_reg({id:'pivot_buf',cat:'exit',icon:'🌉',name:'破位退出缓冲',type:'pct',def:0.02,min:0,max:0.1,unit:'跌破深度',
 desc:'现价跌破近期中枢下沿超过这一幅度才认定为有效破位并退出，避免贴线假破位误伤。',
 check:'0–10%',up:'更容忍贴线波动',down:'破位反应更灵敏',
 timing:'下一轮卖出检查生效',example:'2% → 中枢下沿 10 元时，跌破至 9.8 元才退出',links:['pivot_days']});
fc_reg({id:'pivot_days',cat:'exit',icon:'🌉',name:'破位认定时效',type:'int',def:30,min:1,max:120,unit:'天内',
 desc:'只有该天数内新形成的中枢才作为破位参照——下跌途中的旧中枢不触发（保护中枢下方抄底的入场逻辑）。',
 check:'≥1',up:'更多旧中枢参与参照',down:'只用很新的中枢',
 timing:'下一轮卖出检查生效',example:'30 天 → 3 个月前的高位旧中枢不作为退出依据',links:['pivot_buf']});
/* ---- 信号准入 ---- */
fc_reg({id:'entry_types',cat:'signal',icon:'🚦',name:'入场信号类型',type:'types',def:['buy1','buy2','buy3'],unit:'',
 desc:'允许开仓的缠论买点类型白名单。收窄可聚焦确定性更高的买点，但信号量骤减。',
 check:'至少保留一种类型',up:'（增加类型）信号更多、更杂',down:'（减少类型）更聚焦，样本更少',
 timing:'次日买入生效',example:'仅勾选"三买" → 一买/二买信号全部跳过',links:['min_score']});
fc_reg({id:'min_score',cat:'signal',icon:'💯',name:'最低信号评分',type:'int',def:60,min:0,max:100,unit:'分',
 desc:'信号综合评分（类型/环境/周线/背离/止损五维加权）低于此值不买。',
 check:'0–100',up:'更严，信号更少质量更高',down:'更宽，弱信号混入',
 timing:'次日买入生效',example:'60 分 → 55 分的高盈亏比信号也会被拦',links:['min_rr']});
fc_reg({id:'min_rr',cat:'signal',icon:'📏',name:'最低盈亏比',type:'float',def:2.0,min:0.5,max:10,step:0.1,unit:'',
 desc:'预期收益÷预期风险的最低要求。注意：旧中枢降级后的买点盈亏比会回落到约 1.4，被拦下属于预期保护行为；无目标价的买点自动豁免。',
 check:'0.5–10',up:'只做赔率高的交易',down:'薄利交易也放行',
 timing:'次日买入生效',example:'2.0 → 目标 +12%、止损 −4% 的信号（比 3）通过；+6%/−4%（1.5）被拦',links:['min_score']});
fc_reg({id:'max_chase',cat:'signal',icon:'🏃',name:'追高上限',type:'pct',def:0.03,min:0,max:0.2,unit:'（高出信号价）',
 desc:'开盘现价已高出信号价这一比例视为错过入场窗口，放弃买入。历史案例：曾设 1% 导致首日全部跳过，后放宽至 3%。',
 check:'0–20%',up:'容忍更高开盘溢价',down:'高开即放弃',
 timing:'次日买入生效',example:'3% → 信号价 20 元、开盘 20.7 元以上放弃',links:['buy_premium']});
fc_reg({id:'buy_premium',cat:'signal',icon:'🏷️',name:'买入溢价上限',type:'pct',def:0.02,min:0,max:0.1,unit:'（高出信号价）',
 desc:'挂单价格最多比信号价高这一比例；现价低于信号价时贴现价买。',
 check:'0–10%',up:'更容易成交，成本更高',down:'更挑价，可能买不进',
 timing:'次日买入生效',example:'2% → 信号价 20 元时挂单上限 20.40 元',links:['max_chase']});
fc_reg({id:'chinext',cat:'signal',icon:'🔓',name:'创业板解锁线',type:'money',def:500000,min:50000,max:2000000,step:10000,unit:'元总资产',
 desc:'总资产达到该值后自动解锁创业板（30 开头）股票；解锁后即使回撤也不重新锁定。科创板始终不参与。',
 check:'≥5 万',up:'更难解锁',down:'更易解锁，承受 20% 涨跌幅品种',
 timing:'下一轮资金计算生效',example:'50 万 → 当前 5 万资金池下创业板长期锁定',links:[]});
/* ---- 策略因子（只读） ---- */
fc_reg({id:'ro_score',cat:'strategy',icon:'🧮',name:'缠论评分结构',type:'ro',ro:'类型 25 · 环境 25 · 周线 20 · 背驰 15 · 止损 15（共振 +10，上限 100）',
 desc:'信号端五维评分构成。属于策略研究范畴，本期只读展示。',
 note:'只读原因：策略端评分权重调整属于策略研究动作，需配合回测验证后另行评估。',links:[]});
fc_reg({id:'ro_type_score',cat:'strategy',icon:'🧮',name:'买点类型分',type:'ro',ro:'一买 25 / 二买 20 / 三买 15',
 desc:'三类买点在评分中的固定分值。注意：与"三买确定性最高"的直觉相反，属已知设计议题。',
 note:'只读原因：策略端固定权重。',links:[]});
fc_reg({id:'ro_pool',cat:'strategy',icon:'🏊',name:'选股池门槛',type:'ro',ro:'日均成交额 ≥ 2 亿元',
 desc:'信号端选股池的流动性门槛，剔除成交清淡的僵尸股。',
 note:'只读原因：策略端选股参数。',links:[]});
fc_reg({id:'ro_bearish',cat:'strategy',icon:'🐻',name:'空头买入闸门',type:'ro',ro:'关闭（影子观测中）',
 desc:'开启后大盘转弱时丢弃买入信号。当前以"影子模式"运行：不拦截、只统计若开启会拦多少，等真实弱市样本积累后再评估升级。',
 note:'只读原因：影子观测期，属策略端演进项。',links:[]});
fc_reg({id:'ro_stale_pivot',cat:'strategy',icon:'⏱️',name:'旧中枢时效',type:'ro',ro:'60 天（或上沿涨幅 >30%）',
 desc:'信号端对 buy1 目标价的防线：参照中枢太旧时，目标降级为固定 +9%，防止盈亏比虚高。',
 note:'只读原因：策略端目标价规则。',links:[]});
fc_reg({id:'ro_buy3_target',cat:'strategy',icon:'🎯',name:'三买阶梯目标',type:'ro',ro:'+6%（触发首批止盈）',
 desc:'三买信号无结构目标价，统一按入场价上浮 6% 作为首批止盈触发点，与卖出侧阶梯止盈联动。',
 note:'只读原因：策略端目标价规则。',links:['staged_on']});
fc_reg({id:'ro_stop_max',cat:'strategy',icon:'🛑',name:'止损宽度上限',type:'ro',ro:'单笔止损最宽 8%；超过 15% 的信号直接丢弃',
 desc:'信号端止损带宽约束，是交易侧"单笔风险上限"的上游。',
 note:'只读原因：策略端风控规则。',links:['trade_risk']});
fc_reg({id:'ro_env',cat:'strategy',icon:'🌤️',name:'环境分档',type:'ro',ro:'五档：25 / 18 / 12 / 6 / 0',
 desc:'大盘结构强弱的评分映射，作为信号评分中的"环境"维度（加分项，非一票否决闸门）。',
 note:'只读原因：策略端评分规则；与情绪指标的联动方式仍在研究中。',links:[]});
fc_reg({id:'ro_dead',cat:'strategy',icon:'⚠️',name:'未参数化项',type:'ro',ro:'背驰阈值 / 二买回撤比 / 一买中枢数等',
 desc:'历史上以配置形式存在、但策略引擎实际未读取的参数——配置不生效，已如实标注，避免误以为可调。',
 note:'⚠ 已知能力缺口：待策略端引擎参数化改造完成后转入可调整。',links:[]});
/* 派生指标（概览卡片点击说明用） */
const FC_DERIVED=[
 {id:'d_A',name:'初始本金 A',icon:'🏛️',desc:'本轮资金周期投入的本金（当前 5 万元），是收益率与所有风险线的基准。',formula:'固定值'},
 {id:'d_R',name:'已实现盈亏 R',icon:'📗',desc:'本轮内已平仓交易的净盈亏（卖出收入 − 对应成本 − 已记录费用）。当前费用按零记，可能小幅高估。',formula:'Σ 卖出收入 − 买入成本 − 费用'},
 {id:'d_U',name:'浮动盈亏 U',icon:'📘',desc:'未平仓持仓按保守可成交价（现价打 0.2% 折扣）估算的盈亏，比按现价更悲观、更安全。行情缺失时显示"不可用"。',formula:'Σ (现价×(1−0.2%) − 成本) × 数量'},
 {id:'d_E',name:'生存净值 E',icon:'🫀',desc:'本金 + 已实现 + 浮动盈亏——"现在全部按保守价清盘能拿回多少"，生存底线的判断依据。',formula:'E = A + R + U'},
 {id:'d_D',name:'可运营资金 D',icon:'⚙️',desc:'可用于开新仓的资金池：亏损全额扣减；盈利只按再投入比例（默认一半）放大。所有上限的分母。',formula:'D = A + min(R,0) + 比例×max(R,0)'},
 {id:'d_H',name:'高水位 H',icon:'📏',desc:'历史最高的生存净值，只升不降——衡量"从最好时刻回撤了多少"。',formula:'H = max(历史 E)，初值=本金'},
 {id:'d_SR',name:'本金生存率',icon:'🫁',desc:'生存净值 ÷ 本金。跌到生存底线（默认 60%）触发终局止损。',formula:'SR = E / A'},
 {id:'d_DD',name:'回撤幅度',icon:'📉',desc:'（高水位 − 当前净值）÷ 高水位。决定当前风险状态档位。',formula:'DD = (H − E) / H'}
];
const fc_byId=Object.fromEntries(FC_F.map(f=>[f.id,f]));
const fc_cur=id=>{const d=fc_drafts.find(x=>x.id===id);if(d)return d.to;const f=fc_byId[id];return f?f.def:null};
const fc_disp=(f,v)=>{if(v==null)return '—';if(f.type==='pct')return fmtPct(v);if(f.type==='money')return fmtMoney(v)+(f.unit&&!f.unit.includes('占')&&!f.unit.includes('总资产')?' 元':'');if(f.type==='bool')return v?'开启':'关闭';if(f.type==='types')return v.map(x=>({buy1:'一买',buy2:'二买',buy3:'三买'}[x]||x)).join(' / ');if(f.type==='time')return v;return v+(f.unit&&!['（占资金池）','（占本金）','（高出信号价）','（成本上浮）','（跌破深度）','回撤','折扣','分',''].includes(f.unit)?' '+f.unit.replace('（占资金池）',''):'')};

/* ================= 渲染 ================= */
const fc_$=id=>{
  if(id.startsWith('fc'))return document.getElementById(id);
  return document.getElementById('fc'+id.charAt(0).toUpperCase()+id.slice(1))||document.getElementById(id);
};
const fc_navEl=fc_$('fcNav');
FC_CATS.forEach(c=>{
  const a=document.createElement('a');a.dataset.fcPage=c.id;
  a.innerHTML=`<span>${c.icon} ${c.name}</span>`+(c.id==='history'&&fc_cos.length?`<span class="cnt">${fc_cos.length}</span>`:'');
  a.onclick=()=>fc_go(c.id);fc_navEl.appendChild(a);
});
function fc_go(page){
  document.querySelectorAll('.fc-page').forEach(p=>p.classList.remove('fc-active'));
  const el=fc_$('fcPage-'+page);if(el){el.classList.add('fc-active')}
  fc_navEl.querySelectorAll('a').forEach(a=>a.classList.toggle('fc-active',a.dataset.fcPage===page));
  const c=FC_CATS.find(x=>x.id===page);fc_$('pageTitle').textContent=c?c.title:'搜索结果';
  fc_$('failedBanner').classList.remove('fc-show');
  if(page==='overview')fc_renderOverview();
  if(page==='history')fc_renderHistory();
  fc_renderDraftUI();
}

/* ---------- 概览 ---------- */
const FC_STATE_INFO=[
 {k:'NORMAL',n:'正常',d:'一切照常，可正常开新仓'},
 {k:'CAUTION',n:'警惕',d:'回撤过 10%，各类上限 ×75%'},
 {k:'DEFENSIVE',n:'防守',d:'回撤过 20%，各类上限 ×50%'},
 {k:'REDUCE_ONLY',n:'只减仓',d:'回撤过 30% 或数据异常，禁止新买入'},
 {k:'FAILED',n:'终局止损',d:'家底跌破生存底线且两次确认，不可自动恢复'}];
function fc_stateOf(){return fc_acct.state||'NORMAL'}
function fc_renderOverview(){
  const st=fc_stateOf(),m=fc_acct.M;
  const cards=[
    {id:'d_E',label:'生存净值 E',v:fc_acct.E==null?null:('¥'+fmtMoney(fc_acct.E)),cls:fc_acct.SR>=1?'ok':(fc_acct.SR<=0.65?'bad':'warn'),sub:'本金 ¥'+fmtMoney(fc_acct.A)},
    {id:'d_R',label:'已实现盈亏 R',v:fc_acct.R==null?null:((fc_acct.R>=0?'+':'')+fmtMoney(fc_acct.R)),cls:fc_acct.R>=0?'ok':'bad',sub:'本轮已平仓净盈亏'},
    {id:'d_U',label:'浮动盈亏 U',v:fc_acct.U==null?'不可用':((fc_acct.U>=0?'+':'')+fmtMoney(fc_acct.U)),cls:fc_acct.U==null?'gray':(fc_acct.U>=0?'ok':'warn'),sub:fc_acct.U==null?'行情缺失时不估算':'按保守可成交价'},
    {id:'d_D',label:'可运营资金 D',v:'¥'+fmtMoney(fc_acct.D),cls:'',sub:'所有上限的分母'},
    {id:'d_H',label:'高水位 H',v:'¥'+fmtMoney(fc_acct.H),cls:'',sub:'只升不降'},
    {id:'d_SR',label:'本金生存率',v:fc_acct.SR==null?'不可用':fmtPct(fc_acct.SR),cls:fc_acct.SR>=1?'ok':(fc_acct.SR<=0.65?'bad':'warn'),sub:'底线 '+fmtPct(fc_cur('survival'),0)},
    {id:'d_DD',label:'回撤幅度',v:fc_acct.DD==null?'不可用':fmtPct(fc_acct.DD),cls:fc_acct.DD>=0.3?'bad':(fc_acct.DD>=0.2?'warn':(fc_acct.DD>=0.1?'warn':'ok')),sub:'警惕/防守/只减仓 '+fmtPct(fc_cur('dd_cau'),0)+'/'+fmtPct(fc_cur('dd_def'),0)+'/'+fmtPct(fc_cur('dd_ro'),0)},
    {id:'d_state',label:'风险状态',v:FC_STATE_INFO.find(s=>s.k===st).n,cls:st==='NORMAL'?'ok':(st==='FAILED'||st==='REDUCE_ONLY'?'bad':'warn'),sub:FC_STATE_INFO.find(s=>s.k===st).d+(m!=null&&m<1?'（上限×'+fmtPct(m,0)+'）':'')}
  ];
  const idx=FC_STATE_INFO.findIndex(s=>s.k===st);
  const stepper=FC_STATE_INFO.map((s,i)=>`<div class="fc-st ${i===idx?'fc-cur':(i<idx?'fc-past':'')} ${s.k==='FAILED'?'fc-term':''}" title="${s.d}"><b>${s.n}</b>${s.k==='NORMAL'?'回撤<10%':s.k==='CAUTION'?'≥10%':s.k==='DEFENSIVE'?'≥20%':s.k==='REDUCE_ONLY'?'≥30%':'生存率≤底线'}</div>`).join('');
  const grossPct=fc_acct.max_gross?fc_acct.gross/fc_acct.max_gross:0;
  const riskPct=fc_acct.max_open_risk?fc_acct.open_risk/fc_acct.max_open_risk:0;
  const indRows=Object.entries(fc_acct.industry||{}).map(([k,v])=>{
    const p=v/(fc_acct.industry_limit||1);
    return `<div class="fc-barrow"><span class="fc-bl">${k}行业</span><div class="fc-track"><div class="fc-fill ${p>1?'fc-over':''}" style="width:${Math.min(100,p*100)}%"></div></div><span class="fc-bv"><b>${fmtMoney(v)}</b> / ${fmtMoney(fc_acct.industry_limit)}${p>1?' · 已超限只能减':''}</span></div>`}).join('')||'<div class="fc-empty" style="padding:20px">暂无持仓行业</div>';
  const otherRoom=fc_acct.industry_limit?`<div class="fc-barrow"><span class="fc-bl">其他行业可用额度</span><div class="fc-track"><div class="fc-fill fc-full" style="width:100%"></div></div><span class="fc-bv"><b>${fmtMoney(fc_acct.industry_limit)}</b> 全额可用</span></div>`:'';
  fc_$('fcPage-overview').innerHTML=`
  <div class="fc-metrics">${cards.map(c=>`
    <div class="fc-mc ${c.cls}" data-d="${c.id==='d_state'?'':c.id}" tabindex="0" role="button">
      <div class="fc-label"><span>${c.label}</span></div>
      <div class="fc-value ${c.v==null||c.v==='不可用'?'na':''}">${c.v??'不可用'}</div>
      <div class="fc-sub">${c.sub}</div>
    </div>`).join('')}</div>
  <div class="fc-card"><h3>🚦 风险状态机 <span class="fc-more" id="demoState">演示：切换状态 ▾</span></h3>
    <div class="fc-stepper">${stepper}</div>
    <p style="font-size:12px;color:var(--text3);margin-top:8px">状态由回撤深度自动判定；行情缺失/超时也会临时进入"只减仓"。降档后各类上限同乘状态系数。</p>
  </div>
  <div class="fc-card"><h3>📦 组合占用</h3>
    <div class="fc-barrow"><span class="fc-bl">总市值敞口</span><div class="fc-track"><div class="fc-fill ${grossPct>1?'fc-over':''}" style="width:${Math.min(100,grossPct*100)}%"></div></div><span class="fc-bv"><b>${fmtMoney(fc_acct.gross)}</b> / ${fmtMoney(fc_acct.max_gross)}</span></div>
    <div class="fc-barrow"><span class="fc-bl">开放风险（最坏损失）</span><div class="fc-track"><div class="fc-fill ${riskPct>1?'fc-over':''}" style="width:${Math.min(100,riskPct*100)}%"></div></div><span class="fc-bv"><b>${fmtMoney(fc_acct.open_risk)}</b> / ${fmtMoney(fc_acct.max_open_risk)}</span></div>
    ${indRows}${otherRoom}
    <div class="fc-barrow"><span class="fc-bl">持仓股票数</span><div class="fc-track"><div class="fc-fill" style="width:${fc_acct.stocks/fc_acct.max_stocks*100}%"></div></div><span class="fc-bv"><b>${fc_acct.stocks} / ${fc_acct.max_stocks} 只</b></span></div>
    <div class="fc-barrow"><span class="fc-bl">现金（含缓冲垫）</span><div class="fc-track"><div class="fc-fill fc-full" style="width:${Math.min(100,fc_acct.cash/fc_acct.D*100)}%"></div></div><span class="fc-bv"><b>${fmtMoney(fc_acct.cash)}</b>，其中缓冲 ${fmtMoney(fc_acct.cash_buffer)}</span></div>
  </div>
  <div class="fc-card"><h3>📡 数据质量</h3>
    <div class="fc-barrow"><span class="fc-bl">行情完整度</span><div class="fc-track"><div class="fc-fill ${fc_acct.quote_complete?'fc-full':'fc-over'}" style="width:${fc_acct.quote_complete?100:40}%"></div></div><span class="fc-bv"><b>${fc_acct.quote_complete?'完整':'缺失/超时（已降级）'}</b>，时效要求 ${fc_cur('quote_age')} 秒</span></div>
    <div class="fc-barrow"><span class="fc-bl">底线确认计数</span><div class="fc-track"><div class="fc-fill" style="width:${(fc_acct.hits||0)/(fc_acct.confirms||2)*100}%"></div></div><span class="fc-bv"><b>${fc_acct.hits||0} / ${fc_acct.confirms||2}</b> 次独立确认</span></div>
    <p style="font-size:12px;color:var(--text3)">数据时间：${fc_acct.generated_at}${fc_acct.demo?'（演示快照）':''}</p>
  </div>`;
  document.querySelectorAll('.fc-mc[data-d]').forEach(el=>el.onclick=()=>{const d=FC_DERIVED.find(x=>x.id===el.dataset.d);if(d)fc_showDerived(d)});
  fc_$('demoState').onclick=(e)=>{e.stopPropagation();
    const opts=['NORMAL','CAUTION','DEFENSIVE','REDUCE_ONLY','FAILED'];
    fc_modal('演示：切换风险状态',`<p style="margin-bottom:10px">仅用于预览各状态下的界面表现（演示模式）。切换后概览卡片与状态条随之变化；<b>终局止损</b>会展示横幅并锁定调整入口。</p>
    <div class="fc-filters">${opts.map(o=>`<span class="fc-fb ${o===st?'fc-active':''}" data-st="${o}">${FC_STATE_INFO.find(s=>s.k===o).n}</span>`).join('')}</div>`,
    [{t:'关闭',cls:'fc-btn-ghost',fn:fc_closeModal}]);
    document.querySelectorAll('.fc-fb[data-st]').forEach(b=>b.onclick=()=>{
      fc_acct.state=b.dataset.st;fc_acct.M=b.dataset.st==='NORMAL'?1:b.dataset.st==='CAUTION'?0.75:b.dataset.st==='DEFENSIVE'?0.5:0;
      if(b.dataset.st==='FAILED'){fc_acct.SR=0.58;fc_acct.DD=0.42;fc_acct.E=29000}else{fc_acct.SR=0.998;fc_acct.DD=0.0018;fc_acct.E=49909.5}
      fc_closeModal();fc_renderOverview();fc_go('overview');
    });
  };
  if(st==='FAILED')fc_showFailedBanner();
}
function fc_showFailedBanner(){
  fc_$('failedDetail').textContent=`触发时间 ${fc_acct.generated_at} · 触发时净值 ¥${fmtMoney(fc_acct.E??29000)} · 生存率 ${fmtPct(fc_acct.SR??0.58)}`;
  fc_$('failedBanner').classList.add('fc-show');
}
function fc_showDerived(d){
  fc_modal(d.icon+' '+d.name,`<div class="fc-dsec"><div class="fc-dh">这是什么</div><p>${d.desc}</p></div><div class="fc-dsec"><div class="fc-dh">计算方式</div><div class="fc-kv">${d.formula}</div></div>`,[{t:'关闭',cls:'fc-btn-ghost',fn:fc_closeModal}]);
}

/* ---------- 配置页 ---------- */
function fc_renderConfig(cat){
  const page=fc_$('fcPage-'+cat);if(page.dataset.built)return;page.dataset.built=1;
  const list=FC_F.filter(f=>f.cat===cat);
  page.innerHTML=`
  <div class="fc-filters" data-cat="${cat}">
    <span class="fc-fb fc-active" data-f="all">全部 ${list.length}</span>
    ${cat!=='strategy'?`<span class="fc-fb" data-f="adj">可调整 ${list.filter(f=>f.type!=='ro').length}</span>`:''}
    ${list.some(f=>f.high)?`<span class="fc-fb" data-f="high">高影响 ${list.filter(f=>f.high).length}</span>`:''}
    ${cat==='strategy'?`<span class="fc-fb" data-f="ro">系统规则</span>`:''}
  </div>
  <div class="fc-card" style="padding:0;overflow-x:auto">
    <table class="fc-et"><thead><tr><th style="width:190px">配置项</th><th>当前值</th><th>默认值</th><th>说明</th><th>标识</th></tr></thead>
    <tbody>${list.map(f=>fc_rowHTML(f)).join('')}</tbody></table>
  </div>`;
  page.querySelectorAll('.fc-fb').forEach(b=>b.onclick=()=>{
    page.querySelectorAll('.fc-fb').forEach(x=>x.classList.remove('fc-active'));b.classList.add('fc-active');
    const f=b.dataset.f;
    page.querySelectorAll('tbody tr').forEach(tr=>{
      const fid=tr.dataset.id,fo=fc_byId[fid];
      tr.style.display=(f==='all'||(f==='adj'&&fo.type!=='ro')||(f==='high'&&fo.high)||(f==='ro'&&fo.type==='ro'))?'':'none';
    });
  });
  page.querySelectorAll('tbody tr').forEach(tr=>tr.onclick=()=>fc_openDrawer(fc_byId[tr.dataset.id]));
}
function fc_rowHTML(f){
  const ch=fc_drafts.find(d=>d.id===f.id);
  const curV=ch?ch.to:f.def;
  return `<tr data-id="${f.id}">
    <td class="fc-fname">${f.icon} ${f.name}</td>
    <td class="fc-fval ${ch?'fc-changed':''} ${f.type==='ro'?'fc-ro':''}">${f.type==='ro'?f.ro:fc_disp(f,curV)}</td>
    <td style="color:var(--text3);font-size:12.5px">${f.type==='ro'?'—':fc_disp(f,f.def)}</td>
    <td class="fc-fdesc" title="${(f.desc||'').replace(/"/g,'&quot;')}">${f.desc||''}</td>
    <td>${f.type==='ro'?(f.id==='ro_dead'?'<span class="fc-badge fc-b-warn2">⚠ 配置不生效</span>':'<span class="fc-badge fc-b-ro">仅展示</span>'):'<span class="fc-badge fc-b-adj">可调整</span>'}${f.high?'<span class="fc-badge fc-b-high">高影响</span>':''}</td>
  </tr>`;
}
['entry','risk','exit','signal','strategy'].forEach(fc_renderConfig);

/* ---------- 详情抽屉 ---------- */
function fc_openDrawer(f){
  const ch=fc_drafts.find(d=>d.id===f.id);
  fc_$('dTitle').innerHTML=`${f.icon} ${f.name} ${f.high?'<span class="fc-badge fc-b-high">高影响</span>':''} ${f.type==='ro'?'<span class="fc-badge fc-b-ro">仅展示</span>':'<span class="fc-badge fc-b-adj">可调整</span>'}`;
  fc_$('dBody').innerHTML=`
  <div class="fc-dsec"><div class="fc-dh">这是什么</div><p>${f.desc}</p></div>
  ${f.formula?`<div class="fc-dsec"><div class="fc-dh">计算方式</div><div class="fc-kv">${f.formula}</div></div>`:''}
  <div class="fc-dsec"><div class="fc-dh">当前值 / 默认值</div><div class="fc-kv">当前 <b style="color:var(--primary)">${f.type==='ro'?f.ro:fc_disp(f,ch?ch.to:f.def)}</b>　·　默认 ${f.type==='ro'?'—':fc_disp(f,f.def)}${ch?'　<span style="color:var(--warn)">（草稿中）</span>':''}</div></div>
  ${f.type!=='ro'?`<div class="fc-dsec"><div class="fc-dh">系统检查</div><p>${f.check||'数值范围 '+f.min+' ~ '+f.max}</p></div>`:''}
  ${f.up||f.down?`<div class="fc-dsec"><div class="fc-dh">调整影响</div><div class="fc-updown">
    ${f.up?`<div class="fc-u"><b>⬆ 调大会怎样</b>${f.up}</div>`:''}
    ${f.down?`<div class="fc-d"><b>⬇ 调小会怎样</b>${f.down}</div>`:''}
  </div></div>`:''}
  <div class="fc-dsec"><div class="fc-dh">生效时机</div><p>${f.timing||'—'}</p></div>
  ${f.example?`<div class="fc-dsec"><div class="fc-dh">举个例子</div><div class="fc-kv">${f.example}</div></div>`:''}
  ${f.note?`<div class="fc-dsec"><div class="fc-dh">为什么不可调</div><p>${f.note}</p></div>`:''}
  ${f.links&&f.links.length?`<div class="fc-dsec"><div class="fc-dh">关联因子</div><div class="fc-linkline">${f.links.map(l=>fc_byId[l]?`<span class="fc-lk" data-l="${l}">${fc_byId[l].icon} ${fc_byId[l].name}</span>`:'').join('')}</div></div>`:''}
  <div id="editMount"></div>`;
  fc_$('dBody').querySelectorAll('.fc-lk').forEach(l=>l.onclick=()=>fc_openDrawer(fc_byId[l.dataset.l]));
  const foot=fc_$('dFoot');foot.innerHTML='';
  if(f.type!=='ro'){
    const b=document.createElement('button');b.className='fc-btn';b.textContent=fc_drafts.find(d=>d.id===f.id)?'修改草稿值':'调整';
    if(fc_stateOf()==='FAILED'){b.disabled=true;b.textContent='终局状态下不可调整'}
    b.onclick=()=>fc_renderEdit(f);foot.appendChild(b);
  } else {
    const s=document.createElement('span');s.style.cssText='font-size:12px;color:var(--text3);align-self:center';s.textContent=f.note||'该因子由系统计算或属交易纪律，仅展示。';foot.appendChild(s);
  }
  fc_$('drawerMask').classList.add('fc-show');fc_$('drawer').classList.add('fc-show');
}
function fc_closeDrawer(){fc_$('drawerMask').classList.remove('fc-show');fc_$('drawer').classList.remove('fc-show')}
fc_$('dClose').onclick=fc_closeDrawer;fc_$('drawerMask').onclick=fc_closeDrawer;

/* ---------- 编辑 ---------- */
let fc_pendingAmbiguity=null;
function fc_renderEdit(f){
  const mount=fc_$('editMount');
  const curV=fc_cur(f.id);
  const showVal=f.type==='pct'?(curV*100):curV;
  let ctl='';
  if(f.type==='bool'){ctl=`<select id="eIn"><option value="1" ${curV?'selected':''}>开启</option><option value="0" ${!curV?'selected':''}>关闭</option></select>`}
  else if(f.type==='types'){ctl=`<div class="fc-types">${['buy1','buy2','buy3'].map(t=>`<label><input type="checkbox" data-t="${t}" ${curV.includes(t)?'checked':''}>${{buy1:'一买',buy2:'二买',buy3:'三买'}[t]}</label>`).join('')}</div>`}
  else if(f.type==='time'){ctl=`<input type="text" id="eIn" value="${curV}" placeholder="HH:MM">`}
  else{ctl=`<div class="fc-inrow"><input type="number" id="eIn" value="${showVal}" step="${f.step||(f.type==='int'?1:0.01)}"><span class="fc-unit">${f.type==='pct'?'%':(f.unit||'')}</span></div>`}
  mount.innerHTML=`<div class="fc-editbox" id="eBox">
    <label>${f.high?'⚠ 高影响配置：请先阅读上方"调整影响"再修改。':''}输入新值${f.type==='pct'?'（按百分数输入，如 0.75）':''}</label>
    ${ctl}<div class="fc-err" id="eErr"></div>
    <div style="margin-top:10px;display:flex;gap:8px">
      <button class="fc-btn" id="eAdd">加入调整草稿</button>
      <button class="fc-btn fc-btn-ghost" id="eCancel">取消</button>
    </div>
  </div>`;
  mount.scrollIntoView({behavior:'smooth',block:'nearest'});
  fc_$('eCancel').onclick=()=>{mount.innerHTML=''};
  fc_$('eAdd').onclick=()=>{
    const err=fc_$('eErr');err.classList.remove('fc-show');
    let v;
    if(f.type==='bool'){v=fc_$('eIn').value==='1'}
    else if(f.type==='types'){
      v=[...document.querySelectorAll('.fc-types input:checked')].map(x=>x.dataset.t);
      if(!v.length){err.textContent='至少保留一种入场类型';err.classList.add('fc-show');return}
    }
    else if(f.type==='time'){
      v=fc_$('eIn').value.trim();
      if(!/^\d{1,2}:\d{2}$/.test(v)){err.textContent='格式须为 HH:MM（如 10:00）';err.classList.add('fc-show');return}
    }
    else{
      const raw=fc_$('eIn').value.trim();
      if(raw===''){err.textContent='请输入数值';err.classList.add('fc-show');return}
      const n=Number(raw);
      if(isNaN(n)){err.textContent='必须是数字';err.classList.add('fc-show');return}
      if(f.type==='int'&&!Number.isInteger(n)){err.textContent='必须为整数';err.classList.add('fc-show');return}
      if(f.type==='pct'){
        if(n!==raw&&raw.includes('.')){
          // 小数歧义：0.3 是 0.3% 还是 30%？
          const small=Number(raw);
          if(small>0&&small<1&&small*100<=f.max*100){
            fc_pendingAmbiguity={f,raw:small};err.textContent='';err.classList.remove('fc-show');
            fc_modal('确认输入含义',`<p>检测到输入了小数 <b>${raw}</b>。作为百分数输入，它的含义是？</p>
              <div style="margin-top:12px;display:flex;gap:10px">
                <button class="fc-btn" id="ambPct">${small}%（按百分数输入）</button>
                <button class="fc-btn fc-btn-ghost" id="ambWhole">${(small*100).toFixed(0)}%（把 ${raw} 当作 0→1 比例）</button>
              </div>`,[]);
            fc_$('ambPct').onclick=()=>{fc_closeModal();fc_commitPct(f,small)};
            fc_$('ambWhole').onclick=()=>{fc_closeModal();fc_commitPct(f,small*100)};
            return;
          }
        }
        if(n<f.min*100||n>f.max*100){err.textContent=`范围 ${fmtPct(f.min,2)} ~ ${fmtPct(f.max,2)}`;err.classList.add('fc-show');return}
        v=n/100;
      } else {
        if(n<f.min||n>f.max){err.textContent=`范围 ${f.min} ~ ${f.max}${f.unit?' '+f.unit:''}`;err.classList.add('fc-show');return}
        v=n;
      }
    }
    fc_addDraft(f,v);mount.innerHTML='';
  };
}
function fc_commitPct(f,percent){
  if(percent<f.min*100||percent>f.max*100){fc_toast('范围 '+fmtPct(f.min,2)+' ~ '+fmtPct(f.max,2),true);return}
  fc_addDraft(f,percent/100);
}
function fc_addDraft(f,to){
  const same=JSON.stringify(to)===JSON.stringify(f.def)&&!fc_drafts.find(d=>d.id===f.id);
  if(JSON.stringify(to)===JSON.stringify(fc_cur(f.id))&&fc_drafts.find(d=>d.id===f.id)?.to===to){}
  if(JSON.stringify(to)===JSON.stringify(f.def)){
    fc_drafts=fc_drafts.filter(d=>d.id!==f.id);fc_store.set(LS_DRAFT,fc_drafts);
    fc_toast('已恢复默认值，移出草稿');fc_renderDraftUI();fc_refreshRows(f.cat);fc_closeDrawer();return;
  }
  const ex=fc_drafts.find(d=>d.id===f.id);
  const rec={id:f.id,name:f.name,icon:f.icon,cat:f.cat,from:ex?ex.to:(f.type==='ro'?null:f.def),to,high:!!f.high,timing:f.timing||''};
  if(ex)Object.assign(ex,rec);else fc_drafts.push(rec);
  fc_store.set(LS_DRAFT,fc_drafts);fc_renderDraftUI();fc_refreshRows(f.cat);
  fc_toast(`已加入草稿：${f.name} → ${fc_disp(f,to)}`);fc_closeDrawer();
}
function fc_refreshRows(cat){
  const page=fc_$('fcPage-'+cat);if(!page)return;delete page.dataset.built;fc_renderConfig(cat);
  if(page.classList.contains('fc-active'))page.classList.add('fc-active');
}

/* ---------- 草稿栏与提交 ---------- */
function fc_renderDraftUI(){
  fc_$('draftCount').textContent=fc_drafts.length;
  fc_$('draftbar').classList.toggle('fc-show',fc_drafts.length>0);
}
fc_$('draftClear').onclick=()=>{fc_drafts=[];fc_store.set(LS_DRAFT,fc_drafts);fc_refreshAll();fc_renderDraftUI();fc_toast('草稿已清空')};
function fc_refreshAll(){['entry','risk','exit','signal','strategy'].forEach(c=>{delete fc_$('fcPage-'+c).dataset.built;fc_renderConfig(c)})}
fc_$('draftReview').onclick=()=>{
  if(!fc_drafts.length)return;
  const conflicts=fc_runValidations();
  const items=fc_drafts.map(d=>{const f=fc_byId[d.id];return `<div style="display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-bottom:1px solid var(--divider)">
    <span>${d.icon} ${d.name}</span><span><s style="color:var(--text3)">${fc_disp(f,d.from)}</s> → <b style="color:var(--warn)">${fc_disp(f,d.to)}</b></span></div>`}).join('');
  if(conflicts.length){
    fc_modal('⚠ 组合校验未通过',conflicts.map(c=>`<div class="fc-conflict"><b>${c.title}</b><br>${c.msg}</div>`).join('')+`<p style="color:var(--text3);font-size:12px">请点击"返回修改"，调整相关因子后再提交。</p>`,
    [{t:'返回修改',cls:'fc-btn',fn:fc_closeModal}]);
    return;
  }
  const highs=fc_drafts.filter(d=>d.high);
  const proceed=()=>{
    fc_modal('填写调整理由',`
    ${items}
    <p style="margin:12px 0 6px;font-size:12.5px;color:var(--text2)">调整理由（必填，≥10 字）——将随调整单永久留痕：</p>
    <textarea class="fc-reason" id="coReason" placeholder="例如：复盘 W37 发现僵尸仓占用资金，将持仓时间上限 10 天收窄为 7 天"></textarea>
    <div class="fc-err" id="coErr" style="display:none;color:var(--bad);font-size:12px;margin-top:6px"></div>`,
    [{t:'取消',cls:'fc-btn-ghost',fn:fc_closeModal},{t:'生成调整单',cls:'fc-btn',fn:()=>{
      const r=fc_$('coReason').value.trim();
      if(r.length<10){const e=fc_$('coErr');e.textContent='理由不足 10 字，请补充（当前 '+r.length+' 字）';e.style.display='block';return}
      fc_generateCO(r);
    }}]);
  };
  if(highs.length){
    fc_modal('⚠ 高影响配置确认',`
    <p>本次调整包含 <b>${highs.length}</b> 项高影响配置：</p>
    ${highs.map(d=>{const f=fc_byId[d.id];return `<div class="fc-conflict" style="background:var(--warn-bg);border-color:#ffd591"><b style="color:var(--warn)">${d.icon} ${d.name}：${fc_disp(f,d.from)} → ${fc_disp(f,d.to)}</b><br>${f.up||f.down||''}${f.example?'<br>例：'+f.example:''}</div>`}).join('')}
    <label style="display:flex;gap:8px;align-items:flex-start;font-size:13px;margin-top:8px"><input type="checkbox" id="hiAck" style="margin-top:4px">我已理解上述变更的影响（生存底线变更会改变终局止损的触发边界；盈利再投入变更会改变资金池滚动方式）</label>`,
    [{t:'返回',cls:'fc-btn-ghost',fn:fc_closeModal},{t:'继续',cls:'fc-btn',fn:()=>{
      if(!fc_$('hiAck').checked){fc_toast('请先勾选理解声明',true);return}
      proceed();
    }}]);
    return;
  }
  proceed();
};
/* 组合校验：镜像系统启动检查（口径：指南 §12） */
function fc_runValidations(){
  const v=id=>fc_cur(id),out=[];
  const need=ids=>ids.every(id=>fc_drafts.some(d=>d.id===id)||true);
  if(['dd_cau','dd_def','dd_ro'].some(id=>fc_drafts.some(d=>d.id===id))){
    const a=v('dd_cau'),b=v('dd_def'),c=v('dd_ro');
    if(!(a>0&&a<b&&b<c&&c<1))out.push({title:'回撤三档必须依次增大（0 < 警惕 < 防守 < 只减仓 < 100%）',msg:`当前：警惕 ${fmtPct(a)} · 防守 ${fmtPct(b)} · 只减仓 ${fmtPct(c)}。请整体规划三档数值。`});
  }
  if(['ind_norm','ind_cau','ind_def'].some(id=>fc_drafts.some(d=>d.id===id))){
    const a=v('ind_def'),b=v('ind_cau'),c=v('ind_norm');
    if(!(a<=b&&b<=c))out.push({title:'行业上限必须越险越紧（防守 ≤ 警惕 ≤ 正常）',msg:`当前：正常 ${fmtPct(c)} · 警惕 ${fmtPct(b)} · 防守 ${fmtPct(a)}。`});
  }
  if(['trade_risk','portfolio_risk'].some(id=>fc_drafts.some(d=>d.id===id))){
    if(!(v('trade_risk')<=v('portfolio_risk')))out.push({title:'单笔风险不得超过组合风险',msg:`当前：单笔 ${fmtPct(v('trade_risk'))} > 组合 ${fmtPct(v('portfolio_risk'))}。请同时调整两者。`});
  }
  if(['mult_cau','mult_def'].some(id=>fc_drafts.some(d=>d.id===id))){
    const a=v('mult_def'),b=v('mult_cau');
    if(!(a>=0&&a<=b&&b<=1))out.push({title:'收缩力度不得回弹（0 ≤ 防守 ≤ 警惕 ≤ 100%）',msg:`当前：警惕 ${fmtPct(b,0)} · 防守 ${fmtPct(a,0)}。越危险应收得越紧。`});
  }
  if(fc_drafts.some(d=>d.id==='confirms')&&v('confirms')<2)out.push({title:'底线确认次数至少 2 次',msg:'这是防止单次行情毛刺误伤终局止损的最低要求。'});
  if(fc_drafts.some(d=>d.id==='quote_age')&&v('quote_age')<=0)out.push({title:'行情时效必须为正',msg:''});
  fc_drafts.forEach(d=>{const f=fc_byId[d.id];
    if(f.type==='pct'&&(d.to<f.min||d.to>f.max))out.push({title:`${d.name} 超出范围`,msg:`允许范围 ${fmtPct(f.min)} ~ ${fmtPct(f.max)}。`});
    if((f.type==='int'||f.type==='float'||f.type==='money')&&(d.to<f.min||d.to>f.max))out.push({title:`${d.name} 超出范围`,msg:`允许范围 ${f.min} ~ ${f.max}${f.unit?' '+f.unit:''}。`});
  });
  return out;
}
/* ---------- 调整单 ---------- */
function fc_coSeq(){const n=(fc_store.get(LS_SEQ,0))+1;fc_store.set(LS_SEQ,n);return n}
function fc_generateCO(reason){
  const d=new Date(),pad=n=>String(n).padStart(2,'0');
  const id=`CO-${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}-${String(fc_coSeq()).padStart(2,'0')}`;
  const time=`${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  const lines=fc_drafts.map(dd=>{const f=fc_byId[dd.id];return `| ${dd.name} | ${fc_disp(f,dd.from)} | ${fc_disp(f,dd.to)} |`}).join('\n');
  const guide=fc_drafts.map(dd=>`- ${dd.name}：${dd.timing||'下一轮评估生效'}；已持仓不受影响`).join('\n');
  const md=`# 调整单 ${id}

生成时间：${time}
调整理由：${reason}

| 配置项 | 调整前 | 调整后 |
|---|---|---|
${lines}

应用指引（请在维护时段人工应用）：
${guide}

高影响项：${fc_drafts.filter(x=>x.high).map(x=>x.name).join('、')||'无'}
注意：本调整单由因子中心生成留痕；应用前请备份当前配置，应用后回到界面回填结果。
`;
  const co={id,time,reason,items:fc_drafts.map(x=>({...x})),status:'exported',note:''};
  fc_cos.unshift(co);fc_store.set(LS_CO,fc_cos);
  fc_drafts=[];fc_store.set(LS_DRAFT,fc_drafts);fc_renderDraftUI();fc_refreshAll();
  fc_modal('✅ 调整单已生成 '+id,`
  <p style="margin-bottom:8px">已存入调整历史。请核对以下内容，按指引在维护时段应用：</p>
  <div style="max-height:200px;overflow:auto;margin-bottom:10px">${lines.replace(/\|/g,'').split('\n').slice(0,50).join('<br>')}</div>
  <p style="font-size:12px;color:var(--text3);margin-bottom:6px">完整内容（可复制或下载存档）：</p>
  <textarea class="fc-co-md" id="coMd" readonly>${md}</textarea>`,
  [{t:'下载 .md',cls:'fc-btn-ghost',fn:()=>{fc_download(id+'.md',md)}},{t:'复制',cls:'fc-btn-ghost',fn:async()=>{
    try{await navigator.clipboard.writeText(md);fc_toast('已复制到剪贴板')}catch(e){fc_$('coMd').select();document.execCommand('copy');fc_toast('已复制')}
  }},{t:'完成',cls:'fc-btn',fn:()=>{fc_closeModal();fc_go('history')}}]);
  fc_updateNavCnt();
}
function fc_download(name,text){
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/markdown'}));a.download=name;a.click();URL.revokeObjectURL(a.href);
}
/* ---------- 历史 ---------- */
function fc_renderHistory(){
  fc_updateNavCnt();
  if(!fc_cos.length){fc_$('fcPage-history').innerHTML=`<div class="fc-card"><div class="fc-empty">暂无调整单<br><span style="font-size:12px">在配置页调整任意因子并提交后，调整单会出现在这里</span></div></div>`;return}
  fc_$('fcPage-history').innerHTML=fc_cos.map((c,i)=>`
  <div class="fc-hist-item ${c.status}">
    <div class="fc-ht"><b>${c.id}</b><span>
      <span class="fc-status-pill fc-st-${c.status}">${{exported:'待应用',applied:'已生效',error:'应用异常',discarded:'已放弃'}[c.status]}</span>
    </span></div>
    <div class="fc-hmeta">${c.time} · ${c.items.length} 项 · ${c.reason}</div>
    <div class="fc-hitems">${c.items.map(it=>`${it.icon} ${it.name}：<s>${it.fromDisp||''}</s>→<b>${it.toDisp||''}</b>`).join('；')}
    ${c.items.map(it=>{const f=fc_byId[it.id];return f?`${it.icon} ${it.name}：${fc_disp(f,it.from)} → <b style="color:var(--warn)">${fc_disp(f,it.to)}</b>`:''}).join('；')}
    ${c.note?`<div class="fc-hmeta">备注：${c.note}</div>`:''}
    <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">
      ${c.status==='exported'?`
      <button class="fc-btn" style="padding:5px 14px;font-size:12px" onclick="fc_backfill('${c.id}','applied')">✓ 已生效</button>
      <button class="fc-btn fc-btn-ghost" style="padding:5px 14px;font-size:12px" onclick="fc_backfill('${c.id}','error')">⚠ 应用异常</button>
      <button class="fc-btn fc-btn-ghost" style="padding:5px 14px;font-size:12px" onclick="fc_backfill('${c.id}','discarded')">放弃</button>`:''}
      <button class="fc-btn fc-btn-ghost" style="padding:5px 14px;font-size:12px" onclick="fc_coDownload('${c.id}')">下载调整单</button>
  </div>`).join('');
}
window.fc_backfill=(id,st)=>{
  const c=fc_cos.find(x=>x.id===id);if(!c)return;
  const needNote=st!=='applied';
  fc_modal('回填结果：'+id,`<p style="margin-bottom:8px">状态将记录为：<b>${{applied:'已生效',error:'应用异常',discarded:'已放弃'}[st]}</b>${needNote?'（请填写说明）':''}</p>
  <textarea class="fc-reason" id="bfNote" placeholder="${st==='applied'?'如何验证的？（可选）':st==='error'?'异常现象与回退情况（必填）':'放弃原因（必填）'}"></textarea>`,
  [{t:'取消',cls:'fc-btn-ghost',fn:fc_closeModal},{t:'确认',cls:'fc-btn',fn:()=>{
    const n=fc_$('bfNote').value.trim();
    if(needNote&&n.length<3){fc_toast('请填写说明',true);return}
    c.status=st;c.note=n;fc_store.set(LS_CO,fc_cos);fc_closeModal();fc_renderHistory();fc_toast('已回填');
  }}]);
};
window.fc_coDownload=id=>{const c=fc_cos.find(x=>x.id===id);if(!c)return;
  const md=`# 调整单 ${c.id}\n\n生成时间：${c.time}\n调整理由：${c.reason}\n状态：${{exported:'待应用',applied:'已生效',error:'应用异常',discarded:'已放弃'}[c.status]}\n\n| 配置项 | 调整前 | 调整后 |\n|---|---|---|\n${c.items.map(it=>{const f=fc_byId[it.id];return f?`| ${it.name} | ${fc_disp(f,it.from)} | ${fc_disp(f,it.to)} |`:''}).join('\n')}\n${c.note?'\n备注：'+c.note:''}\n`;
  fc_download(id+'.md',md)};
function fc_updateNavCnt(){const old=fc_navEl.querySelector('a[data-fc-page="history"] .fc-cnt');if(old)old.remove();const link=fc_navEl.querySelector('a[data-fc-page="history"]');if(fc_cos.length){const s=document.createElement('span');s.className='fc-cnt';s.textContent=fc_cos.length;link.appendChild(s)}}

/* ---------- 搜索 ---------- */
fc_$('search').addEventListener('input',e=>{
  const q=e.target.value.trim();
  if(!q){fc_go('overview');return}
  const hits=FC_F.filter(f=>(f.name+(f.desc||'')+(f.ro||'')).toLowerCase().includes(q.toLowerCase()));
  document.querySelectorAll('.fc-page').forEach(p=>p.classList.remove('fc-active'));
  fc_$('fcPage-search').classList.add('fc-active');fc_$('pageTitle').textContent=`搜索“${q}”`;
  fc_navEl.querySelectorAll('a').forEach(a=>a.classList.remove('fc-active'));
  fc_$('fcPage-search').innerHTML=hits.length?`<div class="fc-card" style="padding:0;overflow-x:auto"><table class="fc-et"><thead><tr><th style="width:190px">配置项</th><th>当前值</th><th>类别</th><th>说明</th></tr></thead><tbody>
    ${hits.map(f=>`<tr data-id="${f.id}"><td class="fc-fname">${f.icon} ${f.name}</td><td class="fc-fval ${f.type==='ro'?'ro':''}">${f.type==='ro'?f.ro:fc_disp(f,fc_cur(f.id))}</td><td style="font-size:12px;color:var(--text3)">${FC_CATS.find(c=>c.id===f.cat).name}</td><td class="fc-fdesc">${f.desc||''}</td></tr>`).join('')}
  </tbody></table></div>`:`<div class="fc-card"><div class="fc-empty">没有匹配“${q}”的因子<br><span style="font-size:12px">试试：风险 / 止损 / 行业 / 手数</span></div></div>`;
  fc_$('fcPage-search').querySelectorAll('tbody tr').forEach(tr=>tr.onclick=()=>fc_openDrawer(fc_byId[tr.dataset.id]));
});

/* ---------- 手册浮层 ---------- */
fc_$('manualBtn').onclick=()=>{fc_$('manualMask').classList.add('fc-show')};
fc_$('manualClose').onclick=()=>fc_$('manualMask').classList.remove('fc-show');
fc_$('manualMask').addEventListener('click',e=>{if(e.target===fc_$('manualMask'))fc_$('manualMask').classList.remove('fc-show')});
fc_$('manualFrame').addEventListener('load',()=>{fc_$('manualFail').style.display='none';fc_$('manualFrame').style.display='block'});
fc_$('manualFrame').addEventListener('error',()=>{fc_$('manualFrame').style.display='none';fc_$('manualFail').style.display='flex'});
fc_$('manualLink2').onclick=()=>{fc_$('manualMask').classList.add('fc-show')};

/* ---------- modal / toast ---------- */
function fc_modal(title,body,btns){
  fc_$('mTitle').textContent=title;fc_$('mBody').innerHTML=body;
  const foot=fc_$('mFoot');foot.innerHTML='';
  (btns||[]).forEach(b=>{const el=document.createElement('button');el.className='fc-btn '+(b.cls||'');el.textContent=b.t;el.onclick=b.fn;foot.appendChild(el)});
  fc_$('modalMask').classList.add('fc-show');
}
function fc_closeModal(){fc_$('modalMask').classList.remove('fc-show')}
fc_$('mClose').onclick=fc_closeModal;
fc_$('modalMask').addEventListener('click',e=>{if(e.target===fc_$('modalMask'))fc_closeModal()});
let fc_toastTimer;
function fc_toast(msg,isErr){const t=fc_$('toast');t.textContent=msg;t.className='fc-toast fc-show'+(isErr?' fc-err':'');clearTimeout(fc_toastTimer);fc_toastTimer=setTimeout(()=>t.classList.remove('fc-show'),2200)}
document.addEventListener('keydown',e=>{if(e.key==='Escape'){fc_closeModal();fc_closeDrawer();fc_$('manualMask').classList.remove('fc-show')}});

/* ---------- 实时数据 ---------- */
async function fc_loadData(){
  try{
    const ctl=new AbortController();setTimeout(()=>ctl.abort(),5000);
    const r=await fetch(fc_API_BASE,{signal:ctl.signal});
    const d=await r.json();
    const f=d.factors||d;
    fc_acct={demo:false,generated_at:d.generated_at||new Date().toLocaleString('zh-CN'),
      A:f.initial_capital,R:f.realized_pnl,U:f.unrealized_pnl,E:f.survival_equity,D:f.deployable_pool,H:f.high_water_mark,
      SR:f.survival_ratio,DD:f.high_water_drawdown,status:f.strategy_status,state:f.risk_state,M:f.risk_multiplier,
      quote_complete:f.quote_complete,hits:f.loss_boundary_hits,confirms:f.loss_boundary_confirmations,
      gross:f.gross_exposure,max_gross:f.max_gross_exposure,open_risk:f.open_risk,max_open_risk:f.max_open_risk,
      industry:f.industry_exposure||{},industry_limit:f.industry_limit,stocks:f.stock_count,max_stocks:f.max_stocks,
      cash:f.cash,cash_buffer:f.cash_buffer};
    fc_$('srcBadge').className='fc-src-badge fc-src-live';fc_$('srcBadge').textContent='实时 · '+fc_acct.generated_at.slice(-5);
  }catch(e){
    fc_acct={...fc_DEMO};fc_$('srcBadge').className='fc-src-badge fc-src-demo';fc_$('srcBadge').textContent='演示数据';
  }
  if(fc_$('fcPage-overview').classList.contains('fc-active'))fc_renderOverview();
}

/* ---------- 启动 ---------- */
fc_go('overview');fc_loadData();setInterval(fc_loadData,60000);
}
