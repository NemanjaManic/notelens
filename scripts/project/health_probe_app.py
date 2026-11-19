"""B-owned, synthetic-only bootstrap for D's confirmed application factory."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / '.cache/review/f011-health'
SCENARIOS = ('timeout', 'rate_limit', 'provider_unavailable')


class InertFailureProvider:
    mode = 'mock'

    def __init__(self, scenario, trace, run):
        if scenario not in SCENARIOS:
            raise ValueError('Unknown review failure scenario')
        run, trace = Path(run).resolve(), Path(trace).resolve()
        if (run.parent != CACHE.resolve() or not run.name.startswith('run-') or not run.is_dir() or
                trace.parent != run or trace.name != f'failure-{scenario}.factory.jsonl'):
            raise ValueError('Provider trace must belong to the active F-011 run')
        self.scenario, self.trace = scenario, trace

    def generate(self, operation, request, instructions, *, repair):
        # Persist only safe invocation metadata; request/instructions stay in memory.
        with self.trace.open('a', encoding='utf-8') as output:
            output.write(json.dumps({'scenario': self.scenario, 'operation': operation, 'repair': repair}) + '\n')
        private_detail = 'synthetic-private-provider-detail ' + request['document']['text']
        if self.scenario == 'timeout':
            raise TimeoutError(private_detail)
        if self.scenario == 'provider_unavailable':
            raise ConnectionError(private_detail)
        from notelens_extraction.errors import ServiceError
        raise ServiceError(429, 'rate_limit', 'The synthetic generation rate limit was reached.', True)


def create_app():
    token = os.environ.get('NOTELENS_SERVICE_TOKEN')
    if not token:
        raise ValueError('The review factory requires a synthetic service token')
    provider = InertFailureProvider(os.environ['NOTELENS_REVIEW_FAILURE'],
                                   os.environ['NOTELENS_REVIEW_FACTORY_TRACE'],
                                   os.environ['NOTELENS_REVIEW_FACTORY_RUN'])
    from notelens_extraction.main import create_app as extraction_app
    return extraction_app(provider=provider, token=token)
