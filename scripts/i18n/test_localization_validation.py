from copy import deepcopy

from core.i18n.localization_openai import (
    validate_localized_content,
)


def valid_content(language):
    if language == "en":
        return {
            "id": "camp-001",
            "language": "en",
            "seo_title": "Coleman 2-Person Dome Tent",
            "meta_description": "A waterproof two-person tent for camping trips.",
            "alt_text": "Coleman two-person dome tent",
            "pinterest_title": "Coleman Dome Tent for Camping",
            "pinterest_description": (
                "A practical waterproof tent for weekend camping trips."
            ),
            "hashtags": [
                "#camping",
                "#outdoor",
            ],
            "source": "localized_from_de_v1",
        }

    return {
        "id": "camp-001",
        "language": "ru",
        "seo_title": "Палатка Coleman на двух человек",
        "meta_description": (
            "Водонепроницаемая палатка Coleman для отдыха на природе."
        ),
        "alt_text": "Двухместная палатка Coleman",
        "pinterest_title": "Палатка Coleman для кемпинга",
        "pinterest_description": (
            "Практичная палатка для поездок и отдыха на природе."
        ),
        "hashtags": [
            "#кемпинг",
            "#туризм",
        ],
        "source": "localized_from_de_v1",
    }


def assert_valid(content, language):
    errors = validate_localized_content(
        content,
        "camp-001",
        language,
    )

    if errors:
        raise AssertionError(
            f"Expected valid {language} content, got: {errors}"
        )


def assert_error(content, language, expected_text):
    errors = validate_localized_content(
        content,
        "camp-001",
        language,
    )

    if not any(expected_text in error for error in errors):
        raise AssertionError(
            f"Expected error containing {expected_text!r}, "
            f"got: {errors}"
        )


def main():
    tests_run = 0

    for language in ("en", "ru"):
        assert_valid(
            valid_content(language),
            language,
        )
        tests_run += 1
        print(f"PASS valid_{language}")

    content = deepcopy(valid_content("en"))
    content["seo_title"] = "A" * 71
    assert_error(
        content,
        "en",
        "seo_title exceeds 70 characters",
    )
    tests_run += 1
    print("PASS seo_title_limit")

    content = deepcopy(valid_content("ru"))
    content["meta_description"] = "А" * 161
    assert_error(
        content,
        "ru",
        "meta_description exceeds 160 characters",
    )
    tests_run += 1
    print("PASS meta_description_limit")

    content = deepcopy(valid_content("en"))
    content["id"] = "camp-999"
    assert_error(
        content,
        "en",
        "Invalid id",
    )
    tests_run += 1
    print("PASS fixed_product_id")

    content = deepcopy(valid_content("ru"))
    content["language"] = "en"
    assert_error(
        content,
        "ru",
        "Invalid language",
    )
    tests_run += 1
    print("PASS fixed_language")

    content = deepcopy(valid_content("en"))
    content["source"] = "wrong_source"
    assert_error(
        content,
        "en",
        "Invalid source value",
    )
    tests_run += 1
    print("PASS fixed_source")

    content = deepcopy(valid_content("ru"))
    content["hashtags"] = ["кемпинг"]
    assert_error(
        content,
        "ru",
        "must start with #",
    )
    tests_run += 1
    print("PASS hashtag_prefix")

    content = deepcopy(valid_content("en"))
    del content["alt_text"]
    assert_error(
        content,
        "en",
        "Missing fields: alt_text",
    )
    tests_run += 1
    print("PASS missing_field")

    content = deepcopy(valid_content("ru"))
    content["unexpected"] = "value"
    assert_error(
        content,
        "ru",
        "Unexpected fields: unexpected",
    )
    tests_run += 1
    print("PASS unexpected_field")

    print()
    print("=" * 72)
    print("LOCALIZATION VALIDATION TEST SUMMARY")
    print("=" * 72)
    print(f"Tests run : {tests_run}")
    print(f"Passed    : {tests_run}")
    print("Failed    : 0")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
