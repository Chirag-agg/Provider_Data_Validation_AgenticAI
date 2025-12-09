from typing import List
from crewai import Agent, Crew, Process, Task, LLM
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, task, crew

from tools.twilio_tools import SendRealSMSTool, CallProviderRealTool


@CrewBase
class NotificationCrew:
    """Crew that notifies providers via SMS or call."""

    agents: List[BaseAgent]
    tasks: List[Task]

    ollama_llm = LLM(
        model="ollama/llama3.1:latest",
        base_url="http://localhost:11434",
        api_key="not-needed",
    )

    @agent
    def notifier(self) -> Agent:
        return Agent(
            role="Provider Notifier",
            goal="Send SMS or call providers using Twilio tools.",
            backstory="You notify providers using SMS or calls.",
            tools=[SendRealSMSTool(), CallProviderRealTool()],
            verbose=True,
            llm=self.ollama_llm,
        )

    @task
    def notify_via_sms(self) -> Task:
        return Task(
            description="Send an SMS using the send_real_sms tool.",
            expected_output="A Twilio SMS SID confirming success.",
            agent=self.notifier(),
        )

    @task
    def notify_via_call(self) -> Task:
        return Task(
            description="Call the provider using call_provider_real.",
            expected_output="A Twilio CALL SID confirming success.",
            agent=self.notifier(),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
