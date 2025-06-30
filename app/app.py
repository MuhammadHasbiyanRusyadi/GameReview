from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
import os
import psycopg2
from psycopg2 import extras
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def get_db_connection():
    conn = None
    retries = 5
    delay = 3

    for i in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT
            )
            print(f"Successfully connected to database on attempt {i+1}.")
            return conn
        except psycopg2.OperationalError as e:
            print(f"Database connection attempt {i+1}/{retries} failed: {e}")
            if i < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Could not connect to database.")
                if conn:
                    conn.close()
                abort(500, description=f"Database connection error: {e}. Please ensure the database service is running and accessible.")
        except Exception as e:
            print(f"An unexpected error occurred during database connection: {e}")
            if conn:
                conn.close()
            abort(500, description=f"Unexpected database connection error: {e}.")

    abort(500, description="Failed to connect to database after multiple retries.")


def init_db():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS game_reviews (
                id SERIAL PRIMARY KEY,
                game_name VARCHAR(255) NOT NULL,
                review_text TEXT,
                image_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        print("Database 'game_reviews' table initialized or already exists.")
    except Exception as e:
        print(f"Error initializing database table: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

with app.app_context():
    init_db()

def get_review(review_id):
    conn = None
    cur = None
    review = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SELECT * FROM game_reviews WHERE id = %s', (review_id,))
        review = cur.fetchone()
    except Exception as e:
        print(f"Error fetching review {review_id}: {e}")
        flash('Terjadi kesalahan saat mengambil ulasan.', 'error')
        abort(500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    if review is None:
        flash(f'Ulasan dengan ID {review_id} tidak ditemukan!', 'error')
        abort(404)
    return review

@app.route('/')
def index():
    conn = None
    cur = None
    game_reviews = []
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute('SELECT * FROM game_reviews ORDER BY created_at DESC')
        game_reviews = cur.fetchall()
    except Exception as e:
        print(f"Error fetching game reviews list: {e}")
        flash('Terjadi kesalahan saat memuat daftar ulasan game.', 'error')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return render_template('index.html', game_reviews=game_reviews)

@app.route('/create_review', methods=('GET', 'POST'))
def create_review():
    if request.method == 'POST':
        game_name = request.form['game_name']
        review_text = request.form['review_text']
        image_url = request.form['image_url']

        if not game_name:
            flash('Nama Game wajib diisi!', 'error')
        else:
            conn = None
            cur = None
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('INSERT INTO game_reviews (game_name, review_text, image_url) VALUES (%s, %s, %s)',
                            (game_name, review_text, image_url))
                conn.commit()
                flash('Ulasan game berhasil dibuat!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                print(f"Error creating game review: {e}")
                flash('Terjadi kesalahan saat membuat ulasan game.', 'error')
                if conn:
                    conn.rollback()
            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()
    return render_template('create_review.html')

@app.route('/<int:id>/edit_review', methods=('GET', 'POST'))
def edit_review(id):
    review = get_review(id)

    if request.method == 'POST':
        game_name = request.form['game_name']
        review_text = request.form['review_text']
        image_url = request.form['image_url']

        if not game_name:
            flash('Nama Game wajib diisi!', 'error')
        else:
            conn = None
            cur = None
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE game_reviews SET game_name = %s, review_text = %s, image_url = %s WHERE id = %s',
                            (game_name, review_text, image_url, id))
                conn.commit()
                flash('Ulasan game berhasil diperbarui!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                print(f"Error updating game review {id}: {e}")
                flash('Terjadi kesalahan saat memperbarui ulasan game.', 'error')
                if conn:
                    conn.rollback()
            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()
    return render_template('edit_review.html', review=review)

@app.route('/<int:id>/delete_review', methods=('POST',))
def delete_review(id):
    get_review(id)
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM game_reviews WHERE id = %s', (id,))
        conn.commit()
        flash('Ulasan game berhasil dihapus!', 'success')
    except Exception as e:
        print(f"Error deleting game review {id}: {e}")
        flash('Terjadi kesalahan saat menghapus ulasan game.', 'error')
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)