<?php
    require '../vendor/autoload.php';

    // To enable the web server, type "php -S 127.0.0.1:8000" in the Pycharm Terminal
    // and navigate to 127.0.0.1:8000/server.php

    // Create new Plates instance
    $templates = new League\Plates\Engine('php_templates');

    if ($_POST) {
        if (isset($_POST["identity_form"])) {
            $name = $_POST["name"];
            //$surname = $_POST["surname"];

            $fav_lang = $_POST["fav_language"];
            $vehicle1 = $_POST["vehicle1"];
            $vehicle2 = $_POST["vehicle2"];
            $vehicle3 = $_POST["vehicle3"];

            $password = $_POST["password"];
            $email = $_POST["email"];
            $search = $_POST["search"];
            $tel = $_POST["phone_number"];
            $textarea = $_POST["w3review"];
            $sex = $_POST["sex"];
            // escaping search
            $search = htmlspecialchars($search);

            // define() are used to avoid "undefined constant" errors for
            // drop-down list, radio buttons and checkboxes with legitimate inputs
            /*if (!define($name, $name))
                define($name, $name);*/
            /*if (!define($sex, $sex))
                define($sex, $sex);
            if (!define($fav_lang, $fav_lang))
                define($fav_lang, $fav_lang);
            if (!define($vehicle1, $vehicle1))
                define($vehicle1, $vehicle1);
            if (!define($vehicle2, $vehicle2))
                define($vehicle2, $vehicle2);
            if (!define($vehicle3, $vehicle3))
                define($vehicle3, $vehicle3);*/
            /*if (!define($password, $password))
                define($password, $password);
            if (!define($email, $email))
                define($email, $email);
            if (!define($search, $search))
                define($search, $search);
            if (!define($tel, $tel))
                define($tel, $tel);
            if (!define($textarea, $textarea))
                define($textarea, $textarea);*/


            $plain_context_template = "<h1>User Profile</h1>
                                <p>Hello,  $name </p>
                                <p>Sex: $sex </p>
                                <p>Your fav language: $fav_lang </p>
                                <p>Your vehicles: $vehicle1, $vehicle2 , $vehicle3 </p>
                                <p>Password: $password </p>
                                <p>E-mail: $email </p>
                                <p>Search: $search </p>
                                <p>Phone number: $tel </p>
                                <p>Textarea: $textarea </p>";
            $code_context_template = "<h1>User Profile</h1>
                                <p>Hello, <?= $name ?> </p>
                                <p>Sex: <?= $sex ?></p>
                                <p>Your fav language: <?= $fav_lang ?></p>
                                <p>Your vehicles: <?= $vehicle1 ?>, <?= $vehicle2 ?>, <?= $vehicle3 ?></p>
                                <p>Password: <?= $password ?></p>
                                <p>E-mail: <?= '$email' ?></p>
                                <p>Search: <?= $search ?></p>
                                <p>Phone number: <?= $tel ?></p>
                                <p>Textarea: <?= $textarea ?></p>";

        }
        else if (isset($_POST["credentials_form"])) {
            $user = $_POST["username"];
            $email = $_POST["email"];

            $plain_context_template = "<h1>User Profile</h1>
                            <p>Hello, $user </p>
                            <p>Your email is: $email </p>";
            $code_context_template = "<h1>User Profile</h1>
                            <p>Hello, <?= $user ?> </p>
                            <p>Your email is: <?= $email ?> </p>";
            /* NOTE: <? ?> symbols require "echo 7*7" to obtain same result as <?=7*7?> */
        }

        # create a file with the template
        file_put_contents("php_templates/new_template.php", $plain_context_template);
        //file_put_contents("php_templates/new_template.php", $code_context_template);
        echo $templates->render('new_template');

        #echo $templates->render('profile', ['name' => $name]);

    }
    else {
        // Render a template
        //echo $templates->render('profile', ['name' => 'Jonathan']);
        if (isset($_GET["title"])) {
            //Link 1
            $title = $_GET["title"];
            /*if (!define($title, $title))
                define($title, $title);*/

            $message = "";
            if (isset($_GET["message"])){
                $message = $_GET["message"];
                /*if (!define($message, $message))
                    define($message, $message);*/
            }

            $link_plain_template = "<h1>Value of query parameter in the first link </h1>
                                <p>Link1 query1: $title</p>
                                <p>Link1 query 2: $message</p>";
            $link_code_template = "<h1>Value of query parameter in the first link </h1>
                                <p>Link1 query1: <?= $title ?></p>
                                <p>Link1 query 2: <?= $message ?></p>";
            file_put_contents("php_templates/link_template.php", $link_plain_template);
            //file_put_contents("php_templates/link_template.php", $link_code_template);
            echo $templates->render('link_template');
        }
        else if (isset($_GET["greeting"])) {
            // Link 2
            $greeting = $_GET["greeting"];
            /*if (!define($greeting, $greeting))
                define($greeting, $greeting);*/

            $clap = "";
            if (isset($_GET["clap"])){
                $clap = $_GET["clap"];
                /*if (!define($clap, $clap))
                    define($clap, $clap);*/
            }
            $link_plain_template = "<h1>Value of query parameter in the second link </h1>
                                <p>Link2 query1: $greeting</p>
                                <p>Link2 query2: $clap</p>";
            $link_code_template = "<h1>Value of query parameter in the second link </h1>
                                <p>Link2 query1: <?= $greeting ?></p>
                                <p>Link2 query2: <?= $clap ?></p>";
            file_put_contents("php_templates/link_template.php", $link_plain_template);
            //file_put_contents("php_templates/link_template.php", $link_code_template);
            echo $templates->render("link_template");
        }
        else if (isset($_GET["query1"])) {
            //button JS id=fullnav
            $query1 = $_GET["query1"];
            /*if (!define($query1, $query1))
                define($query1, $query1);*/

            $query2 = "";
            if (isset($_GET["query2"])){
                $query2 = $_GET["query2"];
                /*if (!define($query2, $query2))
                    define($query2, $query2);*/
            }

            $fullnav_btn_plain_template = "<h1>Button JS fullnav clicked! </h1>
                                <p>JSbtn query1: $query1</p>
                                <p>JSbtn query2: $query2</p>";
            $fullnav_btn_code_template = "<h1>Button JS fullnav clicked! </h1>
                                <p>JSbtn query1: <?= $query1 ?></p>
                                <p>JSbtn query2: <?= $query2 ?></p>";
            file_put_contents("php_templates/navbutton_template.php", $fullnav_btn_plain_template);
            //file_put_contents("php_templates/navbutton_template.php", $fullnav_btn_code_template);
            echo $templates->render("navbutton_template");
        }
        else
            echo $templates->render('form');
        //echo $templates->render('form');
    }

?>

