from pydoc import html

from quik import Template, FileLoader

import os.path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
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
        """

        # Parse URL parameters
        query = urlparse(self.path).query
        params = parse_qs(query)

        if params.get("title"):
            title = params.get("title")[0]
            message = params.get("message", [""])[0]

            link_plain_template = "<h1>Value of query parameter in the first link</h1>"
            link_plain_template += "<p>Link1 query1: %s </p>" % title
            link_plain_template += "<p>Link1 query2: %s </p>" % message

            link_code_template = "<h1>Value of query parameter in the first link</h1>"
            link_code_template += "<p>Link1 query1: @%s</p>" % title
            link_code_template += "<p>Link1 query1: @%s</p>" % message

            try:
                response = Template(link_plain_template).render({})
                # response = Template(link_code_template).render({})
            except Exception as e:
                response = f"<h1>Internal server error</h1><p>{str(e)}</p>"


        elif params.get("greeting"):
            greeting = params.get("greeting")[0]
            clap = params.get("clap", [""])[0]

            link_plain_template = "<h1>Value of query parameter in the second link</h1>"
            link_plain_template += "<p>Link2 query1: %s </p>" % greeting
            link_plain_template += "<p>Link2 query2: %s </p>" % clap

            link_code_template = "<h1>Value of query parameter in the second link</h1>"
            link_code_template += "<p>Link2 query1: @%s</p>" % greeting
            link_code_template += "<p>Link2 query1: @%s</p>" % clap

            try:
                response = Template(link_plain_template).render({})
                # response = Template(link_code_template).render({})
            except Exception as e:
                response = f"<h1>Internal server error</h1><p>{str(e)}</p>"

        elif params.get("query1"):
            query1 = params.get("query1")[0]
            query2 = params.get("query2", [""])[0]

            fullnav_btn_plain_template = "<h1>Button JS fullnav clicked! </h1>"
            fullnav_btn_plain_template += "<p>JSbtn query1: %s </p>" % query1
            fullnav_btn_plain_template += "<p>JSbtn query2: %s </p>" % query2

            fullnav_btn_code_template = "<h1>Button JS fullnav clicked! </h1>"
            fullnav_btn_code_template += "<p>JSbtn query1: @%s</p>" % query1
            fullnav_btn_code_template += "<p>JSbtn query2: @%s</p>" % query2

            try:
                # response = Template(fullnav_btn_code_template).render({})
                response = Template(fullnav_btn_plain_template).render({})
            except Exception as e:
                response = f"<h1>Internal server error</h1><p>{str(e)}</p>"
        else:
            try:
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

        plaintext_context_template = ""
        code_context_template = ""
        if params.get("identity_form"):
            name = params.get("name", [""])[0]  # Default to empty string if missing
            fav_lang = params.get("fav_language", [""])[0]
            vehicle1 = params.get("vehicle1", [""])[0]
            vehicle2 = params.get("vehicle2", [""])[0]
            vehicle3 = params.get("vehicle3", [""])[0]
            password = params.get("password", [""])[0]
            email = params.get("email", [""])[0]
            search = params.get("search", [""])[0]
            tel = params.get("phone_number", [""])[0]
            textarea = params.get("w3review", [""])[0]
            sex = params.get("sex", [""])[0]

            search = html.escape(search)

            #####################
            #user = {'name': name}


            plaintext_context_template = "<h1>User Profile</h1>"
            plaintext_context_template += "<p>Hello, %s </p>" % name
            # plaintext_context_template += "<p>Hello, @user.name </p>"
            plaintext_context_template += "<p>Sex: %s </p>" % sex
            plaintext_context_template += "<p>Your fav language: %s </p>" % fav_lang
            plaintext_context_template += "<p>Your vehicles: %s, %s, %s </p>" % (vehicle1, vehicle2, vehicle3)
            plaintext_context_template += "<p>Password: %s </p>" % password
            plaintext_context_template += "<p>E-mail: %s </p>" % email
            plaintext_context_template += "<p>Search: %s </p>" % search
            plaintext_context_template += "<p>Phone number: %s </p>" % tel
            plaintext_context_template += "<p>Textarea: %s </p>" % textarea

            code_context_template = "<h1>User Profile</h1>"
            code_context_template += "<p>Hello, @{%s} </p>" % name
            code_context_template += "<p>Sex: @{%s} </p>" % sex
            code_context_template += "<p>Your fav language: @{%s} </p>" % fav_lang
            code_context_template += "<p>Your vehicles: @{%s}, @{%s}, @{%s} </p>" % (vehicle1, vehicle2, vehicle3)
            code_context_template += "<p>Password: @{%s} </p>" % password
            code_context_template += "<p>E-mail: @{%s} </p>" % email
            code_context_template += "<p>Search: @{%s} </p>" % search
            code_context_template += "<p>Phone number: @{%s} </p>" % tel
            code_context_template += "<p>Textarea: @{%s} </p>" % textarea

            print(code_context_template)
            print(locals())

        try:
            # response = Template(plaintext_context_template).render(locals())
            response = Template(plaintext_context_template).render({})
            # response = Template(code_context_template).render({})
        except Exception as e:
            response = f"<h1>Internal server error</h1><p>{str(e)}</p>"

        # Send Response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))


# Set up the server
PORT = 8000
server_address = ("", PORT)

httpd = HTTPServer(server_address, MyHandler)

print(f"Serving on http://127.0.0.1:{PORT}")
httpd.serve_forever()
