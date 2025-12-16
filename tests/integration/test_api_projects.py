"""Integration tests for Project API endpoints."""

from datetime import datetime, timedelta, timezone


class TestProjectCreation:
    """Test project creation via API."""

    def test_create_project_returns_201(self, client):
        """POST /projects creates project successfully."""
        response = client.post(
            "/projects",
            json={
                "title": "New Project",
                "description": "Project description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Project"
        assert data["description"] == "Project description"
        assert "id" in data
        assert data["completed"] is False
        assert data["total_task_count"] == 0


class TestProjectRetrieval:
    """Test project retrieval via API."""

    def test_get_project_by_id(self, client):
        """GET /projects/{id} retrieves specific project."""
        # Create a project
        create_response = client.post(
            "/projects",
            json={
                "title": "Test Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = create_response.json()["id"]

        # Retrieve it
        response = client.get(f"/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["title"] == "Test Project"

    def test_get_nonexistent_project_returns_404(self, client):
        """GET /projects/{id} returns 404 for nonexistent project."""
        response = client.get("/projects/nonexistent-id")

        assert response.status_code == 404

    def test_list_all_projects(self, client):
        """GET /projects lists all projects."""
        # Create multiple projects
        client.post(
            "/projects",
            json={
                "title": "Project 1",
                "description": "Description 1",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        client.post(
            "/projects",
            json={
                "title": "Project 2",
                "description": "Description 2",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=60)).isoformat(),
            },
        )

        # List all projects
        response = client.get("/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 2
        assert data["total"] >= len(data["items"])


class TestProjectUpdate:
    """Test project updates via API."""

    def test_update_project_title(self, client):
        """PUT /projects/{id} updates project details."""
        # Create a project
        create_response = client.post(
            "/projects",
            json={
                "title": "Original Title",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = create_response.json()["id"]

        # Update it
        response = client.put(
            f"/projects/{project_id}",
            json={"title": "Updated Title"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_nonexistent_project_returns_404(self, client):
        """PUT /projects/{id} returns 404 for nonexistent project."""
        response = client.put(
            "/projects/nonexistent-id",
            json={"title": "New Title"},
        )

        assert response.status_code == 404


class TestProjectCompletion:
    """Test project completion via API."""

    def test_complete_project_with_no_tasks(self, client):
        """Can complete project with no tasks."""
        # Create a project
        create_response = client.post(
            "/projects",
            json={
                "title": "Empty Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = create_response.json()["id"]

        # Complete it
        response = client.patch(f"/projects/{project_id}/complete")

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True

    def test_complete_project_with_all_tasks_completed(self, client):
        """Can complete project when all tasks are completed."""
        # Create project
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Create and complete a task
        task_response = client.post(
            "/tasks",
            json={
                "title": "Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "project_id": project_id,
            },
        )
        task_id = task_response.json()["id"]
        client.patch(f"/tasks/{task_id}/complete")

        # Complete project
        response = client.patch(f"/projects/{project_id}/complete")

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True

    def test_complete_project_with_incomplete_tasks_returns_400(self, client):
        """Cannot complete project with pending tasks."""
        # Create project
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Create a task but don't complete it
        client.post(
            "/tasks",
            json={
                "title": "Incomplete Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "project_id": project_id,
            },
        )

        # Try to complete project
        response = client.patch(f"/projects/{project_id}/complete")

        assert response.status_code == 400
        assert "pending" in response.json()["message"].lower()


class TestProjectDeletion:
    """Test project deletion via API."""

    def test_delete_project(self, client):
        """DELETE /projects/{id} deletes project."""
        # Create a project
        create_response = client.post(
            "/projects",
            json={
                "title": "Project to Delete",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/projects/{project_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/projects/{project_id}")
        assert get_response.status_code == 404

    def test_delete_project_deletes_tasks(self, client):
        """Deleting project also deletes its tasks."""
        # Create project
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Create task in project
        task_response = client.post(
            "/tasks",
            json={
                "title": "Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "project_id": project_id,
            },
        )
        task_id = task_response.json()["id"]

        # Delete project
        client.delete(f"/projects/{project_id}")

        # Verify task is also gone
        get_task_response = client.get(f"/tasks/{task_id}")
        assert get_task_response.status_code == 404


class TestProjectTaskTracking:
    """Test project task count tracking."""

    def test_project_tracks_task_counts(self, client):
        """Project correctly tracks total and completed task counts."""
        # Create project
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

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
        client.post(
            "/tasks",
            json={
                "title": "Task 2",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "project_id": project_id,
            },
        )

        # Complete one task
        task1_id = task1_response.json()["id"]
        client.patch(f"/tasks/{task1_id}/complete")

        # Check project counts
        response = client.get(f"/projects/{project_id}")
        data = response.json()

        assert data["total_task_count"] == 2
        assert data["completed_task_count"] == 1


class TestProjectTaskLinking:
    """Test task-project linking via API."""

    def test_link_task_to_project_succeeds(self, client):
        """POST /projects/{project_id}/tasks/{task_id}/link links task to project."""
        # Create project
        project_response = client.post(
            "/projects",
            json={
                "title": "Test Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Create task without project
        task_response = client.post(
            "/tasks",
            json={
                "title": "Test Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = task_response.json()["id"]

        # Link task to project
        response = client.post(f"/projects/{project_id}/tasks/{task_id}/link")

        assert response.status_code == 204

        # Verify task is now linked to project
        task_response = client.get(f"/tasks/{task_id}")
        assert task_response.status_code == 200
        assert task_response.json()["project_id"] == project_id

        # Verify project task count increased
        project_response = client.get(f"/projects/{project_id}")
        assert project_response.json()["total_task_count"] == 1

    def test_link_task_with_invalid_deadline_returns_400(self, client):
        """Linking task with deadline after project deadline fails."""
        # Create project with earlier deadline
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Create task with later deadline
        task_response = client.post(
            "/tasks",
            json={
                "title": "Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        task_id = task_response.json()["id"]

        # Try to link them
        response = client.post(f"/projects/{project_id}/tasks/{task_id}/link")

        assert response.status_code == 400
        assert "deadline" in response.json()["message"].lower()

    def test_link_nonexistent_task_returns_404(self, client):
        """Linking non-existent task returns 404."""
        # Create project
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Try to link non-existent task
        response = client.post(f"/projects/{project_id}/tasks/nonexistent-task-id/link")

        assert response.status_code == 404

    def test_link_to_nonexistent_project_returns_404(self, client):
        """Linking task to non-existent project returns 404."""
        # Create task
        task_response = client.post(
            "/tasks",
            json={
                "title": "Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = task_response.json()["id"]

        # Try to link to non-existent project
        response = client.post(f"/projects/nonexistent-project-id/tasks/{task_id}/link")

        assert response.status_code == 404

    def test_link_incomplete_task_reopens_completed_project(self, client):
        """Linking an incomplete task to a completed project reopens the project."""
        # Create and complete a project
        project_response = client.post(
            "/projects",
            json={
                "title": "Completed Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Complete the project
        client.patch(f"/projects/{project_id}/complete")

        # Verify project is completed
        project_response = client.get(f"/projects/{project_id}")
        assert project_response.json()["completed"] is True

        # Create an incomplete task
        task_response = client.post(
            "/tasks",
            json={
                "title": "Incomplete Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = task_response.json()["id"]

        # Link the incomplete task to the completed project
        response = client.post(f"/projects/{project_id}/tasks/{task_id}/link")
        assert response.status_code == 204

        # Verify project is now reopened (not completed)
        project_response = client.get(f"/projects/{project_id}")
        project = project_response.json()
        assert (
            project["completed"] is False
        ), "Project should be reopened when incomplete task is linked"
        assert project["total_task_count"] == 1

    def test_link_completed_task_does_not_reopen_completed_project(self, client):
        """Linking a completed task to a completed project does NOT reopen the project."""
        # Create and complete a project
        project_response = client.post(
            "/projects",
            json={
                "title": "Completed Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Complete the project
        client.patch(f"/projects/{project_id}/complete")

        # Verify project is completed
        project_response = client.get(f"/projects/{project_id}")
        assert project_response.json()["completed"] is True

        # Create and complete a task
        task_response = client.post(
            "/tasks",
            json={
                "title": "Completed Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = task_response.json()["id"]

        # Complete the task
        client.patch(f"/tasks/{task_id}/complete")

        # Verify task is completed
        task_response = client.get(f"/tasks/{task_id}")
        assert task_response.json()["completed"] is True

        # Link the completed task to the completed project
        response = client.post(f"/projects/{project_id}/tasks/{task_id}/link")
        assert response.status_code == 204

        # Verify project remains completed (not reopened)
        project_response = client.get(f"/projects/{project_id}")
        project = project_response.json()
        assert (
            project["completed"] is True
        ), "Project should remain completed when completed task is linked"
        assert project["total_task_count"] == 1
        assert project["completed_task_count"] == 1

    def test_create_task_with_completed_project_reopens_project(self, client):
        """Creating a task assigned to a completed project reopens the project."""
        # Create and complete a project
        project_response = client.post(
            "/projects",
            json={
                "title": "Completed Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Complete the project
        client.patch(f"/projects/{project_id}/complete")

        # Verify project is completed
        project_response = client.get(f"/projects/{project_id}")
        assert project_response.json()["completed"] is True

        # Create a task assigned to the completed project
        task_response = client.post(
            "/tasks",
            json={
                "title": "New Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "project_id": project_id,
            },
        )
        assert task_response.status_code == 201

        # Verify project is now reopened (not completed)
        project_response = client.get(f"/projects/{project_id}")
        project = project_response.json()
        assert project["completed"] is False, (
            "Project should be reopened when new task is created " "with project assignment"
        )
        assert project["total_task_count"] == 1


class TestProjectTaskUnlinking:
    """Test task-project unlinking via API."""

    def test_unlink_task_from_project_succeeds(self, client):
        """DELETE /projects/{project_id}/tasks/{task_id}/unlink unlinks task."""
        # Create project
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Create task linked to project
        task_response = client.post(
            "/tasks",
            json={
                "title": "Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "project_id": project_id,
            },
        )
        task_id = task_response.json()["id"]

        # Verify task is linked
        task_check = client.get(f"/tasks/{task_id}")
        assert task_check.json()["project_id"] == project_id

        # Unlink task from project
        response = client.delete(f"/projects/{project_id}/tasks/{task_id}/unlink")

        assert response.status_code == 204

        # Verify task is no longer linked
        task_response = client.get(f"/tasks/{task_id}")
        assert task_response.status_code == 200
        assert task_response.json()["project_id"] is None

        # Verify project task count decreased
        project_response = client.get(f"/projects/{project_id}")
        assert project_response.json()["total_task_count"] == 0

    def test_unlink_from_nonexistent_project_returns_404(self, client):
        """Unlinking from non-existent project returns 404."""
        # Create task
        task_response = client.post(
            "/tasks",
            json={
                "title": "Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        task_id = task_response.json()["id"]

        # Try to unlink from non-existent project
        response = client.delete(f"/projects/nonexistent-project-id/tasks/{task_id}/unlink")

        assert response.status_code == 404

    def test_unlink_nonexistent_task_returns_404(self, client):
        """Unlinking non-existent task returns 404."""
        # Create project
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Try to unlink non-existent task
        response = client.delete(f"/projects/{project_id}/tasks/nonexistent-task-id/unlink")

        assert response.status_code == 404


class TestGetProjectTasks:
    """Test retrieving tasks for a project via API."""

    def test_get_project_tasks_returns_all_tasks(self, client):
        """GET /projects/{id}/tasks returns all tasks for project."""
        # Create project
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Create multiple tasks for this project
        task1_response = client.post(
            "/tasks",
            json={
                "title": "Task 1",
                "description": "Description 1",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "project_id": project_id,
            },
        )
        task2_response = client.post(
            "/tasks",
            json={
                "title": "Task 2",
                "description": "Description 2",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
                "project_id": project_id,
            },
        )

        task1_id = task1_response.json()["id"]
        task2_id = task2_response.json()["id"]

        # Create a task for a different project (should not be included)
        other_project_response = client.post(
            "/projects",
            json={
                "title": "Other Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        other_project_id = other_project_response.json()["id"]
        client.post(
            "/tasks",
            json={
                "title": "Other Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "project_id": other_project_id,
            },
        )

        # Get tasks for our project
        response = client.get(f"/projects/{project_id}/tasks")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 2

        # Verify correct tasks are returned
        task_ids = [task["id"] for task in data["items"]]
        assert task1_id in task_ids
        assert task2_id in task_ids

        # Verify all tasks belong to the project
        for task in data["items"]:
            assert task["project_id"] == project_id

    def test_get_tasks_for_empty_project(self, client):
        """GET /projects/{id}/tasks returns empty list for project with no tasks."""
        # Create project with no tasks
        project_response = client.post(
            "/projects",
            json={
                "title": "Empty Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Get tasks (should be empty)
        response = client.get(f"/projects/{project_id}/tasks")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0

    def test_get_tasks_for_nonexistent_project_returns_404(self, client):
        """GET /projects/{id}/tasks returns 404 for non-existent project."""
        response = client.get("/projects/nonexistent-project-id/tasks")

        assert response.status_code == 404

    def test_get_project_tasks_includes_completed_tasks(self, client):
        """GET /projects/{id}/tasks includes both completed and incomplete tasks."""
        # Create project
        project_response = client.post(
            "/projects",
            json={
                "title": "Project",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            },
        )
        project_id = project_response.json()["id"]

        # Create and complete a task
        completed_task_response = client.post(
            "/tasks",
            json={
                "title": "Completed Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "project_id": project_id,
            },
        )
        completed_task_id = completed_task_response.json()["id"]
        client.patch(f"/tasks/{completed_task_id}/complete")

        # Create an incomplete task
        incomplete_task_response = client.post(
            "/tasks",
            json={
                "title": "Incomplete Task",
                "description": "Description",
                "deadline": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
                "project_id": project_id,
            },
        )
        incomplete_task_id = incomplete_task_response.json()["id"]

        # Get all tasks
        response = client.get(f"/projects/{project_id}/tasks")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] >= 2

        # Find tasks in response
        tasks_by_id = {task["id"]: task for task in data["items"]}
        assert tasks_by_id[completed_task_id]["completed"] is True
        assert tasks_by_id[incomplete_task_id]["completed"] is False
