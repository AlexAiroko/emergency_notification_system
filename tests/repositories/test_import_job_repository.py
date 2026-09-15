import pytest

from app.models.import_job import ImportJobStatus


@pytest.mark.asyncio
async def test_create(import_job_repo):
    job = await import_job_repo.create(filename="contacts.csv")

    assert job.id is not None
    assert job.filename == "contacts.csv"
    assert job.status == ImportJobStatus.PENDING
    assert job.total == 0
    assert job.imported == 0
    assert job.skipped == 0
    assert job.errors == []


@pytest.mark.asyncio
async def test_get(import_job_repo):
    job = await import_job_repo.create(filename="contacts.csv")
    await import_job_repo.flush()

    found = await import_job_repo.get(job.id)

    assert found is not None
    assert found.id == job.id
    assert found.filename == "contacts.csv"


@pytest.mark.asyncio
async def test_get_not_found(import_job_repo):
    found = await import_job_repo.get(999999)

    assert found is None


@pytest.mark.asyncio
async def test_update_progress(import_job_repo):
    job = await import_job_repo.create(filename="contacts.csv")
    await import_job_repo.flush()

    await import_job_repo.update_progress(
        job.id,
        imported=50,
        skipped=3,
        errors=[{"row": 2, "reason": "bad email"}],
    )
    await import_job_repo.flush()

    updated = await import_job_repo.get(job.id)
    assert updated.imported == 50
    assert updated.skipped == 3
    assert updated.errors == [{"row": 2, "reason": "bad email"}]
    assert updated.status == ImportJobStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_mark_completed(import_job_repo):
    job = await import_job_repo.create(filename="contacts.csv")
    await import_job_repo.flush()

    await import_job_repo.mark_completed(job.id)
    await import_job_repo.flush()

    updated = await import_job_repo.get(job.id)
    assert updated.status == ImportJobStatus.COMPLETED


@pytest.mark.asyncio
async def test_mark_failed(import_job_repo):
    job = await import_job_repo.create(filename="contacts.csv")
    await import_job_repo.flush()

    errors = [{"row": 0, "reason": "S3 connection failed"}]
    await import_job_repo.mark_failed(job.id, errors)
    await import_job_repo.flush()

    updated = await import_job_repo.get(job.id)
    assert updated.status == ImportJobStatus.FAILED
    assert updated.errors == errors
