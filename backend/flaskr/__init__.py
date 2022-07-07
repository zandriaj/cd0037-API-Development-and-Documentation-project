import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/categories', methods=['GET'])
    def get_categories():
        selection = Category.query.order_by(Category.id).all()
        categories = {}
        for category in selection:
            categories[category.id] = category.type

        if len(selection) == 0:
            abort(404)

        return jsonify({
            "categories": categories
        }), 200

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    def return_categories():
        selection = Category.query.order_by(Category.id).all()
        categories = {}
        for category in selection:
            categories[category.id] = category.type
        return categories

    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()

        page = request.args.get("page", 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in selection]
        current_questions = questions[start:end]

        if len(current_questions) == 0:
            abort(404)

        # question here about current category. #
        return jsonify({
            "questions": current_questions,
            "total_questions": len(selection),
            "categories": return_categories(),
            "current_category": request.args.get("category", 1, type=int)
        }), 200

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                       "success": True,
                       "question_deleted": question_id
                   }), 200

        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route('/questions', methods=['POST'])
    def post_question():
        body = request.get_json()
        num_params = len(body)
        print(num_params)

        if num_params == 4:
            return create_question(body)
        elif num_params == 1:
            return get_question_by_search(body)
        else:
            abort(400)

    def create_question(body):
        new_question = body.get("question", None)
        new_answer = body.get("answer", None)
        new_category = body.get("category", None)
        new_difficulty = body.get("difficulty", None)

        if (not new_question) or (not new_answer) or (not new_category) or (not new_difficulty):
            abort(422)

        try:
            created_question = Question(question=new_question, answer=new_answer, category=new_category,
                                        difficulty=new_difficulty)
            created_question.insert()

            return jsonify({
                       "success": True,
                       "question_created": created_question.id
                   }), 200
        except:
            abort(412)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    def get_question_by_search(body):
        search_term = body.get("searchTerm", None)

        try:
            selection = Question.query.filter(Question.question.contains(search_term))
            questions = [question.format() for question in selection]
            print(questions)

            return jsonify({
                "questions": questions,
                "total_questions": len(questions)
            }), 200

        except:
            abort(422)

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_question_by_category(category_id):
        category = Category.query.filter(Category.id == category_id).one_or_none()
        name_of_category = category.type

        try:
            selection = Question.query.filter(Question.category == category_id)
            questions = [question.format() for question in selection]
            print(questions)

            if questions is None:
                abort(404)

            return jsonify({
                       "questions": questions,
                       "total_questions": len(questions),
                       "current_category": name_of_category
                   }), 200

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quizzes', methods=['POST'])
    def play_trivia():
        body = request.get_json()
        previous_questions = body.get("previous_questions", None)
        quiz_category = body.get("quiz_category", None)

        if quiz_category:
            selection = Question.query.filter(Question.category == quiz_category.get("type"))
        else:
            selection = Question.query.all()

        try:
            found_question = False

            while not found_question:
                question = selection.query.order_by(random).limit(1)
                if question.id not in previous_questions:
                    found_question = True
                    return {
                               "question": question.format()
                           }, 200
        except:
            abort(422)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "Question or Category not found"}),
            404,
        )

    @app.errorhandler(422)
    def not_processable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "Unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def empty_search(error):
        return (
            jsonify({"success": False, "error": 400, "message": "Incorrect amount of parameters in request"}),
            400,
        )

    @app.errorhandler(412)
    def invalid_syntax(error):
        return (
            jsonify({"success": False, "error": 412, "message": "Invalid syntax on new question parameters"}),
            412,
        )

    @app.errorhandler(500)
    def internal_error(error):
        return (
            jsonify({"success": False, "error": 500, "message": "Something's wrong on our end, try back soon."}),
            500,
        )

    return app
