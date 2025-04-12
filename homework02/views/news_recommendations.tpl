<!-- news_template.tpl -->
<!DOCTYPE html>
<html>
    <head>
        <link rel="stylesheet" href="//cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.12/semantic.min.css"></link>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.12/semantic.min.js"></script>
    </head>
    <body>
        <div class="ui container" style="padding-top: 10px;">
        <tr>
            <th colspan="14">
                <div style="display: flex; justify-content: space-between;">
                    <a href="/news" class="ui small primary button">Все новые новости</a>
                </div>
            </th>
        </tr>
        <table class="ui celled table">
            <thead>
                <th>Название</th>
                <th>Автор</th>
                <th>Сложность</th>
                <th colspan="3">Рекомендация ИИ</th>
            </thead>
            <tbody>
                %for row in rows:
                <tr>
                    <td><a href="{{ row.url }}">{{ row.title }}</a></td>
                    <td>{{ row.author }}</td>
                    <td>{{ row.complexity }}</td>
                    <td>{{ row.pred_label }}</td>
                </tr>
                %end
            </tbody>
            <tfoot class="full-width">
            </tfoot>
        </table>
        </div>
    </body>
</html>
