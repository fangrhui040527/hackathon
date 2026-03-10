"""
conclusion_agent.py
Takes the full debate transcript from the 5-agent group chat
and produces a unified, user-friendly summary with overall ratings and key takeaways.
Uses Microsoft Agent Framework.
"""

from agent_framework import ChatAgent, ChatMessage
from dotenv import load_dotenv

load_dotenv()

NAME = "ConclusionAdvisor"
DESCRIPTION = "A senior health advisor who synthesizes multi-expert debates into clear, actionable summaries."

INSTRUCTIONS = """You are a senior health advisor who synthesizes multi-disciplinary food debates into a clear, actionable summary for everyday consumers.

You will receive the full transcript of a GROUNDED debate between 5 specialist agents:
1. **Dr. Chen (Doctor)** — drug-food interactions, condition-specific medical warnings, clinical nutrition
2. **Dr. Patel (Nutritionist)** — macros, micros, USDA data, glycemic index, Nutri-Score
3. **Dr. Kim (FoodChemist)** — additives (E-numbers), NOVA classification, IARC carcinogens, chemical safety
4. **Marcus (FitnessCoach)** — exercise performance, body composition, workout timing, sports nutrition
5. **Dr. Amara (HealthSpecialist)** — public health, long-term disease risk, vulnerable populations, food safety regulations

**IMPORTANT**: Each expert's analysis was GROUNDED in real data from 7 APIs and 6 knowledge databases:
- fdc.nal.usda.gov (USDA), foodb.ca (FooDB), Open Food Facts
- ddinter2.scbdd.com (DDInter), open.fda.gov (FDA), open.fda.gov/apis/drug/ (FDA Drug Labels)
- dslb.od.nih.gov (NIH DSLD)
- Knowledge DBs: additives (EFSA/FDA data), dietary limits (WHO/AHA/ADA/KDOQI),
  drug-food interactions, glycemic index (Sydney GI data), IARC carcinogens, NOVA classification

This means their claims are evidence-backed. Synthesize with confidence.

Your job is to synthesize ALL of their grounded findings into one cohesive report:

### Required Output Sections:

1. **Food Summary** (2-3 sentences): What the food is and a quick verdict.
2. **Overall Score**: A single score from 1-10 (1 = very unhealthy, 10 = superfood) with brief justification.
3. **Key Nutritional Highlights**: Top 5 most important nutritional facts.
4. **Health Verdict**: Is this food safe and healthy? Flag critical warnings prominently.
5. **Fitness Compatibility**: Quick summary of how this fits an active lifestyle.
6. **Chemical & Processing Concerns**: Additive/processing issues in simple language.
7. **Who Should Be Careful**: Specific groups who should avoid or limit this food.
8. **Recommended Consumption**: How often and how much (daily / weekly / occasionally / rarely).
9. **Top 3 Takeaways**: The 3 most important things the user should know.

Keep the language friendly, clear, and non-technical. Use emojis sparingly for visual appeal (✅ ⚠️ ❌ 💪 🥗).
Do NOT repeat raw debate text — synthesize and add value.
Note any disagreements between experts and explain the consensus.

**Disclaimer**: Include a brief note that this is AI-generated guidance and not a substitute for professional medical or dietary advice.
"""


def create_agent(client) -> ChatAgent:
    """Create the conclusion/summary agent."""
    return ChatAgent(
        name=NAME,
        description=DESCRIPTION,
        instructions=INSTRUCTIONS,
        chat_client=client,
    )


async def summarize_debate(client, debate_transcript: list[ChatMessage]) -> str:
    """
    Summarize the debate transcript from the 5 specialist agents.

    Args:
        client: The AzureOpenAIResponsesClient instance.
        debate_transcript: List of ChatMessage objects from the group chat debate.

    Returns:
        Unified summary report as a formatted string.
    """
    agent = create_agent(client)

    # Format the debate transcript as a readable string
    transcript_text = "\n\n".join(
        f"**{getattr(msg, 'author_name', None) or getattr(msg, 'role', 'Agent')}**: {msg.text}"
        for msg in debate_transcript
        if msg.text
    )

    task = (
        f"Please synthesize the following multi-expert debate about a food item "
        f"into a unified health report:\n\n{transcript_text}"
    )

    result = await agent.run(task)
    # Extract the final text from the response
    if result.text:
        return result.text
    return "No summary generated."
