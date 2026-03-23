from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate

from question_structure import Quiz, UserAnswers, AIAnalyzer, QuizAssessment

MODEL = "gpt-5-mini"


def get_structured_model(model, structured_class):
	structured_model = model.with_structured_output(structured_class)
	return structured_model


def create_prompt(system_prompt: str, human_prompt: str) -> ChatPromptTemplate:
	prompt = ChatPromptTemplate.from_messages(
		[
			("system", system_prompt),
			("human", human_prompt)
		]
	)
	return prompt


def create_chain(prompt, model):
	return prompt | model


def get_model_output(bind_vars, chat_prompt):
	return chat_prompt.invoke(bind_vars)


def run_structured_prompt(model, structured_class, system_prompt, human_prompt, bind_vars):
	structured_model = get_structured_model(model=model, structured_class=structured_class)
	prompt = create_prompt(system_prompt=system_prompt, human_prompt=human_prompt)
	chat_prompt = create_chain(prompt=prompt, model=structured_model)
	answer = get_model_output(bind_vars=bind_vars, chat_prompt=chat_prompt)
	return answer


def main():
	load_dotenv()

	model = init_chat_model(model=MODEL, model_provider='openai')

	system_prompt = "You’re an expert in your field. You create engaging and educational quizzes."
	human_prompt = "Create a quiz on the topic: {topic}. Difficulty level: {difficulty}. Number of questions: {count}."
	bind_vars = {
		"topic": "Python programming language",
		"difficulty": "easy",
		"count": 5
	}

	quiz = run_structured_prompt(
		model=model,
		structured_class=Quiz,
		system_prompt=system_prompt,
		human_prompt=human_prompt,
		bind_vars=bind_vars
	)

	list_of_answers = []
	for q in quiz.questions:
		print(q.question_text)
		for i, a in zip(q.index, q.answers):
			print(f"{i}) {a}")
		while True:
			user_answer_index = input("Your answer: ").strip().upper()
			if user_answer_index in q.index:
				break
			print("Invalid input. Try again.")
		user_answers = UserAnswers(
			question=q.question_text,
			correct_answer=q.correct_answer_index,
			user_answer=user_answer_index
		)
		list_of_answers.append(user_answers)
		print()

	system_prompt = "You are responsible for compiling the answers based on the data provided."
	human_prompt = "This is the {raw_data} quiz data required for analysis"
	bind_vars = {
		"raw_data": [a.model_dump() for a in list_of_answers]
	}

	questions_analyzed = run_structured_prompt(
		model=model,
		structured_class=AIAnalyzer,
		system_prompt=system_prompt,
		human_prompt=human_prompt,
		bind_vars=bind_vars
	)

	for a in questions_analyzed.answers:
		print(a.ai_answer)

	system_prompt = "You are responsible for quiz answers final assessment"
	human_prompt = "This is the quiz analysis {quiz_analysis}. The score in exactly number_of_correct_questions/format number_of_questions format. No spaces, no words"
	bind_vars = {
		"quiz_analysis": [a.ai_answer for a in questions_analyzed.answers]
	}

	quiz_assemssment = run_structured_prompt(
		model=model,
		structured_class=QuizAssessment,
		system_prompt=system_prompt,
		human_prompt=human_prompt,
		bind_vars=bind_vars
	)

	print("Final result: ", quiz_assemssment.assessement)


if __name__ == "__main__":
	main()