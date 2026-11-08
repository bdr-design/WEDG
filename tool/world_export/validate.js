const v = require('gltf-validator'); const fs = require('fs');
(async () => {
  for (const f of process.argv.slice(2)) {
    const r = await v.validateBytes(new Uint8Array(fs.readFileSync(f)), { maxIssues: 50 });
    const i = r.issues;
    console.log(f.split('/').pop(), 'errors', i.numErrors, 'warnings', i.numWarnings, 'infos', i.numInfos, 'hints', i.numHints);
    for (const m of i.messages.filter((m) => m.severity <= 1).slice(0, 12)) console.log('  ', m.severity, m.code, m.message, m.pointer);
  }
})();
