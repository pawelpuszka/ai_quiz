from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


def _normalize_index_letter(value: str) -> str:
	return value.strip().upper()


class Question(BaseModel):
	index: List[str] = Field(description="An index of answers denoted by consecutive letters. There are as many letters as there are answers to a given question")
	question_text: str = Field(description="The question")
	answers: List[str] = Field(description="A list of four answers to the question. Three are incorrect and one is correct")
	correct_answer_index: str = Field(description="Index of correct answer - one letter")

	@field_validator("index")
	@classmethod
	def _validate_index(cls, v: List[str]) -> List[str]:
		if not isinstance(v, list) or not v:
			raise ValueError("index must be a non-empty list")
		normalized = [_normalize_index_letter(x) for x in v]
		if any(len(x) != 1 or not x.isalpha() for x in normalized):
			raise ValueError("index must contain single letters only")
		if len(set(normalized)) != len(normalized):
			raise ValueError("index letters must be unique")
		return normalized

	@field_validator("correct_answer_index")
	@classmethod
	def _validate_correct_answer_index(cls, v: str) -> str:
		vn = _normalize_index_letter(v)
		if len(vn) != 1 or not vn.isalpha():
			raise ValueError("correct_answer_index must be a single letter")
		return vn

	@model_validator(mode="after")
	def _validate_consistency(self) -> "Question":
		if len(self.answers) != len(self.index):
			raise ValueError("answers and index must have the same length")
		if len(self.answers) != 4:
			raise ValueError("answers must contain exactly 4 items")
		if self.correct_answer_index not in self.index:
			raise ValueError("correct_answer_index must be present in index")
		return self


class Quiz(BaseModel):
	title: str
	questions: List[Question]


class UserAnswers(BaseModel):
	question: str|None = Field(default=None, description="The question")
	correct_answer: str|None = Field(default=None, description="the correct answer to the question")
	user_answer: str|None = Field(default=None, description="User's answer")
	ai_answer: str|None = Field(default=None, description="Answer assessment – the question, the user’s answer and the correct answer. If the user gave an incorrect answer – a brief explanation of why")


class AIAnalyzer(BaseModel):
	answers: List[UserAnswers] = Field(description="A list of objects containing the data required for a correct analysis of the user’s response")


class QuizAssessment(BaseModel):
	assessment: str = Field(
		description="Quiz final assessment. The score in exactly number_of_correct_questions/format number_of_questions format. No spaces, no words"
	)

	@field_validator("assessment")
	@classmethod
	def _validate_assessment_format(cls, v: str) -> str:
		val = v.strip()
		parts = val.split("/")
		if len(parts) != 2:
			raise ValueError("assessment must be in 'x/y' format")
		left, right = parts[0].strip(), parts[1].strip()
		if not (left.isdigit() and right.isdigit()):
			raise ValueError("assessment must be in 'x/y' numeric format")
		return f"{int(left)}/{int(right)}"
