<html>
  <head><title>Simple Plates Server</title></head>
  <body>
    <h1>Enter your name!</h1>
    <form method="post" action="/server.php">
        <input type="text" name="name" placeholder="Your Name"> <br><br>
        <input type="text" name="surname" placeholder="Your Surname"> <br><br>
        <input type="submit" name="identity_form" value="Send">
    </form>
    <form method="post" action="/server.php">
        <input type="text" name="username" placeholder="Your username"> <br><br>
        <input type="text" name="email" placeholder="Your e-mail"> <br><br>
        <input type="submit" name="credentials_form" value="Send">
    </form>

  </body>
</html>