from quik import Template, FileLoader

import os.path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import subprocess, sys
import spitfire


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
                template_string = "<h1>Welcome, %s</h1>" % name
                response = Template(template_string).render({})
            else:
                loader = FileLoader('html')
                response = loader.load_template('form.html').render({})
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

        template_string = ""
        if params.get("identity_form"):
            name = params.get("name", [""])[0]  # Default to empty string if missing
            surname = params.get("surname", [""])[0]
            print(f"Name - Username: {name} - {surname}")

            template_string = "<h1>Welcome, %s</h1>" % name
            template_string += "<p style=\"font-size:20px;\">Your surname is: %s </p>" % surname

        if params.get("credentials_form"):
            username = params.get("username", [""])[0]  # Default to empty string if missing
            email = params.get("email", [""])[0]
            print(f"Username - email: {username} - {email}")

            template_string = "<h1>Welcome, @{ %s }!</h1>" % username
            template_string += "<p style=\"font-size:20px;\">Your email is: @{ %s } </p>" % email
            #template_string = "<h1>Welcome, @{username}!</h1>"
            #template_string += "<p style=\"font-size:20px;\">Your email is: @{email} </p>"

        try:
            # response = Template(template_string).render({})
            # response = Template(template_string).render({"username": username})
            response = Template(template_string).render(locals())
            print(locals())
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

httpd = HTTPServer(server_address, MyHandler)

print(f"Serving on http://127.0.0.1:{PORT}")
httpd.serve_forever()
