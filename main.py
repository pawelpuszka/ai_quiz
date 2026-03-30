from question_structure import UserAnswers
from quiz_core import analyze_answers_ai, assess_quiz_ai, generate_quiz, init_model


def main():
	model = init_model()
	quiz = generate_quiz(model=model, topic="Python programming language", difficulty="easy", count=5)

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

	questions_analyzed = analyze_answers_ai(model=model, answers=list_of_answers)

	for a in questions_analyzed.answers:
		print(a.ai_answer)

	quiz_assessment = assess_quiz_ai(model=model, analysis=questions_analyzed)

	print("Final result: ", quiz_assessment.assessment)


if __name__ == "__main__":
	main()