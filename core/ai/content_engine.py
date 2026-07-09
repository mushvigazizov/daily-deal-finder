from datetime import date

from core.ai.local_engine import generate_local_content
from core.ai.openai_engine import generate_openai_content
from core.ai.response_validator import validate_ai_content

def generate_content(product):
    openai_content = generate_openai_content(product)
    validated = validate_ai_content(openai_content)

    if validated:
        validated["content_status"] = "ai_generated"
        validated["content_engine"] = "openai"
        validated["updated_at"] = str(date.today())
        return validated

    return generate_local_content(product)
