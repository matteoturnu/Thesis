<?php

   if (isset($_POST["identity_form"])) {
        $name = $_POST["name"];
        //escape name
        //$name = htmlspecialchars($name);
        $surname = $_POST["surname"];


        echo "Name: $name; Surname: $surname";

   }
   else if (isset($_POST["credentials_form"])) {
        $user = $_POST["username"];
        $email = $_POST["email"];

        echo "Username: $user; Email: $email";
   }

?>
<html>
  <head><title>Simple PHP server</title></head>
  <body>
    <h1>Enter your name!</h1>
    <form action="http://127.0.0.1:8080" method="post">
        <input type="text" name="name" placeholder="Your Name"> <br><br>
        <input type="text" name="surname" placeholder="Your Surname"> <br><br>
        <input type="submit" name="identity_form" value="Send">
    </form>
    <form action="http://127.0.0.1:8080" method="post">
        <input type="text" name="username" placeholder="Your username"> <br><br>
        <input type="text" name="email" placeholder="Your e-mail"> <br><br>
        <input type="submit" name="credentials_form" value="Send">
    </form>

  </body>
</html>
