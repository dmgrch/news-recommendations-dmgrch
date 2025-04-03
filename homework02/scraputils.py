import requests
from bs4 import BeautifulSoup


def extract_news(parser):
    """Extract news from a given web page"""
    news_list = []
    articles = parser.find_all("article", class_="tm-articles-list__item")

    for article in articles:
        if article.find("span", class_="tm-article-complexity__label"):
            complexity = article.find("span", class_="tm-article-complexity__label").text
        else:
            complexity = None

        if article.find("a", class_="tm-user-info__username"):
            user = article.find("a", class_="tm-user-info__username").text
        else:
            user = None

        if article.find("a", class_="tm-title__link"):
            link = "https://habr.com" + article.find("a", class_="tm-title__link")["href"]
        else:
            continue

        news_list.append(
            {
                "author": user,
                "complexity": complexity,
                "id": article["id"],
                "link": link,
                "title": article.find("a", class_="tm-title__link").text,
            }
        )
    return news_list


def extract_next_page(parser):
    """Extract next page URL"""
    link = parser.find_all("a", class_="tm-pagination__navigation-link tm-pagination__navigation-link_active")[-1][
        "href"
    ]
    return link


def get_news(url, n_pages=1):
    """Collect news from a given web page"""
    news = []
    while n_pages:
        print("Collecting data from page: {}".format(url))
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = extract_news(soup)
        next_page = extract_next_page(soup)
        url = "https://habr.com" + next_page
        news.extend(news_list)
        n_pages -= 1
    return news
