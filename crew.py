import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

load_dotenv()  # reads GROQ_API_KEY and SERPER_API_KEY from .env

search = SerperDevTool(n_results=5)
import litellm

def _strip_cache_breakpoint(messages):
    if not isinstance(messages, list):
        return messages
    return [
        {k: v for k, v in m.items() if k != "cache_breakpoint"} if isinstance(m, dict) else m
        for m in messages
    ]

_orig_completion = litellm.completion
_orig_acompletion = litellm.acompletion

def _patched_completion(*args, **kwargs):
    if "messages" in kwargs:
        kwargs["messages"] = _strip_cache_breakpoint(kwargs["messages"])
    return _orig_completion(*args, **kwargs)

async def _patched_acompletion(*args, **kwargs):
    if "messages" in kwargs:
        kwargs["messages"] = _strip_cache_breakpoint(kwargs["messages"])
    return await _orig_acompletion(*args, **kwargs)

litellm.completion = _patched_completion
litellm.acompletion = _patched_acompletion
groq_llm = LLM(
    model="groq/openai/gpt-oss-120b",
    api_key=os.environ["GROQ_API_KEY"],
)


@CrewBase
class ResearchCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        return Agent(config=self.agents_config["researcher"], llm=groq_llm, tools=[search], max_iter=3)



    @agent
    def analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["analyst"],
            llm=groq_llm,
        )

    @agent
    def fact_checker(self) -> Agent:
        return Agent(config=self.agents_config["fact_checker"], llm=groq_llm, tools=[search], max_iter=3)

    @agent
    def writer(self) -> Agent:
        return Agent(
            config=self.agents_config["writer"],
            llm=groq_llm,
        )

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def analysis_task(self) -> Task:
        return Task(config=self.tasks_config["analysis_task"])

    @task
    def fact_check_task(self) -> Task:
        return Task(config=self.tasks_config["fact_check_task"])

    @task
    def report_task(self) -> Task:
        return Task(config=self.tasks_config["report_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
