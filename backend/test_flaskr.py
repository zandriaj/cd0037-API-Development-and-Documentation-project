import configparser
import os
import unittest
import json
import re

from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category, db


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client

        config = configparser.ConfigParser()
        config.read('dl.cfg')

        os.environ['DB_HOST'] = config['PSQL']['PSQL_HOST']
        os.environ['DB_USER'] = config['PSQL']['PSQL_USER']
        os.environ['DB_PSWRD'] = config['PSQL']['PSQL_PASSWORD']
        os.environ['DB_NAME'] = config['PSQL']['PSQL_DB_NAME']

        self.database_path = "postgresql://{}:{}@{}/{}".format(
            os.environ['DB_USER'], os.environ['DB_PSWRD'], os.environ['DB_HOST'], os.environ['DB_NAME']
        )

        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            # self.db = SQLAlchemy()
            db.init_app(self.app)
            # create all tables
            db.create_all()
            db.session.commit()
            categories = ["Science", "Art", "Geography", "History", "Entertainment", "Sports"]

            for category in categories:
                new_category = Category(category)
                db.session.add(new_category)
            db.session.commit()

            file_questions = open('questions.txt', 'r')
            for line in file_questions:
                questions = re.split("\t+", line)
                new_question = Question(questions[1], questions[2], int(questions[3]), int(questions[4]))
                db.session.add(new_question)
            db.session.commit()
            file_questions.close()

    def tearDown(self):
        """Executed after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.session.commit()

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """

    def test_get_categories(self):
        res = self.client().get("/categories")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["categories"])

    def test_get_questions(self):
        res = self.client().get("/questions?page=2")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["questions"])
        self.assertTrue(data["categories"])

    """
    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    def test_get_questions_422(self):
        res = self.client().get("/questions?page=1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "The request could not be processed.")

    def test_post_question_400(self):
        new_question = {"question": "Who is the president?", "answer": "Joe Biden"}
        res = self.client().post("/questions", json=new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(False, data["success"])
        self.assertEqual(data["message"], "Incorrect amount of parameters in request.")

    """
    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    def test_create_question(self):
        new_question = {"question": "Who is the president?", "answer": "Joe Biden", "category": 2, "difficulty": 2}
        res = self.client().post("/questions", json=new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(True, data["success"])
        self.assertTrue(data["question_created"])

    def test_create_question_422(self):
        new_question = {"question": "Who is the president?", "response": "Joe Biden", "category": 2, "difficulty": 2}
        res = self.client().post("/questions", json=new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(False, data["success"])
        self.assertEqual(data["message"], "The request could not be processed.")

    def test_create_question_412(self):
        new_question = {"question": "Who is the president?", "answer": "Joe Biden", "category": "History",
                        "difficulty": "Hard"}
        res = self.client().post("/questions", json=new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 412)
        self.assertEqual(False, data["success"])
        self.assertEqual(data["message"], "Invalid syntax on new question parameters.")

    """
    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    def test_get_question_by_search(self):
        search_term = {"searchTerm": "1930"}
        res = self.client().post("/questions", json=search_term)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["questions"])
        self.assertTrue(data["total_questions"])

    def test_get_question_by_search_422(self):
        search_term = {"searchWorm": "1930"}
        res = self.client().post("/questions", json=search_term)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(False, data["success"])
        self.assertEqual(data["message"], "The request could not be processed.")

    """
    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    def test_delete_question(self):
        to_delete = 2
        res = self.client().delete(f"/questions/{to_delete}")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(to_delete, data["question_deleted"])
        self.assertEqual(True, data["success"])

    def test_delete_question_404(self):
        to_delete = 100
        res = self.client().delete(f"/questions/{to_delete}")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(False, data["success"])
        self.assertEqual(data["message"], "Question or Category not found.")

    """
    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    def test_get_question_by_category(self):
        category_id = 2
        res = self.client().get(f"/categories/{category_id}/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["questions"])
        self.assertTrue(data["total_questions"])
        self.assertEqual(data["current_category"], "Art")

    def test_get_question_by_category_422(self):
        category_id = 100
        res = self.client().get(f"/categories/{category_id}/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(False, data["success"])
        self.assertEqual(data["message"], "The request could not be processed.")

    """
    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    def test_play_trivia_all(self):
        quiz_data = {"previous_questions": [16, 17]}
        res = self.client().post("/quizzes", json=quiz_data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["question"])

    def test_play_trivia_category(self):
        quiz_data = {"previous_questions": [16, 17], "quiz_category": {"type": "Art", "id": "2"}}
        res = self.client().post("/quizzes", json=quiz_data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["question"])

    def test_play_trivia_422(self):
        quiz_data = {"quiz_category": {"type": "", "id": None}}
        res = self.client().post("/quizzes", json=quiz_data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(False, data["success"])
        self.assertEqual(data["message"], "Question or Category not found.")


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
