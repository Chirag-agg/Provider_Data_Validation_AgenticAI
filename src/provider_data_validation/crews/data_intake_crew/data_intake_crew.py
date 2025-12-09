from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

from tools.pdf_reader import ExtractTextFromPDFTool


@CrewBase
class ProviderIntakeCrew():
	"""Provider Intake Crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self, use_pdf_tool: bool = False):
		# Only enable the PDF extraction tool when explicitly requested.
		self.use_pdf_tool = use_pdf_tool

	llm = LLM(
		model="ollama/llama3.1:latest",
		base_url="http://localhost:11434",
		api_key="not-needed",
	)


	@agent
	def intake_agent(self) -> Agent:
		tools = [ExtractTextFromPDFTool()] if self.use_pdf_tool else []
		return Agent(
			config=self.agents_config['intake_agent'],
			tools=tools,
			llm=self.llm,
		)

	@task
	def intake_task(self) -> Task:
		return Task(
			config=self.tasks_config['intake_task'],
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the Provider Intake Crew"""
		return Crew(
			agents=self.agents,  # Auto-loaded by @agent decorators
			tasks=self.tasks,    # Auto-loaded by @task decorators
			process=Process.sequential,
			verbose=True,
		)
