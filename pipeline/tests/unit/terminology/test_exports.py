import healthcare_pipeline.terminology as terminology


def test_terminology_public_api_is_resolvable() -> None:
    for name in terminology.__all__:
        assert getattr(terminology, name) is not None
