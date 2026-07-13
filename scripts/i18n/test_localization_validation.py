from copy import deepcopy

from core.i18n.localization_openai import (
    validate_localized_content,
)


def valid_content():
    return {
        "id": "camp-001",
        "language": "en",
        "title": "Coleman 2-Person Dome Tent",
        "short_description": (
            "A waterproof tent for two people."
        ),
        "long_description": (
            "A practical waterproof tent for "
            "weekend camping trips."
        ),
        "features": [
            "Two-person capacity",
            "Waterproof construction",
        ],
        "button_text": "View on Amazon",
        "buying_angle": (
            "A practical choice for weekend campers."
        ),
        "seo_title": "Coleman 2-Person Dome Tent",
        "meta_description": (
            "A waterproof two-person tent for camping trips."
        ),
        "alt_text": "Coleman two-person dome tent",
        "pinterest_title": "Coleman Dome Tent for Camping",
        "pinterest_description": (
            "A practical waterproof tent for weekend camping trips."
        ),
        "hashtags": [
            "#camping",
            "#outdoor",
        ],
        "source": "localized_from_de_v2",
    }


def assert_valid(content):
    errors = validate_localized_content(
        content,
        "camp-001",
        "en",
    )

    if errors:
        raise AssertionError(
            f"Expected valid English content, got: {errors}"
        )


def assert_error(content, expected_text):
    errors = validate_localized_content(
        content,
        "camp-001",
        "en",
    )

    if not any(expected_text in error for error in errors):
        raise AssertionError(
            f"Expected error containing {expected_text!r}, "
            f"got: {errors}"
        )


def main():
    tests_run = 0

    assert_valid(valid_content())
    tests_run += 1
    print("PASS valid_en")

    content = deepcopy(valid_content())
    content["seo_title"] = "A" * 71
    assert_error(
        content,
        "seo_title exceeds 70 characters",
    )
    tests_run += 1
    print("PASS seo_title_limit")

    content = deepcopy(valid_content())
    content["meta_description"] = "A" * 161
    assert_error(
        content,
        "meta_description exceeds 160 characters",
    )
    tests_run += 1
    print("PASS meta_description_limit")

    content = deepcopy(valid_content())
    content["id"] = "camp-999"
    assert_error(
        content,
        "Invalid id",
    )
    tests_run += 1
    print("PASS fixed_product_id")

    content = deepcopy(valid_content())
    content["language"] = "de"
    assert_error(
        content,
        "Invalid language",
    )
    tests_run += 1
    print("PASS fixed_language")

    content = deepcopy(valid_content())
    content["source"] = "wrong_source"
    assert_error(
        content,
        "Invalid source value",
    )
    tests_run += 1
    print("PASS fixed_source")

    content = deepcopy(valid_content())
    content["hashtags"] = ["camping"]
    assert_error(
        content,
        "must start with #",
    )
    tests_run += 1
    print("PASS hashtag_prefix")

    content = deepcopy(valid_content())
    del content["alt_text"]
    assert_error(
        content,
        "Missing fields: alt_text",
    )
    tests_run += 1
    print("PASS missing_field")

    content = deepcopy(valid_content())
    content["unexpected"] = "value"
    assert_error(
        content,
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
