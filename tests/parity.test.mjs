// Browser engine parity: site/js/plumes2.js must reproduce plumes2py.
// Run: node tests/parity.test.mjs
import { createRequire } from "module";
import fs from "fs";
const require = createRequire(import.meta.url);
const P = require("../site/js/plumes2.js");
const fx = JSON.parse(fs.readFileSync(new URL("./fixtures/parity.json", import.meta.url)));
let fails = 0, checks = 0;
const REL = 1e-7;
function close(a, b, path) {
  checks++;
  if (a === null || b === null || a === undefined || b === undefined) {
    if ((a ?? null) !== (b ?? null)) { fails++; console.log(`  ${path}: ${a} vs ${b}`); }
    return;
  }
  if (typeof b === "number") {
    if (!isFinite(b) && !isFinite(a)) return;
    const err = Math.abs(a - b) / Math.max(1e-9, Math.abs(b));
    if (err > REL && Math.abs(a - b) > 1e-9) { fails++; console.log(`  ${path}: js ${a} py ${b} (rel ${err.toExponential(2)})`); }
  } else if (typeof b === "string" || typeof b === "boolean") {
    if (a !== b) { fails++; console.log(`  ${path}: js ${JSON.stringify(a)} py ${JSON.stringify(b)}`); }
  } else if (Array.isArray(b)) {
    if (!Array.isArray(a) || a.length !== b.length) { fails++; console.log(`  ${path}: length ${a && a.length} vs ${b.length}`); return; }
    b.forEach((v, i) => close(a[i], v, `${path}[${i}]`));
  } else {
    Object.keys(b).forEach(k => close(a ? a[k] : undefined, b[k], `${path}.${k}`));
  }
}
for (const f of fx) {
  const before = fails;
  const res = P.run(f.scenario, f.options);
  const m = res.metrics, ff = res.farfield;
  const got = {
    end: res.nearfield.end, termination: res.nearfield.termination, n_steps: res.nearfield.steps.length,
    events: res.nearfield.events.map(e => [e.event, e.step]),
    step10: res.nearfield.steps[Math.min(10, res.nearfield.steps.length - 1)],
    farfield_rows: ff ? [ff.rows[0], ff.rows[Math.floor(ff.rows.length / 2)], ff.rows[ff.rows.length - 1]] : null,
    w0: ff ? ff.w0 : null, thermal: m.thermal, reach: m.thermal.threshold_reach, exposure: m.exposure,
    oxygen: m.oxygen, heat: m.heat, flow_class: m.flow_class, merging: m.merging || null, caveats: res.caveats,
    verdict: res.compliance ? res.compliance.verdict : null,
  };
  const exp = { ...f.expect };
  if (exp.merging) delete exp.merging.note;
  if (exp.heat) delete exp.heat.note;
  if (exp.exposure) delete exp.exposure.note;
  close(got, exp, f.name);
  console.log(`${fails === before ? "PASS" : "FAIL"} ${f.name}`);
}
console.log(`${checks} comparisons, ${fails} failures`);
process.exit(fails ? 1 : 0);
