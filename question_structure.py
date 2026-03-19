from typing import List
from pydantic import BaseModel, Field


class Question(BaseModel):
	index: List[str] = Field(description="An index of answers denoted by consecutive letters. There are as many letters as there are answers to a given question")
	question_text: str = Field(description="The question")
	answers: List[str] = Field(description="A list of four answers to the question. Three are incorrect and one is correct")
	correct_answer_index: str = Field(description="Index of correct answer - one letter")


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


class QuizAssessement(BaseModel):
	assessement: str = Field(description="Quiz final assessment. The score in exactly number_of_correct_questions/format number_of_questions format. No spaces, no words")




