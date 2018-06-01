from flask import Flask, render_template, redirect

app = Flask(__name__)
app.secret_key="utu_info"
app_name = "Text Reuse in Finnish Newspapers and Journals, 1771–​1920"
port = 8983
domain = "http://comhis.fi/clusters"

@app.route("/clusters/info")
def main():
	return redirect(domain)

@app.route("/clusters/info/about")
def about():
	return render_template("about.html")

@app.route("/clusters/info/credits")
def credits():
	return render_template("credits.html")

@app.route("/clusters/info/cite")
def quote():
	return render_template("cite.html")


if __name__ == "__main__":
	app.run(host="0.0.0.0")
