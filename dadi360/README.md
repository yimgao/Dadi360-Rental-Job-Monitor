# Rental Monitor Web App

This is a Flask-based web app that lets users enter rental search keywords and their email address, then monitors https://c.dadi360.com for matching listings and sends email notifications.

## 🚀 Deploy to Render.com (Free Cloud Hosting)

### 1. Fork or Clone This Repo

Push your code to GitHub if you haven't already.

### 2. Create a `requirements.txt`

Already included:
```
flask
requests
beautifulsoup4
schedule
```

### 3. Create a Render.com Account
- Go to [https://render.com/](https://render.com/)
- Sign up and connect your GitHub account

### 4. Create a New Web Service
- Click **New Web Service**
- Select your GitHub repo
- Set the build command:
  ```
  pip install -r requirements.txt
  ```
- Set the start command:
  ```
  python src/web_monitor.py
  ```
- Choose the free plan

### 5. Configure Environment Variables (Optional)
- For production, you should use environment variables for sensitive info (like email/password)
- On Render, go to your service > Environment > Add Environment Variable

### 6. Deploy!
- Render will build and deploy your app
- You’ll get a public URL to share

## 🖥️ Usage
- Open the web app in your browser
- Enter your email and keywords (comma separated)
- Click **Start Monitoring**
- You’ll receive emails when new matching listings are found

## ⚠️ Notes
- Free Render services may sleep after 15 minutes of inactivity
- For always-on background jobs, consider Render's "Background Worker" (paid)
- For demo/testing, this setup is perfect!

## 🛠️ Local Development
```bash
pip install -r requirements.txt
python src/web_monitor.py
```
Then visit [http://localhost:5000/](http://localhost:5000/)

---

**Questions?**
Open an issue or ask your AI assistant! 