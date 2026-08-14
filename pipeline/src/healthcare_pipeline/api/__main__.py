import uvicorn

from healthcare_pipeline.config.settings import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "healthcare_pipeline.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        access_log=False,
    )


if __name__ == "__main__":
    main()
