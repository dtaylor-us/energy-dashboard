import logging
import instructor
from instructor import Instructor, AsyncInstructor

from anthropic import Anthropic, AsyncAnthropic
from groq import Groq, AsyncGroq
from openai import OpenAI, AsyncOpenAI

from energy_dashboard.models import LLMModel, SqlSelectQuery


# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def gen_client(model=LLMModel.GPT4_Omni) -> Instructor:
    match model:
        case LLMModel.Claude3:
            client = instructor.from_anthropic(Anthropic())
        case LLMModel.GPT4_Omni:
            client = instructor.patch(OpenAI())
        case LLMModel.LLAMA3:
            client = instructor.patch(Groq())
    return client


def gen_async_client(model=LLMModel.GPT4_Omni) -> AsyncInstructor:
    match model:
        case LLMModel.Claude3:
            client = instructor.from_anthropic(AsyncAnthropic())
        case LLMModel.GPT4_Omni:
            client = instructor.patch(AsyncOpenAI())
        case LLMModel.LLAMA3:
            client = instructor.patch(AsyncGroq())
    return client


def gen_select_query(
    ai_client: Instructor, schema, parametre: str, model=LLMModel.GPT4_Omni
) -> SqlSelectQuery:
    system_msg = f"""
    Issue a valid SQL statement based given the following table schema:
    '''sql
    {schema}
    '''
    """
    log.info(f"system_msg: {system_msg}")
    log.info(f"parametre: {parametre}")
    query = ai_client.chat.completions.create(
        model=model,
        response_model=SqlSelectQuery,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": parametre},
        ],
    )
    return query


async def streaming_gen_select_query(
    ai_client: AsyncInstructor, schema, parametre: str, model=LLMModel.GPT4_Omni
) -> SqlSelectQuery:
    system_msg = f"""
    Issue a valid SQL statement based given the following table schema:
    '''sql
    {schema}
    '''
    """
    log.info(f"system_msg: {system_msg}")
    log.info(f"parametre: {parametre}")
    query = await ai_client.chat.completions.create(
        model=model,
        response_model=SqlSelectQuery,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": parametre},
        ],
    )
    return query
