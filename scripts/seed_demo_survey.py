#!/usr/bin/env python3
"""Insert a demo survey for development and testing."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cati.db.session import get_session_factory
from cati.db.repositories.survey_repo import SurveyRepository
from cati.survey.builder import SurveyBuilder
from cati.survey.validator import validate_survey


DEMO_SURVEY = (
    SurveyBuilder("Customer Satisfaction Survey")
    .language("en")
    .intro(
        "Hello! I'm calling on behalf of Acme Corp. "
        "I'd like to ask you a few short questions about your recent experience. "
        "This will take about 2 minutes."
    )
    .outro(
        "Thank you so much for your time! Your feedback is very valuable to us. "
        "Have a great day!"
    )
    .add_question(
        "q1_overall",
        "rating_scale",
        "Overall, how satisfied were you with your recent experience with us?",
        rephrasing="Could you rate your overall satisfaction from 1 to 5, where 1 is very dissatisfied and 5 is very satisfied?",
        validation={"min": 1, "max": 5},
    )
    .add_question(
        "q2_recommend",
        "yes_no",
        "Would you recommend our service to a friend or colleague?",
    )
    .add_question(
        "q3_reason",
        "open_ended",
        "What was the main reason for your rating?",
        rephrasing="Could you briefly describe what influenced your rating most?",
        required=False,
    )
    .add_question(
        "q4_contact",
        "yes_no",
        "Would you be willing to be contacted again for a follow-up survey?",
    )
    # Skip q3_reason if they rated 4 or 5 (satisfied customers)
    .add_skip_rule(
        "q1_overall",
        "responses.q1_overall >= 4",
        target="q4_contact",
        priority=0,
    )
    .build()
)


async def seed() -> None:
    validate_survey(DEMO_SURVEY)
    factory = get_session_factory()
    async with factory() as session:
        repo = SurveyRepository(session)
        survey = await repo.create(DEMO_SURVEY)
        print(f"Created demo survey: {survey.id} — {survey.name}")


if __name__ == "__main__":
    asyncio.run(seed())
