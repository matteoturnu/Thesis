from kajiki import XMLTemplate, PackageLoader, FileLoader

import os.path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os.path
from evoque.template import Template


from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

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
                response = XMLTemplate(template_string).render()
            else:
                loader = FileLoader("templates/")
                Template = loader.import_('form.html')
                response = Template().render()
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

        plaintext_context_template = ""
        code_context_template = ""
        if params.get("identity_form"):
            name = params.get("name", [""])[0]  # Default to empty string if missing
            surname = params.get("surname", [""])[0]
            print(f"Name - Username: {name} - {surname}")

            plaintext_context_template = """<html xmlns='http://www.w3.org/1999/xhtml'>
                                            <body><p>Welcome, %s</p>""" % name
            plaintext_context_template += "<p style=\"font-size:20px;\">Your surname is: %s </p>" % surname
            plaintext_context_template += "</body></html>"

            code_context_template = """<html xmlns='http://www.w3.org/1999/xhtml'>
                                                        <body><p>Welcome, ${%s}</p>""" % name
            code_context_template += "<p style=\"font-size:20px;\">Your surname is: ${%s} </p>" % surname
            code_context_template += "</body></html>"

        if params.get("credentials_form"):
            username = params.get("username", [""])[0]  # Default to empty string if missing
            email = params.get("email", [""])[0]
            print(f"Username - email: {username} - {email}")

            plaintext_context_template = """<html xmlns='http://www.w3.org/1999/xhtml'>
                                            <body><p>Welcome, %s</p> """ % username
            plaintext_context_template += "<p style=\"font-size:20px;\">Your email is: %s </p>" % email
            plaintext_context_template += "</body></html>"

            code_context_template = """<html xmlns='http://www.w3.org/1999/xhtml'>
                                                        <body><p>Welcome, ${%s}</p> """ % username
            code_context_template += "<p style=\"font-size:20px;\">Your email is: ${%s} </p>" % email
            code_context_template += "</body></html>"

        try:
            # response = XMLTemplate(plaintext_context_template).render()
            Tpl = XMLTemplate(code_context_template)
            response = Tpl().render()
            # response = XMLTemplate(code_context_template).render()
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
domain = os.path.join(os.path.abspath("."), "templates")

httpd = HTTPServer(server_address, MyHandler)

print(f"Serving on http://127.0.0.1:{PORT}")
httpd.serve_forever()

