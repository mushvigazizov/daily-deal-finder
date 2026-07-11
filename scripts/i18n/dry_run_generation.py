from core.ai.content_generation_plan import build_generation_plan


def main():
    product = "camp-001"

    plan = build_generation_plan(product)

    print("=" * 60)
    print("MULTILINGUAL DRY RUN")
    print("=" * 60)
    print(f"Product : {plan['product_id']}")

    if plan["skip_generation"]:
        print("Nothing to generate.")
        return

    print("\nLanguages to generate:\n")

    for language in plan["generate_languages"]:
        print(f"  ✓ {product}.{language}.json")

    print("\nNo files were created.")
    print("This is a dry run only.")


if __name__ == "__main__":
    main()
