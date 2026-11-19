"""Start and stop an owned loopback process; no provider or external service is called."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4

import pytest

from notelens_rag.contracts import Contracts
from notelens_rag.main import DEMO_QUESTION


@pytest.mark.parametrize(('mock_ready', 'readiness_status'), [(None, 200), ('false', 503)],
                         ids=['default-ready', 'configured-not-ready'])
def test_real_loopback_http_process_smoke(mock_ready, readiness_status):
    open_url = build_opener(ProxyHandler({})).open
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1',0))
        port=reservation.getsockname()[1]
    environment=os.environ.copy()
    environment.update(NOTELENS_RAG_MODE='mock',NOTELENS_RAG_MOCK_SCENARIO='sufficient')
    for name in ('OPENAI_API_KEY', 'NOTELENS_RAG_SERVICE_TOKEN', 'NOTELENS_RAG_MOCK_READY',
                 'NOTELENS_RAG_CORPUS_MANIFEST', 'NOTELENS_RAG_REPOSITORY_ROOT', 'NOTELENS_RAG_EXPECTED_CORPUS_VERSION'):
        environment.pop(name, None)
    if mock_ready is not None:
        environment['NOTELENS_RAG_MOCK_READY'] = mock_ready
    process=subprocess.Popen([sys.executable,'-m','uvicorn','notelens_rag.main:app',
                              '--host','127.0.0.1','--port',str(port),'--no-proxy-headers',
                              '--no-access-log','--log-level','warning'],
                             cwd=Path(__file__).resolve().parents[1],env=environment,
                             stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    origin=f'http://127.0.0.1:{port}'
    try:
        # These bounds belong to this smoke harness, not an approved application SLO.
        deadline=time.monotonic()+15
        while True:
            if process.poll() is not None: raise AssertionError('Owned smoke server exited before readiness.')
            try:
                with open_url(origin+'/health/live',timeout=1) as response:
                    liveness = Contracts().validate('LivenessResult', json.load(response))
                    assert response.status == 200
                    assert liveness['status'] == 'alive' and liveness['mode'] == 'mock'
                    break
            except URLError:
                if time.monotonic()>=deadline: raise AssertionError('Owned smoke server did not become ready.')
                time.sleep(.1)
        try:
            readiness_response = open_url(origin + '/health/ready', timeout=3)
        except HTTPError as failure:
            readiness_response = failure
        with readiness_response as response:
            assert response.status == readiness_status
            readiness = Contracts().validate('HealthResult', json.load(response))
            assert readiness['mode'] == 'mock'
            assert readiness['status'] == ('ok' if readiness_status == 200 else 'not_ready')
            assert readiness['reason'] == (None if readiness_status == 200 else
                                           'Mock readiness is disabled by server configuration.')
        for path in ['/v1/retrieve','/v1/literature-answer']:
            identifier=str(uuid4())
            request=Request(origin+path,data=json.dumps({'schema_version':'1.0.0','question':DEMO_QUESTION}).encode(),
                            headers={'Content-Type':'application/json','X-Request-ID':identifier})
            with open_url(request,timeout=3) as response:
                assert response.headers['X-Request-ID']==identifier
                assert json.load(response)['mode']=='mock'
        request=Request(origin+'/v1/retrieve',data=b'{}',headers={'Content-Type':'application/json'})
        try: open_url(request,timeout=3)
        except HTTPError as error:
            assert error.code==400
            assert json.load(error)['error']['code']=='validation_failure'
        else: raise AssertionError('Missing correlation ID was accepted.')
    finally:
        process.terminate()
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        if process.stderr: process.stderr.close()
