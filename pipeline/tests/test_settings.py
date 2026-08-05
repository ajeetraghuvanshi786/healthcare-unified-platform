from healthcare_pipeline.config.settings import get_settings


def test_settings_load_database_url() -> None:
    settings = get_settings()

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.app_env == "local"


def test_project_directories_are_resolved() -> None:
    settings = get_settings()

    assert settings.incoming_data_directory.name == "incoming"
    assert settings.processed_data_directory.name == "processed"
    assert settings.rejected_data_directory.name == "rejected"