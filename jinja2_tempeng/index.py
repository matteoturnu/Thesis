from flask import Flask, request, render_template_string

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username', '')
        # template = "Welcome, {{ %s }}!" % username
        template = "Welcome, {{" + username + "}}"
        return render_template_string(template)

    # Show form on GET request
    return '''
    <!doctype html>
    <html>
      <head><title>Welcome Form</title></head>
      <body>
        <form method="POST">
          <label for="username">Enter your name:</label>
          <input type="text" name="username" id="username" />
          <input type="submit" value="Submit" />
        </form>
      </body>
    </html>
    '''


if __name__ == '__main__':
    app.run(debug=True)