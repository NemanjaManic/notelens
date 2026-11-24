"""Score canonical text with a trusted, explicitly selected development artifact."""

from dataclasses import dataclass, field
from hashlib import sha256
from importlib.metadata import version
from io import BytesIO
import json
from math import isfinite
from pathlib import Path
import re

from notelens_contracts.v1 import ClassificationResult, PreparedDocument, validate_record


LABELS = ("Cardiovascular / Pulmonary", "Orthopedic", "Gastroenterology", "Neurology", "Urology")
MODEL_FILE = "model.joblib"
MANIFEST_FILE = "model-manifest.json"
LEXICAL_METHODS = ("single_word", "two_words", "word_or_phrase")

SECTION_BOUNDARY = re.compile(r"\n+|;\s*|(?<=[.!?])\s+")
CLAUSE_BOUNDARY = re.compile(
    r",\s*(?=(?:one|the other)\b)|\s+(?:and|but|while|plus|as well as)\s+",
    re.IGNORECASE,
)
NEGATED_SECTION = re.compile(
    r"^(?:(?:the patient\s+)?(?:denies|denied)|no|without|negative for|"
    r"(?:the report|the note)\s+(?:mentions|notes|documents)\s+no)\b",
    re.IGNORECASE,
)


def score_rows(estimator, features):
    """Yield probabilities in frozen contract order for either candidate estimator."""
    classes = tuple(estimator.classes_.tolist())
    if classes == tuple(range(len(LABELS))):
        classes = LABELS
    if set(classes) != set(LABELS) or len(classes) != len(LABELS):
        raise ValueError("Unexpected classifier labels.")
    order = [classes.index(label) for label in LABELS]
    for row in estimator.predict_proba(features):
        if len(row) != len(order):
            raise ValueError("Unexpected classifier score width.")
        scores = tuple(float(row[index]) for index in order)
        if not all(isfinite(score) and 0 <= score <= 1 for score in scores):
            raise ValueError("Invalid classifier probabilities.")
        yield scores


def accepted_category(scores, has_features, threshold, minimum_margin=0.0):
    top = max(scores)
    if not has_features or top < threshold or scores.count(top) != 1:
        return None
    if top - sorted(scores)[-2] < minimum_margin:
        return None
    return LABELS[scores.index(top)]


def independent_sections(text):
    sections = [part.strip() for part in SECTION_BOUNDARY.split(text)]
    clauses = [clause.strip() for part in sections if not NEGATED_SECTION.match(part)
               for clause in CLAUSE_BOUNDARY.split(part)]
    clauses = [part for part in clauses if part and not NEGATED_SECTION.match(part)]
    return clauses if len(clauses) > 1 else []


@dataclass(frozen=True)
class WordEvidenceIndex:
    words: dict[str, dict[int, float]]
    phrases: dict[str, dict[int, float]]


def word_evidence_index(pipeline):
    """Index the positive winning class coefficient gap for fitted word features."""
    vectorizer = pipeline.named_steps["tfidf"]
    if hasattr(vectorizer, "transformer_list"):
        name, vectorizer = vectorizer.transformer_list[0]
        if name != "word":
            raise ValueError("Ambiguity policy requires word features first.")
    estimator = pipeline.named_steps["classifier"]
    if set(estimator.classes_) != set(LABELS) or not hasattr(estimator, "coef_"):
        raise ValueError("Ambiguity policy requires a fitted linear specialty classifier.")
    lookup = WordEvidenceIndex(words={label: {} for label in LABELS}, phrases={label: {} for label in LABELS})
    for term, column in vectorizer.vocabulary_.items():
        coefficients = zip(estimator.coef_[:, column], estimator.classes_, strict=True)
        top, second, *_ = sorted(coefficients, reverse=True)
        if top[0] > 0 and top[0] > second[0]:
            targets = lookup.phrases if " " in term else lookup.words
            targets[top[1]][column] = float(top[0] - second[0])
    return lookup


def word_evidence(features, category, lookup):
    strengths = lookup.words[category]
    return max((strengths.get(index, 0.0) for index in features.indices), default=0.0)


@dataclass(frozen=True)
class LexicalEvidence:
    single_word: float = 0.0
    two_words: float = 0.0
    word_or_phrase: float = 0.0


def lexical_evidence(features, category, lookup):
    words = lookup.words[category]
    phrases = lookup.phrases[category]
    strengths = sorted((words[index] for index in set(features.indices) if index in words), reverse=True)
    strongest_word = strengths[0] if strengths else 0.0
    two_words = sum(strengths[:2])
    strongest_phrase = max((phrases.get(index, 0.0) for index in features.indices), default=0.0)
    return LexicalEvidence(strongest_word, two_words, max(two_words, strongest_word + strongest_phrase))


@dataclass(frozen=True)
class SectionPrediction:
    scores: tuple[float, ...]
    word_evidence: float
    word_count: int


def score_sections(pipeline, text, lookup):
    sections = independent_sections(text)
    if not sections:
        return []
    features = pipeline.named_steps["tfidf"].transform(sections).tocsr()
    return [
        SectionPrediction(scores, word_evidence(features[index], LABELS[scores.index(max(scores))], lookup),
                          len(sections[index].split()))
        for index, scores in enumerate(score_rows(pipeline.named_steps["classifier"], features))
    ]


@dataclass(frozen=True)
class AmbiguityPolicy:
    minimum_word_evidence: float
    segment_threshold: float
    segment_margin: float
    competing_score_ratio: float
    minimum_section_share: float
    document_evidence_kind: str = "single_word"
    minimum_document_evidence: float | None = None

    def __post_init__(self):
        values = (self.minimum_word_evidence, self.segment_threshold, self.segment_margin,
                  self.competing_score_ratio, self.minimum_section_share)
        if (not all(type(value) in (int, float) and isfinite(value) for value in values)
                or self.minimum_word_evidence <= 0 or not 0 < self.segment_threshold <= 1
                or not 0 <= self.segment_margin <= 1 or not 0 < self.competing_score_ratio <= 1
                or not 0 < self.minimum_section_share <= 0.5):
            raise ValueError("Invalid ambiguity policy.")
        minimum = self.minimum_document_evidence
        if (self.document_evidence_kind not in LEXICAL_METHODS
                or (minimum is not None and (type(minimum) not in (int, float) or not isfinite(minimum) or minimum <= 0))):
            raise ValueError("Invalid document evidence policy.")

    @property
    def document_minimum(self):
        return self.minimum_word_evidence if self.minimum_document_evidence is None else self.minimum_document_evidence

    def abstention_reason(self, evidence, scores, sections, document_words):
        if evidence < self.document_minimum:
            return "limited_word_evidence"
        minimum_competing_score = self.competing_score_ratio * max(scores)
        minimum_section_words = document_words * self.minimum_section_share
        evidence_words = {}
        for section in sections:
            if section.word_evidence < self.minimum_word_evidence:
                continue
            category = accepted_category(section.scores, True, self.segment_threshold, self.segment_margin)
            if category and scores[LABELS.index(category)] >= minimum_competing_score:
                evidence_words[category] = evidence_words.get(category, 0) + section.word_count
        if sum(words >= minimum_section_words for words in evidence_words.values()) > 1:
            return "conflicting_sections"
        return None


@dataclass(frozen=True)
class DevelopmentModel:
    pipeline: object
    model_version: str
    threshold: float
    minimum_margin: float = 0.0
    ambiguity_policy: AmbiguityPolicy | None = None
    _word_evidence: WordEvidenceIndex | None = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        if self.ambiguity_policy:
            object.__setattr__(self, "_word_evidence", word_evidence_index(self.pipeline))

    def classify(self, document: PreparedDocument) -> ClassificationResult:
        text = document["text"]
        features = self.pipeline.named_steps["tfidf"].transform([text]).tocsr()
        scores = next(score_rows(self.pipeline.named_steps["classifier"], features))
        category = accepted_category(scores, bool(features.nnz), self.threshold, self.minimum_margin)
        confidence_note = ("Development-only model. Scores are uncalibrated specialty probabilities. "
                           "They do not establish a diagnosis or whether a document is in scope.")
        if category and self.ambiguity_policy:
            evidence_kind = self.ambiguity_policy.document_evidence_kind
            if evidence_kind == "single_word":
                strength = word_evidence(features, category, self._word_evidence)
            else:
                strength = getattr(lexical_evidence(features, category, self._word_evidence), evidence_kind)
            sections = []
            if strength >= self.ambiguity_policy.document_minimum:
                sections = score_sections(self.pipeline, text, self._word_evidence)
            reason = self.ambiguity_policy.abstention_reason(strength, scores, sections, len(text.split()))
            if reason:
                category = None
                explanation = {
                    "limited_word_evidence": " The text has limited specialty-specific word evidence.",
                    "conflicting_sections": " Different parts of the text support different specialties.",
                }
                confidence_note += explanation[reason]
        return {
            "schema_version": "1.0.0",
            "mode": "live",
            "doc_id": document["doc_id"],
            "text_sha256": document["text_sha256"],
            "status": "supported" if category else "uncertain",
            "category": category,
            "scores": [{"category": label, "score": score} for label, score in zip(LABELS, scores, strict=True)],
            "score_kind": "probability",
            "confidence_note": confidence_note,
            "model_version": self.model_version,
            "classification_execution": "performed",
            "scope_policy_version": None,
            "scope_reason": None,
        }


def load_model(directory: Path, manifest_sha256: str, *, stage="development") -> DevelopmentModel:
    """Load only a locally produced artifact pinned by a trusted operator."""
    raw_manifest = (directory / MANIFEST_FILE).read_bytes()
    if sha256(raw_manifest).hexdigest() != manifest_sha256:
        raise ValueError("Development model manifest checksum mismatch.")
    manifest = json.loads(raw_manifest)
    threshold = manifest["threshold"]
    minimum_margin = manifest.get("minimum_margin", 0.0)
    model_version = manifest["model_version"]
    estimator = manifest["estimator"]
    policy = AmbiguityPolicy(**manifest["ambiguity_policy"]) if "ambiguity_policy" in manifest else None
    if (manifest["stage"] != stage or tuple(manifest["labels"]) != LABELS
            or type(threshold) not in (int, float) or not 0 < threshold <= 1
            or type(minimum_margin) not in (int, float) or not 0 <= minimum_margin <= 1
            or not isinstance(model_version, str) or not model_version.strip()
            or estimator not in ("logistic_regression", "xgboost")):
        raise ValueError("Invalid development model manifest.")
    required_packages = {"scikit-learn", "numpy", "scipy", "joblib"}
    if estimator == "xgboost":
        required_packages.add("xgboost-cpu")
    packages = manifest["packages"]
    if required_packages != set(packages) or any(version(name) != packages[name] for name in required_packages):
        raise ValueError("Development model dependency versions differ.")
    raw_model = (directory / MODEL_FILE).read_bytes()
    if sha256(raw_model).hexdigest() != manifest["artifact_sha256"]:
        raise ValueError("Development model checksum mismatch.")

    # Joblib is only safe for trusted artifacts. Verify the pinned bytes before loading.
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import FeatureUnion, Pipeline

    pipeline = joblib.load(BytesIO(raw_model))
    if not isinstance(pipeline, Pipeline) or tuple(pipeline.named_steps) != ("tfidf", "classifier"):
        raise ValueError("The artifact must contain the fitted TF-IDF classifier pipeline.")
    vectorizer, classifier = (pipeline.named_steps[name] for name in ("tfidf", "classifier"))
    if not isinstance(vectorizer, (TfidfVectorizer, FeatureUnion)):
        raise ValueError("The artifact uses unexpected preprocessing.")
    if estimator == "logistic_regression":
        expected_type, expected_labels = LogisticRegression, set(LABELS)
    else:
        from xgboost import XGBClassifier

        expected_type, expected_labels = XGBClassifier, set(range(len(LABELS)))
    if not isinstance(classifier, expected_type) or set(classifier.classes_) != expected_labels:
        raise ValueError("The fitted classifier or label mapping differs from its manifest.")

    model = DevelopmentModel(pipeline, model_version, threshold, minimum_margin, policy)
    text = "Synthetic startup check."
    probe: PreparedDocument = {
        "schema_version": "1.0.0", "doc_id": "synthetic-classifier-startup", "text": text,
        "text_sha256": sha256(text.encode("utf-8")).hexdigest(), "canonicalization_version": "nfc-lf-v1",
        "source": {"kind": "synthetic_text"}, "language": "en",
        "language_validation": {"outcome": "accepted", "language": "en",
                                "policy_version": "synthetic-startup-probe-v1", "reason": None},
    }
    validate_record("ClassificationResult", model.classify(probe), document=probe)
    return model
