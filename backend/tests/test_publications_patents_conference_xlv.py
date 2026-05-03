"""Phase XLV — Publications + Patents + Conference tests (25 tests)."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call

# ─────────────────────────── helpers ────────────────────────────
def _make_row(id_val: str, **kwargs) -> dict:
    return {"id": id_val, **kwargs}


# ═══════════════════════════════════════════════════════════════
# PUBLICATIONS (tests 1-9)
# ═══════════════════════════════════════════════════════════════

class TestPublicationsStates:
    def test_pub_states_complete(self):
        from app.modules.publications.service import PUB_STATES
        assert PUB_STATES == frozenset(
            {"DRAFT", "SUBMITTED", "PEER_REVIEW", "ACCEPTED", "REJECTED", "PUBLISHED"}
        )


class TestCreatePublication:
    def test_create_publication_success(self):
        from app.modules.publications.service import create_publication
        mock_row = _make_row("p1", title="AI Paper", authors=["Alice"], journal="Nature", status="DRAFT", tenant_id=1)
        with patch("app.modules.publications.service.create_entity_for_tenant", return_value=mock_row):
            result = create_publication(1, title="AI Paper", authors=["Alice"])
        assert result["status"] == "DRAFT"
        assert result["pub_id"] == "p1"

    def test_create_publication_missing_title(self):
        from app.modules.publications.service import create_publication
        with pytest.raises(ValueError, match="title"):
            create_publication(1, title="", authors=["Alice"])

    def test_create_publication_missing_authors(self):
        from app.modules.publications.service import create_publication
        with pytest.raises(ValueError, match="authors"):
            create_publication(1, title="AI Paper", authors=[])

    def test_create_publication_bad_tenant(self):
        from app.modules.publications.service import create_publication
        with pytest.raises(ValueError, match="tenant_id"):
            create_publication(0, title="AI Paper", authors=["Alice"])


class TestPublicationFSM:
    def _pub_row(self, status: str) -> dict:
        return _make_row("p1", title="AI Paper", authors=["Alice"], status=status)

    def test_submit_publication_fires_event(self):
        from app.modules.publications.service import submit_publication
        mock_pub = MagicMock()
        with (
            patch("app.modules.publications.service.list_entities_for_tenant", return_value=[self._pub_row("DRAFT")]),
            patch("app.modules.publications.service.EventPublisher", return_value=mock_pub),
        ):
            result = submit_publication(1, pub_id="p1")
        assert result["status"] == "SUBMITTED"
        mock_pub.publish_event.assert_called_once()
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "publication.submitted"

    def test_accept_publication_fires_event(self):
        from app.modules.publications.service import accept_publication
        mock_pub = MagicMock()
        with (
            patch("app.modules.publications.service.list_entities_for_tenant", return_value=[self._pub_row("PEER_REVIEW")]),
            patch("app.modules.publications.service.EventPublisher", return_value=mock_pub),
        ):
            result = accept_publication(1, pub_id="p1")
        assert result["status"] == "ACCEPTED"
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "publication.accepted"

    def test_reject_publication_success(self):
        from app.modules.publications.service import reject_publication
        with (
            patch("app.modules.publications.service.list_entities_for_tenant", return_value=[self._pub_row("PEER_REVIEW")]),
            patch("app.modules.publications.service.EventPublisher"),
        ):
            result = reject_publication(1, pub_id="p1")
        assert result["status"] == "REJECTED"

    def test_publish_fires_event(self):
        from app.modules.publications.service import publish_publication
        mock_pub = MagicMock()
        with (
            patch("app.modules.publications.service.list_entities_for_tenant", return_value=[self._pub_row("ACCEPTED")]),
            patch("app.modules.publications.service.EventPublisher", return_value=mock_pub),
        ):
            result = publish_publication(1, pub_id="p1")
        assert result["status"] == "PUBLISHED"
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "publication.published"

    def test_add_citation_fires_event(self):
        from app.modules.publications.service import add_citation
        mock_pub = MagicMock()
        citation_row = _make_row("c1", pub_id="p1", cited_by="p2")
        with (
            patch("app.modules.publications.service.create_entity_for_tenant", return_value=citation_row),
            patch("app.modules.publications.service.EventPublisher", return_value=mock_pub),
        ):
            result = add_citation(1, pub_id="p1", cited_by="p2")
        assert result["citation_id"] == "c1"
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "publication.citation_added"


# ═══════════════════════════════════════════════════════════════
# PATENTS (tests 10-18)
# ═══════════════════════════════════════════════════════════════

class TestPatentStates:
    def test_patent_states_complete(self):
        from app.modules.patents.service import PATENT_STATES
        assert PATENT_STATES == frozenset(
            {"IDEA", "FILED", "UNDER_REVIEW", "GRANTED", "REJECTED", "LICENSED"}
        )


class TestCreatePatent:
    def test_create_patent_success(self):
        from app.modules.patents.service import create_patent
        mock_row = _make_row("pat1", title="AI Chip", inventors=["Bob"], status="IDEA", tenant_id=1)
        with patch("app.modules.patents.service.create_entity_for_tenant", return_value=mock_row):
            result = create_patent(1, title="AI Chip", inventors=["Bob"])
        assert result["status"] == "IDEA"
        assert result["patent_id"] == "pat1"

    def test_create_patent_missing_title(self):
        from app.modules.patents.service import create_patent
        with pytest.raises(ValueError, match="title"):
            create_patent(1, title="", inventors=["Bob"])

    def test_create_patent_missing_inventors(self):
        from app.modules.patents.service import create_patent
        with pytest.raises(ValueError, match="inventors"):
            create_patent(1, title="AI Chip", inventors=[])


class TestPatentFSM:
    def _pat_row(self, status: str) -> dict:
        return _make_row("pat1", title="AI Chip", inventors=["Bob"], status=status)

    def test_file_patent_fires_event(self):
        from app.modules.patents.service import file_patent
        mock_pub = MagicMock()
        with (
            patch("app.modules.patents.service.list_entities_for_tenant", return_value=[self._pat_row("IDEA")]),
            patch("app.modules.patents.service.EventPublisher", return_value=mock_pub),
        ):
            result = file_patent(1, patent_id="pat1")
        assert result["status"] == "FILED"
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "patent.filed"

    def test_grant_patent_fires_event(self):
        from app.modules.patents.service import grant_patent
        mock_pub = MagicMock()
        with (
            patch("app.modules.patents.service.list_entities_for_tenant", return_value=[self._pat_row("UNDER_REVIEW")]),
            patch("app.modules.patents.service.EventPublisher", return_value=mock_pub),
        ):
            result = grant_patent(1, patent_id="pat1")
        assert result["status"] == "GRANTED"
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "patent.granted"

    def test_reject_patent_success(self):
        from app.modules.patents.service import reject_patent
        with (
            patch("app.modules.patents.service.list_entities_for_tenant", return_value=[self._pat_row("UNDER_REVIEW")]),
            patch("app.modules.patents.service.EventPublisher"),
        ):
            result = reject_patent(1, patent_id="pat1")
        assert result["status"] == "REJECTED"

    def test_license_patent_fires_event(self):
        from app.modules.patents.service import license_patent
        mock_pub = MagicMock()
        with (
            patch("app.modules.patents.service.list_entities_for_tenant", return_value=[self._pat_row("GRANTED")]),
            patch("app.modules.patents.service.EventPublisher", return_value=mock_pub),
        ):
            result = license_patent(1, patent_id="pat1", licensee="Acme Corp")
        assert result["status"] == "LICENSED"
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "patent.licensed"
        assert call_kwargs["payload"]["licensee"] == "Acme Corp"

    def test_invalid_transition_raises(self):
        from app.modules.patents.service import grant_patent
        with (
            patch("app.modules.patents.service.list_entities_for_tenant", return_value=[self._pat_row("IDEA")]),
            patch("app.modules.patents.service.EventPublisher"),
        ):
            with pytest.raises(ValueError, match="Cannot transition"):
                grant_patent(1, patent_id="pat1")

    def test_list_patents_filter_by_status(self):
        from app.modules.patents.service import list_patents
        rows = [
            _make_row("p1", status="IDEA"),
            _make_row("p2", status="FILED"),
            _make_row("p3", status="IDEA"),
        ]
        with patch("app.modules.patents.service.list_entities_for_tenant", return_value=rows):
            result = list_patents(1, status="IDEA")
        assert len(result) == 2
        assert all(r["status"] == "IDEA" for r in result)


# ═══════════════════════════════════════════════════════════════
# CONFERENCE MANAGEMENT (tests 19-25)
# ═══════════════════════════════════════════════════════════════

class TestConferencePaperStates:
    def test_paper_states_complete(self):
        from app.modules.conference_management.service import PAPER_STATES
        expected = frozenset({"ABSTRACT", "FULL_PAPER", "REVIEWED", "ACCEPTED", "REJECTED", "PRESENTED"})
        assert PAPER_STATES == expected


class TestConferenceOperations:
    def test_create_conference_success(self):
        from app.modules.conference_management.service import create_conference
        mock_row = _make_row("conf1", name="AI Summit", venue="NYC", date="2026-09-01", tenant_id=1)
        with patch("app.modules.conference_management.service.create_entity_for_tenant", return_value=mock_row):
            result = create_conference(1, name="AI Summit", venue="NYC", date="2026-09-01")
        assert result["conference_id"] == "conf1"
        assert result["name"] == "AI Summit"

    def test_submit_abstract_success(self):
        from app.modules.conference_management.service import submit_abstract
        mock_row = _make_row("paper1", status="ABSTRACT")
        with patch("app.modules.conference_management.service.create_entity_for_tenant", return_value=mock_row):
            result = submit_abstract(1, conference_id="conf1", title="Deep Learning", author_id="u1")
        assert result["status"] == "ABSTRACT"
        assert result["paper_id"] == "paper1"

    def _paper_row(self, status: str) -> dict:
        return _make_row("paper1", title="Deep Learning", author_id="u1", conference_id="conf1", status=status)

    def test_accept_paper_fires_event(self):
        from app.modules.conference_management.service import accept_paper
        mock_pub = MagicMock()
        with (
            patch("app.modules.conference_management.service.list_entities_for_tenant", return_value=[self._paper_row("REVIEWED")]),
            patch("app.modules.conference_management.service.EventPublisher", return_value=mock_pub),
        ):
            result = accept_paper(1, paper_id="paper1")
        assert result["status"] == "ACCEPTED"
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "conference.paper_accepted"

    def test_schedule_presentation_fires_event(self):
        from app.modules.conference_management.service import schedule_presentation
        mock_pub = MagicMock()
        with (
            patch("app.modules.conference_management.service.list_entities_for_tenant", return_value=[self._paper_row("ACCEPTED")]),
            patch("app.modules.conference_management.service.EventPublisher", return_value=mock_pub),
        ):
            result = schedule_presentation(1, paper_id="paper1", slot="2026-09-02T10:00")
        assert result["status"] == "PRESENTED"
        assert result["slot"] == "2026-09-02T10:00"
        call_kwargs = mock_pub.publish_event.call_args[1]
        assert call_kwargs["event_type"] == "conference.presentation_scheduled"

    def test_invalid_paper_transition_raises(self):
        from app.modules.conference_management.service import accept_paper
        with (
            patch("app.modules.conference_management.service.list_entities_for_tenant", return_value=[self._paper_row("ABSTRACT")]),
            patch("app.modules.conference_management.service.EventPublisher"),
        ):
            with pytest.raises(ValueError, match="Cannot transition"):
                accept_paper(1, paper_id="paper1")

    def test_list_papers_filter_by_conference(self):
        from app.modules.conference_management.service import list_papers
        rows = [
            _make_row("p1", conference_id="conf1", status="ABSTRACT"),
            _make_row("p2", conference_id="conf2", status="ABSTRACT"),
            _make_row("p3", conference_id="conf1", status="ACCEPTED"),
        ]
        with patch("app.modules.conference_management.service.list_entities_for_tenant", return_value=rows):
            result = list_papers(1, conference_id="conf1")
        assert len(result) == 2
        assert all(r["conference_id"] == "conf1" for r in result)
