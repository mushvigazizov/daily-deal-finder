from core.i18n.missing_languages import missing_languages


def build_generation_plan(product_id):
    missing = missing_languages(product_id)

    return {
        "product_id": product_id,
        "generate_languages": missing,
        "skip_generation": len(missing) == 0,
    }


if __name__ == "__main__":
    plan = build_generation_plan("camp-001")

    print(plan)
