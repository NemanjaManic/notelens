"""Check the built local shell without launching Python services or a browser."""

from pathlib import Path
import os
import re
import shutil
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[3]


def check(mode, expected_status):
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    environment = {**os.environ, 'NOTELENS_MODE': mode, 'NEXT_TELEMETRY_DISABLED': '1'}
    command = [shutil.which('node'), str(ROOT / 'node_modules/next/dist/bin/next'),
               'start', str(ROOT / 'apps/web'), '--hostname', '127.0.0.1', '--port', str(port)]
    process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    try:
        origin = f'http://127.0.0.1:{port}'
        deadline = time.monotonic() + 30
        while True:
            if process.poll() is not None:
                raise RuntimeError('Owned web process exited before verification')
            try:
                response = urlopen(origin, timeout=3)
            except HTTPError as error:
                response = error
            except (URLError, TimeoutError):
                if time.monotonic() >= deadline:
                    raise RuntimeError('Local web startup exceeded the verification deadline') from None
                time.sleep(.2)
                continue
            break
        with response:
            assert response.status == expected_status, f'Unexpected HTTP status in {mode} mode'
            html = response.read().decode('utf-8')
        if mode == 'mock':
            for label in ('<html lang="en"', 'Mock mode', 'Educational demonstration',
                          'does not replace a doctor', 'Do not upload real personal medical reports',
                          'Web workspace ready'):
                assert label in html, 'Missing required shell label'
            assert '<form' not in html and '<input' not in html, 'Submission controls are out of scope'
            assets = set(re.findall(r'(?:src|href)="(/_next/[^"?]+)', html))
            assert assets, 'No built assets found'
            for asset in assets:
                with urlopen(origin + asset, timeout=5) as result:
                    assert result.status == 200, 'Built asset unavailable'
        print(f'PASS: local production shell mode={mode}, HTTP {expected_status}')
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == '__main__':
    check('mock', 200)
    check('live', 500)
