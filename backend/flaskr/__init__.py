import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from sqlalchemy.sql.expression import func

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
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS')
        return response

    """
    @TODO:
    An endpoint to handle GET requests
    for all available categories.
    This endpoint returns a key(id),value(name) pair
    for each category.
    """
    @app.route('/categories', methods=['GET'])
    def get_categories():
        try:
            selection = Category.query.order_by(Category.id).all()
            categories = {}
            for category in selection:
                categories[category.id] = category.type

            if len(selection) == 0:
                abort(404)

            return jsonify({
                "categories": categories
            }), 200
        except:
            abort(422)

    """
    @TODO:
    An endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint returns a list of questions,
    number of total questions, current category, categories. 
    This endpoint includes a helper function to format the
    categories in key value pairs and return them for json output.
    """
    def return_categories():
        selection = Category.query.order_by(Category.id).all()
        categories = {}
        for category in selection:
            categories[category.id] = category.type
        return categories

    @app.route('/questions', methods=['GET'])
    def get_questions():
        try:
            items_limit = request.args.get('limit', 10, type=int)
            page = request.args.get("page", 1, type=int)
            start = (page - 1)
            end = start + QUESTIONS_PER_PAGE

            selection = Question.query.order_by(Question.id).limit(items_limit).offset(start * items_limit).all()

            questions = [question.format() for question in selection]
            current_questions = questions[start:end]

            if len(current_questions) == 0:
                abort(404)

            return jsonify({
                "questions": current_questions,
                "total_questions": len(selection),
                "categories": return_categories(),
                "current_category": request.args.get("category", 1, type=int)
            }), 200
        except:
            abort(422)

    """
    @TODO:
    An endpoint to DELETE question using a question ID.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.filter(Question.id == question_id).one_or_none()

        if question is None:
            abort(404)

        try:
            question.delete()

            return jsonify({
                       "success": True,
                       "question_deleted": question_id
                   }), 200

        except:
            abort(422)

    """
    @TODO:
    An endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.
    """
    @app.route('/questions', methods=['POST'])
    def post_question():
        body = request.get_json()
        num_params = len(body)

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
    A POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.
    """
    def get_question_by_search(body):
        search_term = body.get("searchTerm", None)

        try:
            selection = Question.query.filter(Question.question.contains(search_term))
            questions = [question.format() for question in selection]

            return jsonify({
                "questions": questions,
                "total_questions": len(questions)
            }), 200

        except:
            abort(422)

    """
    @TODO:
    A GET endpoint to get questions based on category.
    """
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_question_by_category(category_id):
        try:
            category = Category.query.filter(Category.id == category_id).one_or_none()
            if category is None:
                abort(404)

            name_of_category = category.type

            selection = Question.query.filter(Question.category == str(category_id))

            if selection is None:
                abort(404)

            questions = [question.format() for question in selection]

            return jsonify({
                       "questions": questions,
                       "total_questions": len(questions),
                       "current_category": name_of_category
                   }), 200

        except:
            abort(422)

    """
    @TODO:
    A POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.
    """
    @app.route('/quizzes', methods=['POST'])
    def play_trivia():
        body = request.get_json()
        previous_questions = body.get("previous_questions", [])
        quiz_category = body.get("quiz_category", {})
        category_id = quiz_category.get("id", 0)

        if category_id is None:
            abort(404)

        if quiz_category and (category_id != 0):
            selection = Question.query.filter(Question.category == category_id).order_by(func.random()).all()
        else:
            selection = Question.query.order_by(func.random()).all()

        if selection is None:
            abort(404)

        try:
            questions = [question.format() for question in selection]
            options = [x for x in questions if x.get("id") not in previous_questions]

            if not options:
                return jsonify({
                    "message": "No more questions for this category."
                }), 200

            quiz_question = random.choice(options)

            return jsonify({
                        "question": quiz_question
                   }), 200

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
            jsonify({"success": False, "error": 404, "message": "Question or Category not found."}),
            404,
        )

    @app.errorhandler(422)
    def not_processable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "The request could not be processed."}),
            422,
        )

    @app.errorhandler(400)
    def empty_search(error):
        return (
            jsonify({"success": False, "error": 400, "message": "Incorrect amount of parameters in request."}),
            400,
        )

    @app.errorhandler(412)
    def invalid_syntax(error):
        return (
            jsonify({"success": False, "error": 412, "message": "Invalid syntax on new question parameters."}),
            412,
        )

    @app.errorhandler(500)
    def internal_error(error):
        return (
            jsonify({"success": False, "error": 500, "message": "Something's wrong on our end, try back soon."}),
            500,
        )

    return app
