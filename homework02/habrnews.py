import string
import nltk  # type: ignore
import pymorphy3  # type: ignore


from nltk.corpus import stopwords  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore
from sklearn.naive_bayes import MultinomialNB  # type: ignore
from sklearn.pipeline import Pipeline  # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
from bottle import route, run, template, request, redirect  # type: ignore
from scraputils import get_news
from db import News, session
from bayes import NaiveBayesClassifier


nltk.download("stopwords")


def clean_text(text):
    """Clears text from punctuation marks and numbers, lemanticizes it"""
    morph = pymorphy3.MorphAnalyzer()
    stop_words = set(stopwords.words("russian"))

    sym_to_del = string.punctuation + "«»—–_#()" + string.digits
    translator = str.maketrans("", "", sym_to_del)

    res = []
    clean_rows = [el.translate(translator).lower().strip() for el in text]
    for row in clean_rows:
        clean_row = " ".join([morph.parse(word)[0].normal_form for word in row.split() if word not in stop_words])
        res.append(clean_row)
    return res


@route("/")
@route("/news")
def news_list():
    """Lists all unlabeled news"""
    with session() as s:
        rows = s.query(News).filter(News.label == None).all()
    return template("news_template", rows=rows)


@route("/add_label/")
def add_label():
    """Allows you to label news"""
    with session() as s:
        label = request.query.label
        news_id = request.query.id

        news = s.query(News).get(news_id)

        if label == "good":
            news.label = "good"
        elif label == "maybe":
            news.label = "maybe"
        elif label == "never":
            news.label = "never"

        s.commit()

    if __name__ == "__main__":
        redirect("/news")


@route("/update")
def update_news():
    """Checks if new news has appeared and if so, adds it to the database"""
    with session() as s:
        for row in get_news("https://habr.com/ru/articles/", 15):
            existing_news = s.query(News).filter_by(title=row["title"], author=row["author"]).first()
            if not existing_news:
                news = News(
                    title=row["title"],
                    author=row["author"],
                    url=row["link"],
                    complexity=row["complexity"],
                    habr_id=row["id"],
                    label=None,
                )
                s.add(news)
                s.commit()

    if __name__ == "__main__":
        redirect("/news")


@route("/classify")
def classify_news():
    """Tags unlabeled news and displays them as a ranked list"""
    # Обучение модели и проверка работоспособности в сравнении с MultinomialNB из sklearn
    with session() as s:
        rows = s.query(News).filter(News.label != None).all()

    X = clean_text(
        [
            row.title + " " + (row.author if row.author else "") + " " + (row.complexity if row.complexity else "")
            for row in rows
        ]
    )
    y = [row.label for row in rows]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    model = NaiveBayesClassifier(0.05)
    model.fit(X_train, y_train)
    my_accuracy = model.score(X_test, y_test)

    sk_model = Pipeline(
        [
            ("vectorizer", TfidfVectorizer()),
            ("classifier", MultinomialNB(alpha=0.05)),
        ]
    )
    sk_model.fit(X_train, y_train)
    sk_accuracy = sk_model.score(X_test, y_test)

    print("Алгоритмы обучились")
    print(f"Accuracy NaiveBayesClassifier на тестовой выборке = {round(my_accuracy, 2)}")
    print(f"Accuracy MultinomialNB на тестовой выборке = {round(sk_accuracy, 2)}")

    # Предсказание меток неразмеченных новостей
    with session() as s:
        rows = s.query(News).filter(News.label == None).all()

    X = clean_text(
        [
            row.title + " " + (row.author if row.author else "") + " " + (row.complexity if row.complexity else "")
            for row in rows
        ]
    )
    preds = model.predict(X)
    labels = ["Интересно" if i == "good" else "Возможно интересно" if i == "maybe" else "Не интересно" for i in preds]

    sorted_data = list(zip(labels, rows))
    sorted_data.sort(key=lambda x: ["Интересно", "Возможно интересно", "Не интересно"].index(x[0]))

    labels_sorted, rows_sorted = zip(*sorted_data)
    labels_sorted = list(labels_sorted)
    rows_sorted = list(rows_sorted)

    classified_news = []
    for i, row in enumerate(rows_sorted):
        classified_news.append([row.title, row.author, row.url, row.complexity, labels_sorted[i]])

    return template("news_recommendations", rows=classified_news)


if __name__ == "__main__":
    run(host="localhost", port=8080, debug=True)
