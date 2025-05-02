from flask import Flask, flash, render_template, request, redirect, url_for
from myapp.models import db, Book, User, Loan, Author, Publisher
from datetime import datetime, timedelta
from sqlalchemy import text, func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return redirect(url_for('list_books'))

@app.route('/books')
def list_books():
    books = Book.query.all()
    return render_template('list_books.html', books=books)

@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        book = Book(
            title=request.form['title'],
            genre=request.form['genre'],
            published_date=datetime.fromisoformat(request.form['published_date']),
            author_id=int(request.form['author']),
            publisher_id=int(request.form['publisher'])
        )

        db.session.add(book)
        db.session.commit()

        return redirect(url_for('list_books'))

    authors = Author.query.all()
    publishers = Publisher.query.all()
    return render_template('add_book.html', authors=authors, publishers=publishers)

@app.route('/books/edit/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    book = Book.query.get_or_404(id)

    if request.method == 'POST':
        book.title = request.form['title']
        book.genre = request.form['genre']
        book.published_date = datetime.fromisoformat(request.form['published_date'])
        
        # Check if 'author' and 'publisher' fields are not empty before converting to int
        author_id = request.form['author']
        if author_id:
            book.author_id = int(author_id)
        else:
            book.author_id = None  # Or some default value

        publisher_id = request.form['publisher']
        if publisher_id:
            book.publisher_id = int(publisher_id)
        else:
            book.publisher_id = None  # Or some default value
        
        db.session.commit()

        return redirect(url_for('list_books'))

    authors = Author.query.all()
    publishers = Publisher.query.all()
    return render_template('edit_book.html', book=book, authors=authors, publishers=publishers)


# Delete a book
@app.route('/books/delete/<int:id>', methods=['POST'])
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('list_books'))


if __name__ == '__main__':
    app.run(debug=True)


@app.route('/report/books', methods=['GET','POST'])
def book_report():
    # 1) Load dropdown lists via ORM
    authors    = Author.query.order_by(Author.name).all()
    publishers = Publisher.query.order_by(Publisher.name).all()
    genres     = [g[0] for g in db.session.query(Book.genre).distinct()]

    books       = []
    stats       = {}
    report_desc = ""

    if request.method == 'POST':
        # 2) Pull filter values
        sel_a     = request.form.get('author')       or None
        sel_p     = request.form.get('publisher')    or None
        sel_g     = request.form.get('genre')        or None
        sel_start = request.form.get('start_date')   or "1900-01-01"
        sel_end   = request.form.get('end_date')     or datetime.today().strftime("%Y-%m-%d")

        # 3) Prepared‐statement SQL
        stmt = text("""
            SELECT
              b.book_id,
              b.title,
              b.genre,
              b.published_date,
              a.author_id,
              a.name   AS author_name,
              p.publisher_id,
              p.name   AS publisher_name
            FROM books b
            JOIN authors    a ON b.author_id    = a.author_id
            JOIN publishers p ON b.publisher_id = p.publisher_id
            WHERE b.published_date BETWEEN :start AND :end
              AND (:a IS NULL OR b.author_id    = :a)
              AND (:p IS NULL OR b.publisher_id = :p)
              AND (:g IS NULL OR b.genre        = :g)
            ORDER BY b.published_date
        """)

        result = db.session.execute(stmt, {
            "start": sel_start,
            "end":   sel_end,
            "a":     sel_a,
            "p":     sel_p,
            "g":     sel_g
        })

        # 4) Map result rows into dicts, parsing published_date
        for row in result:
            m = row._mapping
            pd = m.published_date
            # if SQLite gives you a string, turn it into a datetime
            if isinstance(pd, str):
                pd = datetime.fromisoformat(pd)

            books.append({
                "book_id":        m.book_id,
                "title":          m.title,
                "genre":          m.genre,
                "published_date": pd,
                "author_id":      m.author_id,
                "author_name":    m.author_name,
                "publisher_id":   m.publisher_id,
                "publisher_name": m.publisher_name,
            })

        # 5) Compute statistics
        stats["total_books"] = len(books)
        ages = [
            (datetime.today().date() - b["published_date"].date()).days/365
            for b in books
        ]
        stats["avg_age"] = round(sum(ages)/len(ages),1) if ages else 0
        stats["distinct_authors"]    = len({b["author_id"]    for b in books})
        stats["distinct_publishers"] = len({b["publisher_id"] for b in books})

        by_genre = {}
        for b in books:
            by_genre[b["genre"]] = by_genre.get(b["genre"], 0) + 1
        stats["by_genre"] = by_genre

        dates = [b["published_date"] for b in books]
        stats["oldest"] = min(dates).strftime("%Y-%m-%d") if dates else "—"
        stats["newest"] = max(dates).strftime("%Y-%m-%d") if dates else "—"

        # 6) Build summary sentence
        parts = []
        if sel_a:
            name = next((a.name for a in authors if str(a.author_id)==sel_a), "Unknown")
            parts.append(f"by {name}")
        if sel_p:
            name = next((p.name for p in publishers if str(p.publisher_id)==sel_p), "Unknown")
            parts.append(f"from {name}")
        if sel_g:
            parts.append(f"(Genre: {sel_g})")
        if sel_start or sel_end:
            parts.append(f"published between {sel_start} and {sel_end}")

        report_desc = f"Showing {stats['total_books']} books " + " ".join(parts) + "."

    # 7) Render the template
    return render_template(
        'book_report.html',
        authors=authors,
        publishers=publishers,
        genres=genres,
        books=books,
        stats=stats,
        report_desc=report_desc
    )