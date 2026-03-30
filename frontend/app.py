from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

import streamlit as st

# Ensure imports work when running `streamlit run frontend/app.py`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
	sys.path.insert(0, PROJECT_ROOT)

from question_structure import Quiz, UserAnswers
from quiz_core import analyze_answers_ai, assess_quiz_ai, generate_quiz, init_model


@dataclass(frozen=True)
class QuizConfig:
	topic: str
	difficulty: str
	count: int
	use_ai_analysis: bool


def _init_state() -> None:
	if "stage" not in st.session_state:
		st.session_state.stage = "config"  # config | quiz | result
	if "quiz" not in st.session_state:
		st.session_state.quiz = None
	if "config" not in st.session_state:
		st.session_state.config = None
	if "user_answers" not in st.session_state:
		st.session_state.user_answers = {}  # question_idx -> "A"/"B"/...
	if "ai_analysis" not in st.session_state:
		st.session_state.ai_analysis = None
	if "ai_assessment" not in st.session_state:
		st.session_state.ai_assessment = None
	if "error" not in st.session_state:
		st.session_state.error = None


def _reset_quiz() -> None:
	st.session_state.stage = "config"
	st.session_state.quiz = None
	st.session_state.config = None
	st.session_state.user_answers = {}
	st.session_state.ai_analysis = None
	st.session_state.ai_assessment = None
	st.session_state.error = None


def _compute_local_score(quiz: Quiz, selected: Dict[int, str]) -> int:
	correct = 0
	for idx, q in enumerate(quiz.questions):
		if selected.get(idx) == q.correct_answer_index:
			correct += 1
	return correct


def _answers_to_models(quiz: Quiz, selected: Dict[int, str]) -> List[UserAnswers]:
	models: List[UserAnswers] = []
	for idx, q in enumerate(quiz.questions):
		models.append(
			UserAnswers(
				question=q.question_text,
				correct_answer=q.correct_answer_index,
				user_answer=selected.get(idx),
			)
		)
	return models


def _render_config() -> None:
	st.subheader("Konfiguracja")

	topic = st.text_input("Temat", value="Python programming language")
	difficulty = st.selectbox("Poziom trudności", options=["easy", "medium", "hard"], index=0)
	count = st.number_input("Liczba pytań", min_value=1, max_value=20, value=5, step=1)
	use_ai_analysis = st.checkbox("Analizuj odpowiedzi przez AI (wolniej, wymaga API)", value=False)

	col1, col2 = st.columns([1, 1])
	with col1:
		generate = st.button("Generuj quiz", type="primary")
	with col2:
		clear = st.button("Wyczyść")

	if clear:
		_reset_quiz()
		st.rerun()

	if generate:
		st.session_state.error = None
		cfg = QuizConfig(
			topic=topic.strip(),
			difficulty=difficulty,
			count=int(count),
			use_ai_analysis=use_ai_analysis,
		)
		st.session_state.config = cfg

		if not cfg.topic:
			st.session_state.error = "Podaj temat."
			return

		try:
			with st.spinner("Generuję quiz..."):
				model = init_model()
				quiz = generate_quiz(model=model, topic=cfg.topic, difficulty=cfg.difficulty, count=cfg.count)
			st.session_state.quiz = quiz
			st.session_state.stage = "quiz"
			st.rerun()
		except Exception as e:
			st.session_state.error = f"Nie udało się wygenerować quizu: {e}"


def _render_quiz(quiz: Quiz) -> None:
	st.subheader(quiz.title or "Quiz")
	st.caption("Odpowiedz na pytania, a potem kliknij „Zakończ i policz wynik”.")

	for idx, q in enumerate(quiz.questions):
		st.markdown(f"**{idx + 1}. {q.question_text}**")

		options = list(q.index)
		format_map = {letter: f"{letter}) {answer}" for letter, answer in zip(q.index, q.answers)}

		previous = st.session_state.user_answers.get(idx)
		default_index: Optional[int] = options.index(previous) if previous in options else None

		chosen = st.radio(
			label="",
			options=options,
			index=default_index,
			format_func=lambda x, fm=format_map: fm.get(x, x),
			key=f"q_{idx}",
		)
		st.session_state.user_answers[idx] = chosen
		st.divider()

	col1, col2 = st.columns([1, 1])
	with col1:
		back = st.button("← Wróć do konfiguracji")
	with col2:
		finish = st.button("Zakończ i policz wynik", type="primary")

	if back:
		st.session_state.stage = "config"
		st.rerun()

	if finish:
		st.session_state.stage = "result"
		st.rerun()


def _render_result(quiz: Quiz, cfg: QuizConfig) -> None:
	st.subheader("Wynik")

	local_correct = _compute_local_score(quiz, st.session_state.user_answers)
	st.metric("Wynik (lokalnie)", value=f"{local_correct}/{len(quiz.questions)}")

	answers_models = _answers_to_models(quiz, st.session_state.user_answers)

	if cfg.use_ai_analysis:
		try:
			with st.spinner("Analizuję odpowiedzi przez AI..."):
				model = init_model()
				analysis = analyze_answers_ai(model=model, answers=answers_models)
				assessment = assess_quiz_ai(model=model, analysis=analysis)
			st.session_state.ai_analysis = analysis
			st.session_state.ai_assessment = assessment
		except Exception as e:
			st.warning(f"AI analiza nie powiodła się: {e}")

	if st.session_state.ai_assessment is not None:
		st.metric("Wynik (AI)", value=st.session_state.ai_assessment.assessment)

	st.divider()
	st.subheader("Szczegóły")

	analysis_answers = None
	if st.session_state.ai_analysis is not None:
		analysis_answers = st.session_state.ai_analysis.answers

	for idx, q in enumerate(quiz.questions):
		user_choice = st.session_state.user_answers.get(idx)
		correct_choice = q.correct_answer_index

		user_text = None
		correct_text = None
		for letter, answer in zip(q.index, q.answers):
			if letter == user_choice:
				user_text = answer
			if letter == correct_choice:
				correct_text = answer

		is_correct = user_choice == correct_choice
		st.markdown(f"**{idx + 1}. {q.question_text}**")
		st.write(f"Twoja odpowiedź: {user_choice}) {user_text}" if user_choice else "Twoja odpowiedź: (brak)")
		st.write(f"Poprawna: {correct_choice}) {correct_text}")
		st.write("Status: ✅ poprawnie" if is_correct else "Status: ❌ błędnie")

		if analysis_answers is not None and idx < len(analysis_answers) and analysis_answers[idx].ai_answer:
			with st.expander("Analiza AI", expanded=False):
				st.write(analysis_answers[idx].ai_answer)
		st.divider()


	col1, col2, col3 = st.columns([1, 1, 1])
	with col1:
		again = st.button("Nowy quiz")
	with col2:
		back = st.button("← Wróć do pytań")
	with col3:
		to_config = st.button("⏪ Wróć do konfiguracji")

	if again:
		_reset_quiz()
		st.rerun()
	if back:
		st.session_state.stage = "quiz"
		st.rerun()
	if to_config:
		_reset_quiz()
		st.session_state.stage = "config"
		st.rerun()


def main() -> None:
	st.set_page_config(page_title="Quiz", page_icon="🧠", layout="centered")
	_init_state()

	st.title("Quiz generator")
	st.caption("Generowanie quizu przez LLM + proste UI w Streamlit.")

	if st.session_state.error:
		st.error(st.session_state.error)

	stage = st.session_state.stage
	quiz = st.session_state.quiz
	cfg = st.session_state.config

	if stage == "config" or quiz is None or cfg is None:
		_render_config()
		return

	if stage == "quiz":
		_render_quiz(quiz)
		return

	_render_result(quiz, cfg)


if __name__ == "__main__":
	main()

