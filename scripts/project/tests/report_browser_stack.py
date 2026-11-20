"""Start the local mock demo with one explicit browser test profile."""

import argparse
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch


PROFILES = ('slow', 'summary-failure', 'findings-failure', 'extraction-failure', 'classifier-failure', 'uncertain')


def extraction_app():
    from notelens_extraction.main import create_app
    from notelens_extraction.providers import FakeProvider

    profile = os.environ['NOTELENS_REPORT_BROWSER_PROFILE']

    class SlowExtraction(FakeProvider):
        def generate(self, operation, request, instructions, *, repair):
            if operation == 'extract':
                time.sleep(3)
            return super().generate(operation, request, instructions, repair=repair)

    if profile == 'slow':
        return create_app(SlowExtraction())
    return create_app(FakeProvider(
        extraction_state='failed' if profile in ('findings-failure', 'extraction-failure') else 'completed',
        summary_failed=profile in ('summary-failure', 'extraction-failure'),
    ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', choices=PROFILES)
    profile = parser.parse_args().profile

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import start_mock

    owned_process = start_mock.owned_process

    def launch(command, *, env, **options):
        if 'notelens_extraction.main:app' in command and profile not in ('classifier-failure', 'uncertain'):
            command = [
                'report_browser_stack:extraction_app' if arg == 'notelens_extraction.main:app' else arg
                for arg in command
            ] + ['--factory', '--app-dir', str(Path(__file__).resolve().parent)]
            env = {**env, 'NOTELENS_REPORT_BROWSER_PROFILE': profile}
        if 'notelens_classifier.main:app' in command and profile == 'classifier-failure':
            env = {**env, 'NOTELENS_CLASSIFIER_MOCK_FAILURE': 'provider_unavailable'}
        if 'notelens_classifier.main:app' in command and profile == 'uncertain':
            env = {**env, 'NOTELENS_CLASSIFIER_MOCK_SCENARIO': 'uncertain'}
        return owned_process(command, env=env, **options)

    with patch.object(start_mock, 'owned_process', launch):
        return start_mock.main()


if __name__ == '__main__':
    sys.exit(main())
