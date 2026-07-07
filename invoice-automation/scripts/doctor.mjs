import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

function checkCommand(cmd, args = ['--version']) {
  const result = spawnSync(cmd, args, { encoding: 'utf8' });
  return {
    ok: result.status === 0,
    output: (result.stdout || result.stderr || '').trim().split('\n')[0] || '',
  };
}

const checks = [
  ['node', checkCommand('node')],
  ['npm', checkCommand('npm')],
  ['rclone', checkCommand('rclone')],
];

for (const [name, result] of checks) {
  console.log(`${result.ok ? '✓' : '✗'} ${name}${result.output ? ` — ${result.output}` : ''}`);
}

console.log(`${existsSync('node_modules/playwright') ? '✓' : '✗'} node_modules/playwright`);
console.log(`${existsSync('config.yaml') ? '✓' : '✗'} config.yaml`);
console.log(`${existsSync('browser-profiles/openai') ? '✓' : '✗'} browser profile: openai`);
console.log(`${existsSync('browser-profiles/telekom') ? '✓' : '✗'} browser profile: telekom`);
