import http.server
import socketserver
from datetime import datetime
from openai import OpenAI
import cgi
import requests
import os
import json
import threading

# -_- < zzz.....

client = OpenAI(api_key="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")

LISTEN_PORT = 8080
STATIC_DIR = "static"


class ServerHandler(http.server.SimpleHTTPRequestHandler):
    def translate_and_generate_prompt(self, text):
        # 日本語のテキストを英語に翻訳するためのプロンプトを作成
        translation_messages = [
            {
                "role": "system",
                "content": "Translate the following Japanese text to English.",
            },
            {"role": "user", "content": text},
        ]

        try:
            # GPT-4を使用して翻訳
            translation_response = client.chat.completions.create(
                model="gpt-4-1106-preview", messages=translation_messages, temperature=0
            )
            translated_text = translation_response.choices[0].message.content.strip()

            # ユーザーの入力に基づいて連想されるアイデアを生成するためのプロンプトを作成
            idea_messages = [
                {
                    "role": "system",
                    "content": "Summarize and generate associated keywords from the following text.",
                },
                {"role": "user", "content": translated_text},
            ]

            # GPT-4を使用して関連アイデアを生成
            idea_response = client.chat.completions.create(
                model="gpt-4-1106-preview", messages=idea_messages, temperature=0.3
            )
            related_ideas = idea_response.choices[0].message.content.strip()

            # 今日の日付を取得してフォーマットする
            today_date = datetime.now().strftime("%Y-%m-%d")

            # 翻訳したテキスト、関連アイデア、日付を組み合わせたプロンプトを作成
            full_prompt = f"{translated_text}, {related_ideas}, {today_date},real, Japan, masterpeace"
            return full_prompt
        except Exception as e:
            print(f"翻訳エラー: {e}")
            return None

    # 占いデータをHTMLに整形する関数
    def format_horoscope(self, horoscope_data, today):
        html_content = '<div class="horoscope">'
        for index, sign in enumerate(horoscope_data["horoscope"][today]):
            modal_id = f"horoscopeModal-{index}"

            # 星座のタイトルをdivタグで囲む
            html_content += f"""
                <div class="horoscope-title">
                    <a href="#" data-toggle="modal" data-target="#{modal_id}" class="horoscope-link">{sign["sign"]}</a>
                </div>
            """

        # モーダルのコンテンツ

    def format_horoscope(self, horoscope_data, today):
        html_content = '<div class="horoscope">'
        for index, sign in enumerate(horoscope_data["horoscope"][today]):
            modal_id = f"horoscopeModal-{index}"

            # 星座のタイトルとモーダルを開くためのリンク
            html_content += f"""
                <div class="horoscope-title">
                    <a href="#" data-toggle="modal" data-target="#{modal_id}" class="horoscope-link">{sign["sign"]}</a>
                </div>
            """

            # モーダルのコンテンツ
            html_content += f"""
                <div class="modal fade" id="{modal_id}" tabindex="-1" role="dialog" aria-labelledby="{modal_id}Label" aria-hidden="true">
                    <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable" role="document">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="{modal_id}Label">{sign['sign']}</h5>
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                <p>{sign['content']}</p>
                                <p>ラッキーアイテム: {sign['item']}</p>
                                <p>ラッキーカラー: {sign['color']}</p>
                                <p>総合運: {sign['total']} / 恋愛運: {sign['love']}</p>
                            </div>
                            <div class="modal-footer">
                                <div class="horoscope-footer" style="font-size: small;">
                                    【PR】<a href="http://www.tarim.co.jp/">原宿占い館 塔里木</a><br>
                                    Powered by <a href="http://jugemkey.jp/api/">JugemKey</a>
                                </div>
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">閉じる</button>
                            </div>
                        </div>
                    </div>
                </div>
            """
        html_content += "</div>"
        return html_content

    def do_GET(self):
        if self.path == "/":
            # 今日の日付を取得
            today = datetime.now().strftime("%Y/%m/%d")
            year, month, day = today.split("/")

            # 占いAPIのURLを構築
            horoscope_url = (
                f"http://api.jugemkey.jp/api/horoscope/free/{year}/{month}/{day}"
            )

            # 占いAPIからデータを取得
            horoscope_response = requests.get(horoscope_url)
            horoscope_html = ""
            if horoscope_response.status_code == 200:
                horoscope_data = horoscope_response.json()
                # 占いデータをHTMLに整形
                horoscope_html = self.format_horoscope(horoscope_data, today)
            else:
                horoscope_html = "<p>占いデータの取得に失敗しました。</p>"

            # 天気情報のAPIからデータを取得
            weather_response = requests.get(
                "https://weather.tsukumijima.net/api/forecast/city/130010"
            )
            weather_data = weather_response.json()

            # 天気情報の抽出
            (
                today_forecast,
                tomorrow_forecast,
                day_after_tomorrow_forecast,
            ) = weather_data["forecasts"][0:3]

            def safe_replace(string, old, new):
                """安全に文字列の置換を行う関数。Noneの場合は空文字を返す"""
                if string is not None:
                    return string.replace(old, new)
                return ""

            # 天気情報の抽出時の処理を変更
            today_wind = safe_replace(today_forecast["detail"]["wind"], "後", "のち")
            tomorrow_wind = safe_replace(tomorrow_forecast["detail"]["wind"], "後", "のち")
            day_after_tomorrow_wind = safe_replace(
                day_after_tomorrow_forecast["detail"]["wind"], "後", "のち"
            )

            today_min_temp = today_forecast["temperature"]["min"]["celsius"] or "-"
            today_max_temp = today_forecast["temperature"]["max"]["celsius"] or "-"
            tomorrow_min_temp = (
                tomorrow_forecast["temperature"]["min"]["celsius"] or "-"
            )
            tomorrow_max_temp = (
                tomorrow_forecast["temperature"]["max"]["celsius"] or "-"
            )
            day_after_tomorrow_min_temp = (
                day_after_tomorrow_forecast["temperature"]["min"]["celsius"] or "-"
            )
            day_after_tomorrow_max_temp = (
                day_after_tomorrow_forecast["temperature"]["max"]["celsius"] or "-"
            )

            # 名言情報のAPIからデータを取得
            meigen_response = requests.get(
                "https://meigen.doodlenote.net/api/json.php?c=1"
            )
            meigen_data = meigen_response.json()

            # 名言と著者を抽出
            meigen = meigen_data[0]["meigen"]
            auther = meigen_data[0]["auther"]

            # HTMLテンプレートファイルを読み込む
            with open("template.html", "r", encoding="utf-8") as file:
                html_template = file.read()

            # テンプレートをデータで埋める
            html_content = html_template.format(
                today_date=today_forecast["date"],
                today_telop=today_forecast["telop"],
                today_wind=today_wind,
                today_min_temp=today_min_temp,  # 今日の最低気温
                today_max_temp=today_max_temp,
                today_weather_image_url=today_forecast["image"]["url"],  # 今日の天気画像URL
                tomorrow_date=tomorrow_forecast["date"],
                tomorrow_telop=tomorrow_forecast["telop"],
                tomorrow_wind=tomorrow_wind,
                tomorrow_min_temp=tomorrow_min_temp,  # 明日の最低気温
                tomorrow_max_temp=tomorrow_max_temp,
                tomorrow_weather_image_url=tomorrow_forecast["image"][
                    "url"
                ],  # 明日の天気画像URL
                day_after_tomorrow_date=day_after_tomorrow_forecast["date"],
                day_after_tomorrow_telop=day_after_tomorrow_forecast["telop"],
                day_after_tomorrow_wind=day_after_tomorrow_wind,
                day_after_tomorrow_min_temp=day_after_tomorrow_min_temp,  # 明後日の最低気温
                day_after_tomorrow_max_temp=day_after_tomorrow_max_temp,
                day_after_tomorrow_weather_image_url=day_after_tomorrow_forecast[
                    "image"
                ][
                    "url"
                ],  # 明後日の天気画像URL
                meigen=meigen,
                auther=auther,
                horoscope_html=horoscope_html,
            )

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
        elif self.path == "/style.css":
            # Serve the CSS file
            try:
                with open("style.css", "r", encoding="utf-8") as file:
                    css_content = file.read()
                self.send_response(200)
                self.send_header("Content-type", "text/css; charset=utf-8")
                self.end_headers()
                self.wfile.write(css_content.encode("utf-8"))
            except FileNotFoundError:
                # If style.css not found
                self.send_error(404, "File Not Found: style.css")
        elif self.path == "/script.js":
            # Serve the JavaScript file
            try:
                with open("script.js", "r", encoding="utf-8") as file:
                    js_content = file.read()
                self.send_response(200)
                self.send_header(
                    "Content-type", "application/javascript; charset=utf-8"
                )
                self.end_headers()
                self.wfile.write(js_content.encode("utf-8"))
            except FileNotFoundError:
                # If script.js not found
                self.send_error(404, "File Not Found: script.js")

    def do_POST(self):
        if self.path == "/generate_image":
            # JSON形式のリクエストデータを解析
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data)

            user_input = request_data.get("userInput", "")
            beauty_mode = request_data.get("beautyMode", False)

            if beauty_mode:
                user_input += "追加のキーワード"

            # 画像生成処理を実行
            image_url = self.generate_image(user_input)

            # レスポンスを送信
            self.send_image_response(image_url)

    def generate_image_async(self, user_input):
        # 新しいスレッドで画像生成を実行
        image_url = None
        thread = threading.Thread(target=lambda: self.generate_image(user_input))
        thread.start()
        thread.join()  # スレッドの終了を待つ
        return image_url

    def generate_image(self, text):
        # ユーザー入力と日付を組み合わせたプロンプトを作成
        full_prompt = self.translate_and_generate_prompt(text)
        print(full_prompt)

        if full_prompt is None:
            return "翻訳またはプロンプトの生成に失敗しました。"

        try:
            # DALL-E 3を使用して画像を生成
            response = client.images.generate(
                model="dall-e-3",
                prompt=full_prompt,
                size="1024x1024",
                response_format="url",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            return image_url
        except Exception as e:
            print(f"画像生成エラー: {e}")
            return None

    def send_image_response(self, image_url):
        # ここでレスポンスをクライアントに送信
        if image_url:
            response_data = {"imageUrl": image_url}
        else:
            response_data = {"error": "Image generation failed"}

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode("utf-8"))


if __name__ == "__main__":
    HOST, PORT = "", LISTEN_PORT

    with socketserver.TCPServer((HOST, PORT), ServerHandler) as server:
        print(f"サーバーがポート {PORT} で起動しました")
        server.serve_forever()
