from flask import Flask, request, render_template
import mysql.connector
import re

app = Flask(__name__)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='rajipo@#1711',
        database='student_db'
    )

# NLP Query Parsing
def parse_query(user_query):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check for score queries
    match = re.search(r'(more than|less than|between) (\d+)(?: and (\d+))? in (math|physics|chemistry)', user_query)
    if match:
        condition, score1, score2, subject = match.groups()
        subject_column = subject + '_score'

        if condition == 'more than':
            cursor.execute(f"SELECT * FROM students WHERE {subject_column} > %s", (score1,))
        elif condition == 'less than':
            cursor.execute(f"SELECT * FROM students WHERE {subject_column} < %s", (score1,))
        elif condition == 'between' and score2:
            cursor.execute(f"SELECT * FROM students WHERE {subject_column} BETWEEN %s AND %s", (score1, score2))

        result = cursor.fetchall()
        conn.close()
        return result

    # Check for name starting condition
    match = re.search(r'starts with \"(.*?)\"', user_query)
    if match:
        start_letter = match.group(1)
        cursor.execute("SELECT * FROM students WHERE name LIKE %s", (start_letter + '%',))
        result = cursor.fetchall()
        conn.close()
        return result

    # Alphabetical range for names
    match = re.search(r'names between \"(.*?)\" and \"(.*?)\"', user_query)
    if match:
        start_letter, end_letter = match.groups()
        cursor.execute("SELECT * FROM students WHERE name >= %s AND name <= %s", (start_letter, end_letter))
        result = cursor.fetchall()
        conn.close()
        return result

    # Counting queries
    match = re.search(r'count students with (more than|less than) (\d+) in (math|physics|chemistry)', user_query)
    if match:
        condition, score, subject = match.groups()
        subject_column = subject + '_score'
        if condition == 'more than':
            cursor.execute(f"SELECT COUNT(*) as count FROM students WHERE {subject_column} > %s", (score,))
        elif condition == 'less than':
            cursor.execute(f"SELECT COUNT(*) as count FROM students WHERE {subject_column} < %s", (score,))

        result = cursor.fetchone()
        conn.close()
        return [{"count": result["count"]}]

    # Sorting queries
    match = re.search(r'sort by (name|math|physics|chemistry) (ascending|descending)', user_query)
    if match:
        field, order = match.groups()
        if field in ['math', 'physics', 'chemistry']:
            field += '_score'
        order = 'ASC' if order == 'ascending' else 'DESC'
        cursor.execute(f"SELECT * FROM students ORDER BY {field} {order}")
        result = cursor.fetchall()
        conn.close()
        return result

    # Average score queries
    match = re.search(r'average score in (math|physics|chemistry)', user_query)
    if match:
        subject = match.group(1) + '_score'
        cursor.execute(f"SELECT AVG({subject}) as average FROM students")
        result = cursor.fetchone()
        conn.close()
        return [{"average": result["average"]}]

    # Maximum or minimum score queries
    match = re.search(r'(highest|lowest) score in (math|physics|chemistry)', user_query)
    if match:
        agg_function, subject = match.groups()
        subject_column = subject + '_score'
        agg_function = 'MAX' if agg_function == 'highest' else 'MIN'
        cursor.execute(f"SELECT {agg_function}({subject_column}) as result FROM students")
        result = cursor.fetchone()
        conn.close()
        return [{"result": result["result"]}]

    # Wildcard search: names containing specific substrings
    match = re.search(r'names containing \"(.*?)\"', user_query)
    if match:
        substring = match.group(1)
        cursor.execute("SELECT * FROM students WHERE name LIKE %s", ('%' + substring + '%',))
        result = cursor.fetchall()
        conn.close()
        return result

    # Pass/Fail classification
    match = re.search(r'(pass|fail) students in (math|physics|chemistry) with threshold (\d+)', user_query)
    if match:
        classification, subject, threshold = match.groups()
        subject_column = subject + '_score'
        if classification == 'pass':
            cursor.execute(f"SELECT * FROM students WHERE {subject_column} >= %s", (threshold,))
        else:
            cursor.execute(f"SELECT * FROM students WHERE {subject_column} < %s", (threshold,))
        result = cursor.fetchall()
        conn.close()
        return result

    # Multi-condition query: e.g., "more than 50 in math and starts with 'A'"
    match = re.search(r'more than (\d+) in (math|physics|chemistry) and starts with \"(.*?)\"', user_query)
    if match:
        score, subject, start_letter = match.groups()
        subject_column = subject + '_score'
        cursor.execute(f"SELECT * FROM students WHERE {subject_column} > %s AND name LIKE %s", (score, start_letter + '%'))
        result = cursor.fetchall()
        conn.close()
        return result

    conn.close()
    return [{"error": "Invalid query. Please try again with supported queries."}]

@app.route('/', methods=['GET', 'POST'])
def index():
    result = []
    if request.method == 'POST':
        user_query = request.form['query']
        result = parse_query(user_query)
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
