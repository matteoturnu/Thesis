from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import spitfire
from spitfire.compiler.util import load_template



class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse URL parameters
        query = urlparse(self.path).query
        params = parse_qs(query)
        name = params.get("name", [""])[0]
        print("Name parameter: ", name)

        try:
            # Render the template
            if name != "":
                new_template = "<h1>Welcome, %s</h1>" % name
                print("Template: ", new_template)
                with open("templates/welcome.spf", "w") as f:
                    f.write(new_template)
                env.load_dir()
                #response = env.render_template("templates\\new_template", opts=[])
                response = env.render_template("templates\\welcome", opts=[])
            else:
                response = env.render_template("templates\\form", opts=[])
        except Exception as e:
            response = f"<h1>Internal server error</h1><p>{str(e)}</p>"

        # Send response headers
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # Send the rendered HTML
        self.wfile.write(response.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        # Read the POST body data
        post_data = self.rfile.read(content_length).decode('utf-8')

        # Parse form data
        params = parse_qs(post_data)

        if params.get("identity_form"):
            name = params.get("name", [""])[0]  # Default to empty string if missing
            surname = params.get("surname", [""])[0]
            print(f"Name - Username: {name} - {surname}")

            new_template = "<h1>Welcome, %s!</h1>" % name
            new_template += "<p style=\"font-size:20px;\">Your surname is: %s </p>" % surname
            print("Template: ", new_template)
            with open("templates/new_template.spf", "w") as f:
                f.write(new_template)

        if params.get("credentials_form"):
            username = params.get("username", [""])[0]  # Default to empty string if missing
            email = params.get("email", [""])[0]
            print(f"Username - email: {username} - {email}")

            new_template = "<h1>Welcome, %s!</h1>" % username
            new_template += "<p style=\"font-size:20px;\">Your email is: %s </p>" % email
            print("Template: ", new_template)
            with open("templates/new_template.spf", "w") as f:
                f.write(new_template)

        # Need to keep the server online
        try:
            env.load_dir()
            response = env.render_template("templates\\new_template", opts=[])
        except Exception as e:
            response = f"<h1>Internal server error</h1><p>{str(e)}</p>"


        # Send Response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write(response.encode("utf-8"))


# Set up the server
PORT = 8080
server_address = ("", PORT)
env = spitfire.Environment('templates')
# 'templates' folder becomes the "home" of this Environment
env.load_dir() # no parameters on load_dir() loads the "home" directory

httpd = HTTPServer(server_address, MyHandler)

print(f"Serving on http://127.0.0.1:{PORT}")
httpd.serve_forever()

