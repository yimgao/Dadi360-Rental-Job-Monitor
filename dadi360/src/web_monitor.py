from flask import Flask, request, render_template_string
import threading
import time
from rental.rental import fetch_html, parse_html_for_listings, filter_new_listings, format_email_body, send_email, fetch_listing_description

app = Flask(__name__)

# In-memory store for user jobs (for demo)
user_jobs = {}

HTML_FORM = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Rental Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f7f7f7; }
        .container { max-width: 400px; margin: 60px auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px #ccc; }
        h2 { text-align: center; }
        label { display: block; margin-top: 15px; }
        input, textarea { width: 100%; padding: 8px; margin-top: 5px; border-radius: 4px; border: 1px solid #ccc; }
        button { margin-top: 20px; width: 100%; padding: 10px; background: #007bff; color: #fff; border: none; border-radius: 4px; font-size: 16px; }
        .msg { margin-top: 20px; color: green; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Rental Monitor</h2>
        <form method="post" action="/start">
            <label for="email">Your Email:</label>
            <input type="email" id="email" name="email" required>
            <label for="keywords">Keywords (comma separated):</label>
            <textarea id="keywords" name="keywords" rows="2" required>2房一厅,两房一厅</textarea>
            <button type="submit">Start Monitoring</button>
        </form>
        {% if msg %}<div class="msg">{{ msg }}</div>{% endif %}
    </div>
</body>
</html>
'''

def monitor_job(email, keywords, interval=600):
    # Use a simple config for each user
    config = {
        "TARGET_URL_BASE": "https://c.dadi360.com/c/forums/show//87.page",
        "NUM_PAGES_TO_SCRAPE": 5,
        "SEARCH_TERMS": [k.strip() for k in keywords.split(",") if k.strip()],
        "EMAIL": {
            "SENDER_EMAIL": "g1097420948@gmail.com",  # You can change this
            "SENDER_PASSWORD": "yjfj mcsk oinl tsxv",  # Your Gmail app password
            "RECEIVER_EMAIL": email,
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": 587
        },
        "HEADERS": {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Connection': 'keep-alive'
        }
    }
    sent_ids = set()
    while True:
        all_raw_listings = []
        for page_num in range(1, config["NUM_PAGES_TO_SCRAPE"] + 1):
            if page_num == 1:
                page_url = config['TARGET_URL_BASE']
            else:
                offset = (page_num - 1) * 90
                page_url = f"https://c.dadi360.com/c/forums/show/{offset}/87.page"
            html_content = fetch_html(page_url, config["HEADERS"])
            if html_content:
                listings_on_page = parse_html_for_listings(
                    html_content, config["TARGET_URL_BASE"], config["SEARCH_TERMS"]
                )
                all_raw_listings.extend(listings_on_page)
            time.sleep(2)
        new_listings, sent_ids = filter_new_listings(all_raw_listings, sent_ids)
        for listing in new_listings:
            listing['desc'] = fetch_listing_description(listing['link'], config["HEADERS"])
        if new_listings:
            subject, body = format_email_body(new_listings, config["SEARCH_TERMS"])
            send_email(config["EMAIL"], subject, body)
        time.sleep(interval)

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_FORM)

@app.route('/start', methods=['POST'])
def start():
    email = request.form['email']
    keywords = request.form['keywords']
    # Start a background thread for this user
    if email in user_jobs:
        msg = "You are already being monitored!"
    else:
        t = threading.Thread(target=monitor_job, args=(email, keywords), daemon=True)
        t.start()
        user_jobs[email] = t
        msg = f"Started monitoring for {email}! You will receive emails when new listings are found."
    return render_template_string(HTML_FORM, msg=msg)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 