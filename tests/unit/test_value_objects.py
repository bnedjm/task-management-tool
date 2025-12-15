"""Unit tests for value objects."""

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions.project_exceptions import PastDateError
from src.domain.value_objects.deadline import Deadline
from src.domain.value_objects.ids import ProjectId, TaskId


class TestTaskId:
    """Test TaskId value object."""

    def test_generate_creates_unique_id(self):
        """Generate creates unique task IDs."""
        id1 = TaskId.generate()
        id2 = TaskId.generate()

        assert id1 != id2

    def test_from_string_creates_task_id(self):
        """Can create TaskId from string."""
        id_str = "test-task-id-123"
        task_id = TaskId.from_string(id_str)

        assert str(task_id) == id_str

    def test_equality(self):
        """TaskIds with same value are equal."""
        id_str = "same-id"
        id1 = TaskId.from_string(id_str)
        id2 = TaskId.from_string(id_str)

        assert id1 == id2

    def test_inequality(self):
        """TaskIds with different values are not equal."""
        id1 = TaskId.from_string("id-1")
        id2 = TaskId.from_string("id-2")

        assert id1 != id2

    def test_hashable(self):
        """TaskIds can be used in sets and dicts."""
        id1 = TaskId.generate()
        id2 = TaskId.generate()

        id_set = {id1, id2}
        assert len(id_set) == 2


class TestProjectId:
    """Test ProjectId value object."""

    def test_generate_creates_unique_id(self):
        """Generate creates unique project IDs."""
        id1 = ProjectId.generate()
        id2 = ProjectId.generate()

        assert id1 != id2

    def test_from_string_creates_project_id(self):
        """Can create ProjectId from string."""
        id_str = "test-project-id-123"
        project_id = ProjectId.from_string(id_str)

        assert str(project_id) == id_str

    def test_equality(self):
        """ProjectIds with same value are equal."""
        id_str = "same-id"
        id1 = ProjectId.from_string(id_str)
        id2 = ProjectId.from_string(id_str)

        assert id1 == id2


class TestDeadline:
    """Test Deadline value object."""

    def test_is_after(self):
        """is_after correctly compares deadlines."""
        earlier = Deadline(datetime.now(timezone.utc) + timedelta(days=1))
        later = Deadline(datetime.now(timezone.utc) + timedelta(days=2))

        assert later.is_after(earlier)
        assert not earlier.is_after(later)

    def test_is_before(self):
        """is_before correctly compares deadlines."""
        earlier = Deadline(datetime.now(timezone.utc) + timedelta(days=1))
        later = Deadline(datetime.now(timezone.utc) + timedelta(days=2))

        assert earlier.is_before(later)
        assert not later.is_before(earlier)

    def test_is_within_hours_future(self):
        """is_within_hours detects deadlines within time window."""
        deadline = Deadline(datetime.now(timezone.utc) + timedelta(hours=12))

        assert deadline.is_within_hours(24)
        assert not deadline.is_within_hours(6)

    def test_past_date_raises_error(self):
        """Creating a deadline in the past raises PastDateError."""
        past_date = datetime.now(timezone.utc) - timedelta(days=1)

        with pytest.raises(PastDateError) as exc_info:
            Deadline(past_date)

        assert "past" in str(exc_info.value).lower()

    def test_is_within_hours_past(self):
        """is_within_hours returns False for deadlines that are not within the window."""
        # Create a deadline far in the future (not within 24 hours)
        deadline = Deadline(datetime.now(timezone.utc) + timedelta(days=2))

        assert not deadline.is_within_hours(24)

    def test_is_overdue_future_deadline(self):
        """is_overdue returns False for future deadlines."""
        deadline = Deadline(datetime.now(timezone.utc) + timedelta(days=1))

        assert not deadline.is_overdue()

    def test_from_string(self):
        """Can create Deadline from ISO format string."""
        # Use a future date to avoid past date validation
        future_date = datetime.now(timezone.utc) + timedelta(days=365)
        date_str = future_date.isoformat()
        deadline = Deadline.from_string(date_str)

        # Compare just the date/time components (ignore timezone)
        expected = future_date.replace(tzinfo=None)
        assert deadline.value.replace(tzinfo=None) == expected

    def test_to_string(self):
        """Can convert Deadline to ISO format string."""
        dt = datetime.now(timezone.utc) + timedelta(days=365)
        deadline = Deadline(dt)

        # Check that it produces a valid ISO format string
        result = deadline.to_string()
        assert dt.strftime("%Y-%m-%d") in result

    def test_equality(self):
        """Deadlines with same datetime are equal."""
        dt = datetime.now(timezone.utc) + timedelta(days=1)
        d1 = Deadline(dt)
        d2 = Deadline(dt)

        assert d1 == d2

    def test_immutability(self):
        """Deadline is immutable (frozen dataclass)."""
        deadline = Deadline(datetime.now(timezone.utc) + timedelta(days=1))

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            deadline.value = datetime.now(timezone.utc) + timedelta(days=2)
