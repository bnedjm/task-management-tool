"""Integration tests for Task API endpoints."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch


class TestTaskCreation:
    """Test task creation via API."""

    def test_create_task_returns_201(self, client):
        """POST /tasks creates task successfully."""
        response = client.post(
            "/tasks",
            json={
                "title": "New Task",
                "description": "Task description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["description"] == "Task description"
        assert "id" in data
        assert data["completed"] is False

    def test_create_task_with_project_succeeds(self, client):
        """Can create task assigned to a project."""
        # First create a project
        project_response = client.post(
            "/projects",
            json={
                "title": "Test Project",
                "description": "Project description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Create task with project assignment
        response = client.post(
            "/tasks",
            json={
                "title": "Project Task",
                "description": "Task for project",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "project_id": project_id,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == project_id

    def test_create_task_with_invalid_project_deadline_returns_400(self, client):
        """Cannot create task with deadline after project deadline."""
        # Create project with earlier deadline
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Test project",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Try to create task with later deadline
        response = client.post(
            "/tasks",
            json={
                "title": "Task",
                "description": "Test task",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "project_id": project_id,
            },
        )

        assert response.status_code == 400
        assert "deadline" in response.json()["message"].lower()


class TestTaskRetrieval:
    """Test task retrieval via API."""

    def test_get_task_by_id(self, client):
        """GET /tasks/{id} retrieves specific task."""
        # Create a task
        create_response = client.post(
            "/tasks",
            json={
                "title": "Test Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = create_response.json()["id"]

        # Retrieve it
        response = client.get(f"/tasks/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Test Task"

    def test_get_nonexistent_task_returns_404(self, client):
        """GET /tasks/{id} returns 404 for nonexistent task."""
        response = client.get("/tasks/nonexistent-id")

        assert response.status_code == 404

    def test_list_all_tasks(self, client):
        """GET /tasks lists all tasks."""
        # Create multiple tasks
        client.post(
            "/tasks",
            json={
                "title": "Task 1",
                "description": "Description 1",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            },
        )
        client.post(
            "/tasks",
            json={
                "title": "Task 2",
                "description": "Description 2",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            },
        )

        # List all tasks
        response = client.get("/tasks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_list_completed_tasks_only(self, client):
        """GET /tasks?completed=true filters completed tasks."""
        # Create and complete a task
        create_response = client.post(
            "/tasks",
            json={
                "title": "Task to Complete",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            },
        )
        task_id = create_response.json()["id"]
        client.patch(f"/tasks/{task_id}/complete")

        # Create an incomplete task
        client.post(
            "/tasks",
            json={
                "title": "Incomplete Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            },
        )

        # List only completed tasks
        response = client.get("/tasks?completed=true")

        assert response.status_code == 200
        data = response.json()
        assert all(task["completed"] for task in data)


class TestTaskUpdate:
    """Test task updates via API."""

    def test_update_task_title(self, client):
        """PUT /tasks/{id} updates task details."""
        # Create a task
        create_response = client.post(
            "/tasks",
            json={
                "title": "Original Title",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = create_response.json()["id"]

        # Update it
        response = client.put(
            f"/tasks/{task_id}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_nonexistent_task_returns_404(self, client):
        """PUT /tasks/{id} returns 404 for nonexistent task."""
        response = client.put(
            "/tasks/nonexistent-id",
            json={"title": "New Title"},
        )

        assert response.status_code == 404


class TestTaskCompletion:
    """Test task completion via API."""

    def test_complete_task(self, client):
        """PATCH /tasks/{id}/complete marks task as completed."""
        # Create a task
        create_response = client.post(
            "/tasks",
            json={
                "title": "Task to Complete",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = create_response.json()["id"]

        # Complete it
        response = client.patch(f"/tasks/{task_id}/complete")

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True

    def test_complete_already_completed_task_returns_400(self, client):
        """Cannot complete an already completed task."""
        # Create and complete a task
        create_response = client.post(
            "/tasks",
            json={
                "title": "Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = create_response.json()["id"]
        client.patch(f"/tasks/{task_id}/complete")

        # Try to complete again
        response = client.patch(f"/tasks/{task_id}/complete")

        assert response.status_code == 400

    def test_reopen_task(self, client):
        """PATCH /tasks/{id}/reopen reopens completed task."""
        # Create and complete a task
        create_response = client.post(
            "/tasks",
            json={
                "title": "Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = create_response.json()["id"]
        client.patch(f"/tasks/{task_id}/complete")

        # Reopen it
        response = client.patch(f"/tasks/{task_id}/reopen")

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is False


class TestTaskDeletion:
    """Test task deletion via API."""

    def test_delete_task(self, client):
        """DELETE /tasks/{id} deletes task."""
        # Create a task
        create_response = client.post(
            "/tasks",
            json={
                "title": "Task to Delete",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/tasks/{task_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404


class TestAutoCompleteProject:
    """Test automatic project completion when last task is completed."""

    def test_complete_last_task_auto_completes_project(self, client):
        """Completing last task auto-completes project if enabled."""
        # Ensure event bus is initialized with correct config
        from src.api import dependencies
        from src.infrastructure import config as config_module

        # Reset both the event bus and config singleton to ensure clean state
        dependencies._event_bus = None
        config_module._config_instance = None

        # Patch at the module level where it's actually imported
        with patch.object(config_module, "_config_instance", None):
            with patch.object(config_module, "Config") as MockConfig:
                # Create a config instance with auto-complete enabled
                mock_config = config_module.Config(AUTO_COMPLETE_PROJECTS=True)
                MockConfig.return_value = mock_config

                # Patch the get_config to return our enabled config
                with patch.object(config_module, "get_config", return_value=mock_config):
                    # Force re-initialization with enabled config
                    dependencies.get_event_bus()

                    # Create project
                    project_response = client.post(
                        "/projects",
                        json={
                            "title": "Auto Complete Project",
                            "description": "Test project",
                            "deadline": (
                                datetime.now(timezone.utc) + timedelta(days=30)
                            ).isoformat(),
                        },
                    )
                    project_id = project_response.json()["id"]

                    # Verify project starts as incomplete
                    project_response = client.get(f"/projects/{project_id}")
                    assert project_response.status_code == 200
                    project = project_response.json()
                    assert project["completed"] is False
                    assert project["total_task_count"] == 0

                    # Create two tasks
                    task1_response = client.post(
                        "/tasks",
                        json={
                            "title": "Task 1",
                            "description": "Description",
                            "deadline": (
                                datetime.now(timezone.utc) + timedelta(days=7)
                            ).isoformat(),
                            "project_id": project_id,
                        },
                    )
                    task2_response = client.post(
                        "/tasks",
                        json={
                            "title": "Task 2",
                            "description": "Description",
                            "deadline": (
                                datetime.now(timezone.utc) + timedelta(days=7)
                            ).isoformat(),
                            "project_id": project_id,
                        },
                    )

                    task1_id = task1_response.json()["id"]
                    task2_id = task2_response.json()["id"]

                    # Verify project has 2 tasks, none completed
                    project_response = client.get(f"/projects/{project_id}")
                    project = project_response.json()
                    assert project["total_task_count"] == 2
                    assert project["completed_task_count"] == 0
                    assert project["completed"] is False

                    # Complete first task
                    response = client.patch(f"/tasks/{task1_id}/complete")
                    assert response.status_code == 200

                    # Verify project is still incomplete (1/2 tasks done)
                    project_response = client.get(f"/projects/{project_id}")
                    project = project_response.json()
                    assert project["completed_task_count"] == 1
                    assert project["completed"] is False

                    # Complete second (last) task
                    response = client.patch(f"/tasks/{task2_id}/complete")
                    assert response.status_code == 200

                    # Verify project is now automatically completed (2/2 tasks done)
                    project_response = client.get(f"/projects/{project_id}")
                    project = project_response.json()
                    assert project["completed_task_count"] == 2
                    assert project["total_task_count"] == 2
                    # With the fix, auto-completion should work now
                    assert (
                        project["completed"] is True
                    ), "Project should be auto-completed when all tasks are done"

        # Cleanup: Reset singletons after test
        dependencies._event_bus = None
        config_module._config_instance = None

    def test_complete_last_task_does_not_auto_complete_when_disabled(self, client):
        """When AUTO_COMPLETE is disabled, completing last task doesn't auto-complete project."""
        # Ensure event bus is initialized with correct config
        from src.api import dependencies
        from src.infrastructure import config as config_module
        from src.infrastructure.config import Config

        # Reset both the event bus and config singleton to ensure clean state
        dependencies._event_bus = None
        config_module._config_instance = None

        # Create a real Config instance with auto-complete disabled
        disabled_config = Config(AUTO_COMPLETE_PROJECTS=False)

        # Patch get_config in both the config module and dependencies module
        # (dependencies imports get_config directly, so we need to patch it there too)
        with patch.object(config_module, "get_config", return_value=disabled_config):
            with patch.object(dependencies, "get_config", return_value=disabled_config):
                # Force re-initialization with disabled config
                dependencies.get_event_bus()

                # Create project
                project_response = client.post(
                    "/projects",
                    json={
                        "title": "Disabled Auto Complete Project",
                        "description": "Test project",
                        "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                    },
                )
                project_id = project_response.json()["id"]

                # Verify project starts as incomplete
                project_response = client.get(f"/projects/{project_id}")
                assert project_response.status_code == 200
                project = project_response.json()
                assert project["completed"] is False
                assert project["total_task_count"] == 0

                # Create two tasks
                task1_response = client.post(
                    "/tasks",
                    json={
                        "title": "Task 1",
                        "description": "Description",
                        "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                        "project_id": project_id,
                    },
                )
                task2_response = client.post(
                    "/tasks",
                    json={
                        "title": "Task 2",
                        "description": "Description",
                        "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                        "project_id": project_id,
                    },
                )

                task1_id = task1_response.json()["id"]
                task2_id = task2_response.json()["id"]

                # Verify project has 2 tasks, none completed
                project_response = client.get(f"/projects/{project_id}")
                project = project_response.json()
                assert project["total_task_count"] == 2
                assert project["completed_task_count"] == 0
                assert project["completed"] is False

                # Complete first task
                response = client.patch(f"/tasks/{task1_id}/complete")
                assert response.status_code == 200

                # Verify project is still incomplete (1/2 tasks done)
                project_response = client.get(f"/projects/{project_id}")
                project = project_response.json()
                assert project["completed_task_count"] == 1
                assert project["completed"] is False

                # Complete second (last) task
                response = client.patch(f"/tasks/{task2_id}/complete")
                assert response.status_code == 200

                # Verify project is not automatically completed (2/2 tasks done)
                project_response = client.get(f"/projects/{project_id}")
                project = project_response.json()
                assert project["completed_task_count"] == 2
                assert project["total_task_count"] == 2
                assert (
                    project["completed"] is False
                ), "Project should not be auto-completed when auto-complete is disabled"

        # Cleanup: Reset singletons after test
        dependencies._event_bus = None
        config_module._config_instance = None

    def test_delete_incomplete_task_auto_completes_when_remaining_complete(self, client):
        """Deleting incomplete task auto-completes project if all remaining tasks are complete."""
        from src.api import dependencies
        from src.infrastructure import config as config_module

        # Reset both the event bus and config singleton to ensure clean state
        dependencies._event_bus = None
        config_module._config_instance = None

        with patch.object(config_module, "_config_instance", None):
            with patch.object(config_module, "Config") as MockConfig:
                mock_config = config_module.Config(AUTO_COMPLETE_PROJECTS=True)
                MockConfig.return_value = mock_config

                with patch.object(config_module, "get_config", return_value=mock_config):
                    dependencies.get_event_bus()

                    # Create project
                    project_response = client.post(
                        "/projects",
                        json={
                            "title": "Auto Complete Project",
                            "description": "Test project",
                            "deadline": (
                                datetime.now(timezone.utc) + timedelta(days=30)
                            ).isoformat(),
                        },
                    )
                    project_id = project_response.json()["id"]

                    # Create two tasks
                    task1_response = client.post(
                        "/tasks",
                        json={
                            "title": "Task 1",
                            "description": "Description",
                            "deadline": (
                                datetime.now(timezone.utc) + timedelta(days=7)
                            ).isoformat(),
                            "project_id": project_id,
                        },
                    )
                    task2_response = client.post(
                        "/tasks",
                        json={
                            "title": "Task 2",
                            "description": "Description",
                            "deadline": (
                                datetime.now(timezone.utc) + timedelta(days=7)
                            ).isoformat(),
                            "project_id": project_id,
                        },
                    )

                    task1_id = task1_response.json()["id"]
                    task2_id = task2_response.json()["id"]

                    # Complete task 1
                    client.patch(f"/tasks/{task1_id}/complete")

                    # Verify project is incomplete (1/2 tasks done)
                    project_response = client.get(f"/projects/{project_id}")
                    project = project_response.json()
                    assert project["completed"] is False
                    assert project["completed_task_count"] == 1
                    assert project["total_task_count"] == 2

                    # Delete the incomplete task (task 2)
                    # After deletion, only task 1 remains, which is complete
                    response = client.delete(f"/tasks/{task2_id}")
                    assert response.status_code == 204

                    # Verify project should be auto-completed (all remaining tasks are complete)
                    project_response = client.get(f"/projects/{project_id}")
                    project = project_response.json()
                    assert project["total_task_count"] == 1
                    assert project["completed_task_count"] == 1
                    assert project["completed"] is True, (
                        "Project should be auto-completed when incomplete task is "
                        "deleted and all remaining tasks are complete"
                    )

        # Cleanup
        dependencies._event_bus = None
        config_module._config_instance = None

    def test_unlink_incomplete_task_auto_completes_when_remaining_complete(self, client):
        """Unlinking incomplete task auto-completes project if all remaining tasks are complete."""
        from src.api import dependencies
        from src.infrastructure import config as config_module

        # Reset both the event bus and config singleton to ensure clean state
        dependencies._event_bus = None
        config_module._config_instance = None

        with patch.object(config_module, "_config_instance", None):
            with patch.object(config_module, "Config") as MockConfig:
                mock_config = config_module.Config(AUTO_COMPLETE_PROJECTS=True)
                MockConfig.return_value = mock_config

                with patch.object(config_module, "get_config", return_value=mock_config):
                    dependencies.get_event_bus()

                    # Create project
                    project_response = client.post(
                        "/projects",
                        json={
                            "title": "Auto Complete Project",
                            "description": "Test project",
                            "deadline": (
                                datetime.now(timezone.utc) + timedelta(days=30)
                            ).isoformat(),
                        },
                    )
                    project_id = project_response.json()["id"]

                    # Create two tasks
                    task1_response = client.post(
                        "/tasks",
                        json={
                            "title": "Task 1",
                            "description": "Description",
                            "deadline": (
                                datetime.now(timezone.utc) + timedelta(days=7)
                            ).isoformat(),
                            "project_id": project_id,
                        },
                    )
                    task2_response = client.post(
                        "/tasks",
                        json={
                            "title": "Task 2",
                            "description": "Description",
                            "deadline": (
                                datetime.now(timezone.utc) + timedelta(days=7)
                            ).isoformat(),
                            "project_id": project_id,
                        },
                    )

                    task1_id = task1_response.json()["id"]
                    task2_id = task2_response.json()["id"]

                    # Complete task 1
                    client.patch(f"/tasks/{task1_id}/complete")

                    # Verify project is incomplete (1/2 tasks done)
                    project_response = client.get(f"/projects/{project_id}")
                    project = project_response.json()
                    assert project["completed"] is False
                    assert project["completed_task_count"] == 1
                    assert project["total_task_count"] == 2

                    # Unlink the incomplete task (task 2)
                    # After unlinking, only task 1 remains, which is complete
                    response = client.delete(f"/projects/{project_id}/tasks/{task2_id}/unlink")
                    assert response.status_code == 204

                    # Verify project should be auto-completed (all remaining tasks are complete)
                    project_response = client.get(f"/projects/{project_id}")
                    project = project_response.json()
                    assert project["total_task_count"] == 1
                    assert project["completed_task_count"] == 1
                    assert project["completed"] is True, (
                        "Project should be auto-completed when incomplete task is "
                        "unlinked and all remaining tasks are complete"
                    )

        # Cleanup
        dependencies._event_bus = None
        config_module._config_instance = None
