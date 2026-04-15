"""Unit tests for module DB dependency injection functions.

Tests exercise the success path (session_factory available → yield session,
close() called in finally) that was previously uncovered.  All tests use a
lightweight MagicMock request object — no real DB or HTTP server needed.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


def _make_mock_request(**state_attrs):
    """Build a minimal mock Request with app.state attrs as specified."""
    request = MagicMock()
    state = MagicMock(spec=[])  # blank state to avoid auto-attribute creation
    for attr, val in state_attrs.items():
        setattr(state, attr, val)
    request.app.state = state
    return request


def _run_generator_to_completion(gen):
    """Consume a generator: retrieve yielded value, then exhaust it."""
    yielded = next(gen)
    try:
        next(gen)
    except StopIteration:
        pass
    return yielded


# ---------------------------------------------------------------------------
# workflows/dependencies.py
# ---------------------------------------------------------------------------

class TestWorkflowsDependencies:
    def test_success_path_yields_session(self):
        from app.modules.workflows.dependencies import get_workflows_db

        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)
        request = _make_mock_request(workflows_session_factory=mock_factory)

        session = _run_generator_to_completion(get_workflows_db(request))
        assert session is mock_session

    def test_success_path_calls_close(self):
        from app.modules.workflows.dependencies import get_workflows_db

        mock_session = MagicMock()
        request = _make_mock_request(workflows_session_factory=MagicMock(return_value=mock_session))

        _run_generator_to_completion(get_workflows_db(request))
        mock_session.close.assert_called_once()

    def test_missing_factory_raises_503(self):
        from app.modules.workflows.dependencies import get_workflows_db
        from fastapi import HTTPException

        request = _make_mock_request()  # no factory attr
        with pytest.raises(HTTPException) as exc_info:
            _run_generator_to_completion(get_workflows_db(request))
        assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# enrollments/dependencies.py
# ---------------------------------------------------------------------------

class TestEnrollmentsDependencies:
    def test_success_via_enrollments_factory(self):
        from app.modules.enrollments.dependencies import get_enrollments_db

        mock_session = MagicMock()
        request = _make_mock_request(enrollments_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_enrollments_db(request))
        assert session is mock_session
        mock_session.close.assert_called_once()

    def test_success_via_profiles_fallback(self):
        from app.modules.enrollments.dependencies import get_enrollments_db

        mock_session = MagicMock()
        request = _make_mock_request(profiles_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_enrollments_db(request))
        assert session is mock_session

    def test_missing_factory_raises_503(self):
        from app.modules.enrollments.dependencies import get_enrollments_db
        from fastapi import HTTPException

        request = _make_mock_request()
        with pytest.raises(HTTPException) as exc_info:
            _run_generator_to_completion(get_enrollments_db(request))
        assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# scheduling/dependencies.py
# ---------------------------------------------------------------------------

class TestSchedulingDependencies:
    def test_success_via_scheduling_factory(self):
        from app.modules.scheduling.dependencies import get_scheduling_db

        mock_session = MagicMock()
        request = _make_mock_request(scheduling_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_scheduling_db(request))
        assert session is mock_session
        mock_session.close.assert_called_once()

    def test_success_via_profiles_fallback(self):
        from app.modules.scheduling.dependencies import get_scheduling_db

        mock_session = MagicMock()
        request = _make_mock_request(profiles_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_scheduling_db(request))
        assert session is mock_session

    def test_missing_factory_raises_503(self):
        from app.modules.scheduling.dependencies import get_scheduling_db
        from fastapi import HTTPException

        request = _make_mock_request()
        with pytest.raises(HTTPException) as exc_info:
            _run_generator_to_completion(get_scheduling_db(request))
        assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# transcripts/dependencies.py
# ---------------------------------------------------------------------------

class TestTranscriptsDependencies:
    def test_success_via_transcripts_factory(self):
        from app.modules.transcripts.dependencies import get_transcripts_db

        mock_session = MagicMock()
        request = _make_mock_request(transcripts_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_transcripts_db(request))
        assert session is mock_session
        mock_session.close.assert_called_once()

    def test_success_via_profiles_fallback(self):
        from app.modules.transcripts.dependencies import get_transcripts_db

        mock_session = MagicMock()
        request = _make_mock_request(profiles_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_transcripts_db(request))
        assert session is mock_session

    def test_missing_factory_raises_503(self):
        from app.modules.transcripts.dependencies import get_transcripts_db
        from fastapi import HTTPException

        request = _make_mock_request()
        with pytest.raises(HTTPException) as exc_info:
            _run_generator_to_completion(get_transcripts_db(request))
        assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# org_structure/dependencies.py
# ---------------------------------------------------------------------------

class TestOrgStructureDependencies:
    def test_success_via_org_structure_factory(self):
        from app.modules.org_structure.dependencies import get_org_structure_db

        mock_session = MagicMock()
        request = _make_mock_request(org_structure_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_org_structure_db(request))
        assert session is mock_session
        mock_session.close.assert_called_once()

    def test_success_via_admissions_fallback(self):
        from app.modules.org_structure.dependencies import get_org_structure_db

        mock_session = MagicMock()
        request = _make_mock_request(admissions_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_org_structure_db(request))
        assert session is mock_session

    def test_missing_factory_raises_503(self):
        from app.modules.org_structure.dependencies import get_org_structure_db
        from fastapi import HTTPException

        request = _make_mock_request()
        with pytest.raises(HTTPException) as exc_info:
            _run_generator_to_completion(get_org_structure_db(request))
        assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# degree_progress/dependencies.py
# ---------------------------------------------------------------------------

class TestDegreeProgressDependencies:
    def test_success_via_degree_progress_factory(self):
        from app.modules.degree_progress.dependencies import get_degree_progress_db

        mock_session = MagicMock()
        request = _make_mock_request(degree_progress_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_degree_progress_db(request))
        assert session is mock_session
        mock_session.close.assert_called_once()

    def test_success_via_profiles_fallback(self):
        from app.modules.degree_progress.dependencies import get_degree_progress_db

        mock_session = MagicMock()
        request = _make_mock_request(profiles_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_degree_progress_db(request))
        assert session is mock_session

    def test_missing_factory_raises_503(self):
        from app.modules.degree_progress.dependencies import get_degree_progress_db
        from fastapi import HTTPException

        request = _make_mock_request()
        with pytest.raises(HTTPException) as exc_info:
            _run_generator_to_completion(get_degree_progress_db(request))
        assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# grades/dependencies.py
# ---------------------------------------------------------------------------

class TestGradesDependencies:
    def test_success_via_grades_factory(self):
        from app.modules.grades.dependencies import get_grades_db

        mock_session = MagicMock()
        request = _make_mock_request(grades_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_grades_db(request))
        assert session is mock_session
        mock_session.close.assert_called_once()

    def test_success_via_profiles_fallback(self):
        from app.modules.grades.dependencies import get_grades_db

        mock_session = MagicMock()
        request = _make_mock_request(profiles_session_factory=MagicMock(return_value=mock_session))

        session = _run_generator_to_completion(get_grades_db(request))
        assert session is mock_session

    def test_missing_factory_raises_503(self):
        from app.modules.grades.dependencies import get_grades_db
        from fastapi import HTTPException

        request = _make_mock_request()
        with pytest.raises(HTTPException) as exc_info:
            _run_generator_to_completion(get_grades_db(request))
        assert exc_info.value.status_code == 503
