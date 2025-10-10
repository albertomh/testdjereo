from testdjereo.models import CreatedAtModel, DeletedAtModel, UpdatedAtModel


class TestModelCreatedAt(CreatedAtModel):
    class Meta:
        app_label = "test_app"


class TestModelUpdatedAt(UpdatedAtModel):
    class Meta:
        app_label = "test_app"


class TestModelDeletedAt(DeletedAtModel):
    class Meta:
        app_label = "test_app"
