"""Serve Milica's pinned saved D-005 responses over the reviewed service."""

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import BadZipFile, ZipFile


SERVICE_SHA = 'c7d0797a86061c643b0f23e6d56f8caa9e7a6813'
BUNDLE_SHA = 'e3ae6b924d80d122afa3b88fa23830bd220a9dc81bb66cfabcdacfe20182ecaf'
MODEL = 'gpt-6-luna'
OUTPUTS = {'extract': (5, 'extract.validated.json'), 'answer': (6, 'answer.validated.json')}


class ReplaySetupError(RuntimeError):
    pass


def digest(data):
    return sha256(data).hexdigest()


@dataclass(frozen=True)
class D005Replay:
    checkout: Path
    bundle: Path

    @classmethod
    def from_paths(cls, checkout, bundle):
        replay = cls(Path(checkout).resolve(), Path(bundle).resolve())

        def git(*args):
            return subprocess.run(
                ['git', '-C', str(replay.checkout), *args], check=True,
                capture_output=True, text=True, timeout=10,
            ).stdout.strip()

        try:
            if git('rev-parse', 'HEAD') != SERVICE_SHA or git(
                'status', '--porcelain=v1', '--untracked-files=all', '--',
                'services/extraction', 'contracts/generated/python', 'contracts/v1',
            ):
                raise ReplaySetupError('Use the clean checkout at the reviewed D-005 service SHA.')
            if digest(replay.bundle.read_bytes()) != BUNDLE_SHA:
                raise ReplaySetupError('The private D-005 handoff bundle checksum differs.')
            with ZipFile(replay.bundle) as archive:
                receipt = json.loads(archive.read('reviewed-receipt.json'))
            if receipt['service_sha'] != SERVICE_SHA or any(
                digest((replay.checkout / name).read_bytes()) != checksum
                for name, checksum in receipt['artifact_pins'].items()
            ):
                raise ReplaySetupError('The reviewed D-005 service artifact pins differ.')
        except (OSError, ValueError, KeyError, BadZipFile, subprocess.SubprocessError):
            raise ReplaySetupError('Could not verify the D-005 service checkout and private bundle.') from None
        return replay

    def command(self, interpreter, port):
        return [str(interpreter), '-B', str(Path(__file__).resolve()),
                str(self.checkout), str(self.bundle), str(port)]


def bind_document_id(value, original_id, replay_id):
    if isinstance(value, list):
        for item in value:
            bind_document_id(item, original_id, replay_id)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key == 'doc_id':
                if item != original_id:
                    raise ReplaySetupError('The saved response has an unexpected document ID.')
                value[key] = replay_id
            else:
                bind_document_id(item, original_id, replay_id)


def serve(checkout, bundle, port):
    if os.environ.get('NOTELENS_MODE') != 'mock' or not getattr(sys.modules.get('sitecustomize'), 'GUARD_ACTIVE', False):
        raise ReplaySetupError('Start the D-005 replay with the key-free loopback launcher.')
    if digest(bundle.read_bytes()) != BUNDLE_SHA:
        raise ReplaySetupError('The private D-005 handoff bundle checksum differs.')
    # Use the reviewed source and generated binding from the checkout, with its locked dependencies.
    sys.path[:0] = [str(checkout / 'services/extraction/src'), str(checkout / 'contracts/generated/python/src')]
    import uvicorn
    from notelens_extraction.demo import request as demo_request
    from notelens_extraction.errors import ServiceError
    from notelens_extraction.main import create_app
    from notelens_extraction.openai_trial import DEMO_QUESTION, OpenAIResponsesProvider, completion_text

    with ZipFile(bundle) as archive:
        responses = {op: json.loads(archive.read(f'call-{number}.response.json'))
                     for op, (number, _) in OUTPUTS.items()}
        validated = {op: json.loads(archive.read(name)) for op, (_, name) in OUTPUTS.items()}
    if any(json.loads(completion_text(response)) != validated[op] for op, response in responses.items()):
        raise ReplaySetupError('The saved responses differ from the reviewed records.')
    pinned = demo_request()['document']

    class ReplayProvider:
        mode = 'live'
        configured = True
        provider_name = 'openai'
        model = MODEL

        def generate(self, operation, request, instructions, *, repair):
            document = request['document']
            if (repair or operation not in responses or document['source']['kind'] != 'synthetic_text' or
                    document['text'] != pinned['text'] or document['text_sha256'] != pinned['text_sha256'] or
                    (operation == 'answer' and request['question'] != DEMO_QUESTION)):
                raise ServiceError(503, 'configuration_required', 'No saved D-005 response matches this request.')
            replay = responses[operation]
            if document['doc_id'] != pinned['doc_id']:
                # Only the app-generated ID changes. The text, digest, claims and offsets stay pinned.
                replay = deepcopy(replay)
                record = deepcopy(validated[operation])
                bind_document_id(record, pinned['doc_id'], document['doc_id'])
                output, = (node for item in replay['output'] if item['type'] == 'message'
                           for node in item['content'] if node['type'] == 'output_text')
                output['text'] = json.dumps(record, ensure_ascii=False)
            provider = OpenAIResponsesProvider(lambda _: replay, model=MODEL, max_output_tokens=2048,
                                               input_format='messages')
            return provider.generate(operation, request, instructions, repair=repair)

    app = create_app(ReplayProvider(), token=os.environ['NOTELENS_SERVICE_TOKEN'])
    uvicorn.run(app, host='127.0.0.1', port=port, access_log=False, log_level='error', proxy_headers=False)


if __name__ == '__main__':
    checkout, bundle, port = sys.argv[1:]
    serve(Path(checkout), Path(bundle), int(port))
