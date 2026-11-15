"""Canonical v1 validation, preserving the accepted revision-3 semantics."""

from pathlib import Path
from referencing import Registry, Resource

from check_contracts import ROOT, CheckError, read_json, no_remote_resource
from check_candidate import CandidateContracts


class FrozenContracts(CandidateContracts):
    def __init__(self, root: Path = ROOT):
        self.root = Path(root).resolve()
        self.directory = self.root / 'contracts/v1'
        self.schema = read_json(self.directory / 'schema.json')
        self.api = read_json(self.directory / 'openapi.json')
        self.schema_id = self.schema['$id']
        if self.schema_id != 'urn:notelens:contracts:v1':
            raise CheckError('SPECIFICATION: expected canonical v1 identifier')
        self.check_schema(self.schema)
        self.check_refs(self.schema, self.directory / 'schema.json')
        self.check_openapi(self.api)
        self.registry = Registry(retrieve=no_remote_resource).with_resource(
            self.schema_id, Resource.from_contents(self.schema))
