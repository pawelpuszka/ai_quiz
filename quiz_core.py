from __future__ import annotations

import json
import random
import time
from typing import Any, Dict, Iterable, List, Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

from question_structure import AIAnalyzer, Quiz, QuizAssessment, UserAnswers

DEFAULT_MODEL = "gpt-5-mini"


class QuizCoreError(RuntimeError):
	pass


class QuizModelInvocationError(QuizCoreError):
	pass


def _create_prompt(system_prompt: str, human_prompt: str) -> ChatPromptTemplate:
	return ChatPromptTemplate.from_messages(
		[
			("system", system_prompt),
			("human", human_prompt),
		]
	)


def _invoke_with_retry(*, chain: Any, bind_vars: Dict[str, Any], attempts: int = 3) -> Any:
	last_exc: Optional[BaseException] = None
	for i in range(attempts):
		try:
			return chain.invoke(bind_vars)
		except Exception as exc:
			last_exc = exc
			if i == attempts - 1:
				break
			delay_s = min(8.0, (0.75 * (2**i)) + random.random() * 0.25)
			time.sleep(delay_s)
	raise QuizModelInvocationError("Model invocation failed after retries") from last_exc


def _run_structured_prompt(
	*,
	model: Any,
	structured_class: Any,
	system_prompt: str,
	human_prompt: str,
	bind_vars: Dict[str, Any],
):
	structured_model = model.with_structured_output(structured_class)
	prompt = _create_prompt(system_prompt=system_prompt, human_prompt=human_prompt)
	chain = prompt | structured_model
	return _invoke_with_retry(chain=chain, bind_vars=bind_vars)


def init_model(*, model_name: str = DEFAULT_MODEL, model_provider: str = "openai"):
	"""
	Initialize LangChain chat model using environment variables (e.g. OPENAI_API_KEY).
	"""
	load_dotenv()
	return init_chat_model(model=model_name, model_provider=model_provider)


def generate_quiz(*, model: Any, topic: str, difficulty: str, count: int) -> Quiz:
	system_prompt = "You’re an expert in your field. You create engaging and educational quizzes."
	human_prompt = (
		"Create a quiz on the topic: {topic}. Difficulty level: {difficulty}. "
		"Number of questions: {count}. "
		"Return exactly 4 answers per question and keep indices consistent."
	)
	return _run_structured_prompt(
		model=model,
		structured_class=Quiz,
		system_prompt=system_prompt,
		human_prompt=human_prompt,
		bind_vars={"topic": topic, "difficulty": difficulty, "count": count},
	)


def analyze_answers_ai(*, model: Any, answers: Iterable[UserAnswers]) -> AIAnalyzer:
	system_prompt = "You are responsible for compiling the answers based on the data provided."
	human_prompt = (
		"Analyze the quiz data provided as JSON. "
		"Return a list of per-question assessments in the required schema.\n\n"
		"JSON:\n{raw_data_json}"
	)
	raw_data: List[Dict[str, Any]] = [a.model_dump() for a in answers]
	raw_data_json = json.dumps(raw_data, ensure_ascii=False)
	return _run_structured_prompt(
		model=model,
		structured_class=AIAnalyzer,
		system_prompt=system_prompt,
		human_prompt=human_prompt,
		bind_vars={"raw_data_json": raw_data_json},
	)


def assess_quiz_ai(*, model: Any, analysis: AIAnalyzer) -> QuizAssessment:
	system_prompt = "You are responsible for quiz answers final assessment"
	human_prompt = (
		"This is the quiz analysis {quiz_analysis}. The score in exactly "
		"number_of_correct_questions/format number_of_questions format. No spaces, no words"
	)
	quiz_analysis: List[Optional[str]] = [a.ai_answer for a in analysis.answers]
	return _run_structured_prompt(
		model=model,
		structured_class=QuizAssessment,
		system_prompt=system_prompt,
		human_prompt=human_prompt,
		bind_vars={"quiz_analysis": quiz_analysis},
	)

