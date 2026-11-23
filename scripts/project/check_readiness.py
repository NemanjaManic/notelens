"""Check the production web build and all three mock services on Windows loopback."""

from http.client import HTTPException
import json
import sys

from smoke_mock import read_page, require, verify_shutdown
from start_mock import MockStartupError, SERVICES, get, start_stack


SERVICE_PROBES = (('/health/live', 'alive'), ('/health/ready', 'ok'))


def check_stack(stack):
    status, body = get(stack.web_port, '/demo/health')
    require(status == 200, 'web /demo/health returns HTTP 200')
    web = json.loads(body)
    require(isinstance(web, dict) and web.get('mode') == 'mock', 'web health identifies mock mode')
    require(read_page(stack, '/demo').contains('Mock mode'), 'the web workspace displays mock mode')
    print('PASS: web health and demo workspace returned HTTP 200 in mock mode.', flush=True)

    auth = {'Authorization': f'Bearer {stack.service_token}'}
    for name in SERVICES:
        port = stack.ports[name]
        for endpoint, expected_status in SERVICE_PROBES:
            label = f'{name} {endpoint}'
            status, _ = get(port, endpoint)
            require(status == 401, f'{label} requires service authentication')
            status, body = get(port, endpoint, auth)
            require(status == 200, f'{label} returns authenticated HTTP 200')
            record = json.loads(body)
            require(isinstance(record, dict) and
                    (record.get('service'), record.get('mode'), record.get('status')) ==
                    (name, 'mock', expected_status), f'{label} reports the expected mock service and status')
        print(f'PASS: {name} liveness and readiness returned authenticated HTTP 200 and '
              'rejected unauthenticated requests with HTTP 401.', flush=True)


def main():
    stack = None
    try:
        try:
            with start_stack() as stack:
                check_stack(stack)
        finally:
            if stack is not None:
                verify_shutdown(stack)
    except MockStartupError as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    except (OSError, ValueError, HTTPException, RuntimeError):
        print('FAIL: could not start, probe, or stop the local mock stack.', file=sys.stderr)
        return 1

    print('PASS: key-free readiness for the web app and all three services. All four listeners stopped.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
