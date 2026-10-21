import { spawn } from 'node:child_process';

const procs = [];

function run(name, cmd, args, cwd) {
  const p = spawn(cmd, args, { cwd, shell: true, stdio: 'inherit' });
  p.on('close', (code) => {
    if (code !== 0) process.exit(code);
  });
  procs.push(p);
}

process.on('SIGINT', () => {
  procs.forEach((p) => p.kill('SIGINT'));
  process.exit(0);
});

process.on('SIGTERM', () => {
  procs.forEach((p) => p.kill('SIGTERM'));
  process.exit(0);
});

run('api', 'python', ['-m', 'uvicorn', 'main:app', '--reload', '--port', '8000'], 'apps/api');
run('web', 'pnpm', ['dev'], 'apps/web');
