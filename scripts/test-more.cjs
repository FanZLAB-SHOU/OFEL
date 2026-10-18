// Busuanzi visit model: nightly snapshots (00:00 Beijing time) plus the live running total.
const assert=require('node:assert/strict'),M=require('../assets/scripts/more-model.js');
assert.equal(M.parseLive('1,234'),1234);assert.equal(M.parseLive(' 0 '),0);
for(const text of [null,undefined,'','—','12a','-3','1.5'])assert.equal(M.parseLive(text),null);
assert.deepEqual(M.reelDigits(3),[0,0,0,0,0,3]);assert.deepEqual(M.reelDigits(1000000),[1,0,0,0,0,0,0]);assert.equal(M.reelDigits(null),null);
// 23:30 UTC on 1 January is already 2 January in Beijing.
assert.equal(M.beijingDate(Date.UTC(2026,0,1,23,30)),'2026-01-02');assert.equal(M.shift('2026-03-01',-1),'2026-02-28');
const source={},origin='https://fanzhang-lab-shou.github.io',event={origin,source,data:{type:'ofel-world-height',height:1234.5}};
assert.equal(M.frameHeight(event,origin,source),1235);
for(const other of [{...event,origin:'https://example.com'},{...event,source:{}},{...event,data:{type:'other',height:1200}},{...event,data:{type:'ofel-world-height',height:Infinity}},{...event,data:{type:'ofel-world-height',height:2}}])assert.equal(M.frameHeight(other,origin,source),null);
// Snapshots: each reading is one Busuanzi visit itself, tracked by the cumulative `reads`.
const snap=(date,site_pv,reads)=>({date,site_pv,site_uv:Math.floor(site_pv/3),reads});
const store={snapshots:[snap('2026-10-20',100,1),snap('2026-10-21',131,2),snap('2026-10-23',160,3),snap('2026-10-24',175,4),{date:'bad',site_pv:1,site_uv:1,reads:1}]};
const now=Date.UTC(2026,9,24,4); // 12:00 on 24 October in Beijing
const s=M.series(store,190,now);
assert.equal(s.today,'2026-10-24');assert.equal(s.days.length,14);assert.equal(s.days[13],'2026-10-24');assert.equal(s.days[0],'2026-10-11');
const at=day=>s.values[s.days.indexOf(day)];
assert.equal(at('2026-10-20'),30,'131-100 minus the next morning reading');
assert.equal(at('2026-10-21'),null,'no snapshot for 22 October, so 21 October is unknown');
assert.equal(at('2026-10-22'),null);assert.equal(at('2026-10-23'),14);
assert.equal(s.todayVisits,15,'live 190 minus the 00:00 total 175');
assert.equal(s.week,(190-4)-(100-1),'past 7 days counts from the first snapshot inside the window');
assert.equal(at('2026-10-11'),null);assert.equal(s.tracking,'2026-10-20');
// Without a live total (Busuanzi unreachable) past days still show; today and the week do not.
const offline=M.series(store,null,now);assert.equal(offline.todayVisits,null);assert.equal(offline.week,null);assert.equal(offline.values[s.days.indexOf('2026-10-20')],30);
// A stale live total below the last snapshot is ignored rather than producing negative visits.
assert.equal(M.series(store,170,now).todayVisits,null);
// Before tonight's snapshot exists, today is not guessed.
assert.equal(M.series({snapshots:[snap('2026-10-23',160,1)]},170,now).todayVisits,null);
// No snapshots yet.
const empty=M.series({snapshots:[]},50,now);assert.equal(empty.tracking,null);assert.ok(empty.values.every(v=>v===null));assert.equal(empty.week,null);
assert.equal(M.series(null,50,now).tracking,null);
console.log('Passed Beijing dates, snapshot self-count correction, gaps, today, past 7 days, stale/offline live totals, digit targets and secure frame sizing.');
