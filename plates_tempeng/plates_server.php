<?php
    require '../vendor/autoload.php';

    // To enable the web server, type "php -S 127.0.0.1:8000" in the Pycharm Terminal
    // and navigate to 127.0.0.1:8000/server.php

    // Create new Plates instance
    $templates = new League\Plates\Engine('php_templates');

    if ($_POST) {
        if (isset($_POST["identity_form"])) {
            $name = $_POST["name"];
            //escape name (htmlspecialchars() not working...)
            # $name = htmlspecialchars($name, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
            $name = htmlentities($name);
            $surname = $_POST["surname"];

            /*$new_temp\late = "<h1>User Profile</h1>
            <p>Hello, <?php echo \"$name\" ?></p>";
            <?*/

            /*$new_template = "<h1>User Profile</h1>
                            <p>Hello, <?php echo \$user ?></p>";*/

            /*$new_template = "<h1>User Profile</h1>
                            <p>Hello, <?php echo \"${name}\" ?></p>
                            <p>Your surname is: <?php echo \"${surname}\" ?></p>";*/
            $new_template = "<h1>User Profile</h1>
                            <p>Hello, $name </p>
                            <p>Your surname is: $surname</p>";

        }
        else if (isset($_POST["credentials_form"])) {
            $user = $_POST["username"];
            $email = $_POST["email"];

            $new_template = "<h1>User Profile</h1>
                            <p>Hello, $user </p>
                            <p>Your email is: $email</p>";
        }

        # create a file with the template
        file_put_contents("php_templates/new_template.php", $new_template);
        echo $templates->render('new_template');

        #echo $templates->render('profile', ['name' => $name]);

    }
    else {
        // Render a template
        //echo $templates->render('profile', ['name' => 'Jonathan']);
        echo $templates->render('form');
    }

?>

