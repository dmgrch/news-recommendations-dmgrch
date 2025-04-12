import os
import string
import nltk  # type: ignore
import pymorphy3  # type: ignore


from nltk.corpus import stopwords  # type: ignore
from bottle import route, run, template, request, redirect, TEMPLATE_PATH  # type: ignore
from scraputils import get_news
from db import News, session
from bayes import NaiveBayesClassifier

TEMPLATE_PATH.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "views")))
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
    s = session()
    rows = s.query(News).filter(News.label == None).all()
    s.close()
    return template("news_template", rows=rows)


@route("/add_label/")
def add_label():
    """Allows you to label news"""
    s = session()
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
    s.close()

    if __name__ == "__main__":
        redirect("/news")


@route("/update")
def update_news():
    """Checks if new news has appeared and if so, adds it to the database"""
    s = session()
    for row in get_news("https://habr.com/ru/articles/", 15):
        existing_news = s.query(News).filter(News.author == row["author"], News.title == row["title"]).first()
        if not existing_news:
            news = News(
                title=row["title"],
                author=row["author"],
                url=row["url"],
                complexity=row["complexity"],
                habr_id=row.get("id"),
                label=None,
            )
            s.add(news)
            s.commit()
    s.close()

    if __name__ == "__main__":
        redirect("/news")


def classify_news():
    """Tags unlabeled news"""
    # Обучение модели
    s = session()
    rows = s.query(News).filter(News.label != None).all()

    X = clean_text(
        [
            row.title + " " + (row.author if row.author else "") + " " + (row.complexity if row.complexity else "")
            for row in rows
        ]
    )
    y = [row.label for row in rows]

    model = NaiveBayesClassifier(0.05)
    model.fit(X, y)

    # Предсказание меток неразмеченных новостей и их ранжирование
    rows = s.query(News).filter(News.label == None).all()

    X = clean_text(
        [
            row.title + " " + (row.author if row.author else "") + " " + (row.complexity if row.complexity else "")
            for row in rows
        ]
    )

    preds = model.predict(X)

    for news, pred in zip(rows, preds):
        news.pred_label = pred

    label_priority = {"good": 0, "maybe": 1, "never": 2}
    sorted_rows = sorted(rows, key=lambda x: label_priority[x.pred_label])

    s.close()

    return sorted_rows


@route("/recommendations")
def recommendations():
    """Displays news as a ranked list"""
    classified_news = classify_news()

    for news in classified_news:
        if news.pred_label == "good":
            news.pred_label = "Интересно"
        elif news.pred_label == "maybe":
            news.pred_label = "Возможно интересно"
        else:
            news.pred_label = "Не интересно"

    return template("news_recommendations", rows=classified_news)


if __name__ == "__main__":
    run(host="localhost", port=8080, debug=True)
