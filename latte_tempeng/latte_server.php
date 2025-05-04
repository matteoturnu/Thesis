<?php
    require '../vendor/autoload.php';
    $latte = new Latte\Engine;
    // cache directory
    #$latte->setTempDirectory('/path/to/tempdir');


    // or $params = new TemplateParameters(/* ... */);

    // "/" before $ needed to tell PHP not to consider it as a variable
    /*
    $new_template = "<h1>Welcome, {\$user}</h1>";
    file_put_contents("templates/template.latte", $new_template);
    $params = ['user' => 'Matteo'];

    // render to output
    $latte->render('templates/template.latte', $params);
    */

    if ($_POST) {
        ///if ($_POST["identity_form"]) {
        if (isset($_POST["identity_form"])) {
            $name = $_POST["name"];
            $surname = $_POST["surname"];
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

            $new_template = "<h1>User Profile</h1>
                                <p>Hello, $name </p>
                                <p>Your other data: </p>
                                <p>Surname: $surname </p>
                                <p>Sex: $sex</p>
                                <p>Your fav language: $fav_lang </p>
                                <p>Your vehicles: $vehicle1, $vehicle2, $vehicle3</p>
                                <p>Password: $password </p>
                                <p>E-mail: $email </p>
                                <p>Search: $search </p>
                                <p>Phone number: $tel </p>
                                <p>Textarea: $textarea </p>";

        }
        else if (isset($_POST["credentials_form"])) {
            $user = $_POST["username"];
            $email = $_POST["email"];

            $new_template = "<h1>User Profile</h1>
                                <p>Hello, { $user }</p>
                                <p>Your email is: {= $email }</p>";
        }
        //$name = $_POST["name"];

        # if I don't create everytime the template SSTI doesn't work
        # it would give "undefined variable $name"
        # vulnerable to SSTI

        //$new_template = "<h1>Welcome, {$name}</h1>";
        /*
        $template = $latte->createTemplate();
        $template->setSource($new_template);  // Set the string as the template source
        echo $template->renderToString();*/

        file_put_contents("templates/template.latte", $new_template);
        #$params = ['user' => $name];
        $params = [];

        $latte->render('templates/template.latte', $params);


    }
    else {      //GET request

        if (isset($_GET["title"])) {
            //Link 1
            $title = $_GET["title"];
            $message = "";
            if (isset($_GET["message"]))
                $message = $_GET["message"];
            $link_template = "<h1>Value of query parameter in the first link </h1>
                                <p>Link1 query1: $title</p>
                                <p>Link1 query 2: $message</p>";
            file_put_contents("templates/link_template.latte", $link_template);
            $latte->render("templates/link_template.latte");
        }
        else if (isset($_GET["greeting"])) {
            // Link 2
            $greeting = $_GET["greeting"];
            $clap = "";
            if (isset($_GET["clap"]))
                $clap = $_GET["clap"];
            $link_template = "<h1>Value of query parameter in the second link </h1>
                                <p>Link2 query1: $greeting</p>
                                <p>Link2 query2: $clap</p>";
            file_put_contents("templates/link_template.latte", $link_template);
            $latte->render("templates/link_template.latte");
        }
        else if (isset($_GET["query1"])) {
            //button JS id=fullnav
            $query1 = $_GET["query1"];
            $query2 = "";
            if (isset($_GET["query2"]))
                $query2 = $_GET["query2"];
            $fullnav_btn_template = "<h1>Button JS fullnav clicked! </h1>
                                <p>JSbtn query1: $query1</p>
                                <p>JSbtn query2: $query2</p>";
            file_put_contents("templates/navbutton_template.latte", $fullnav_btn_template);
            $latte->render("templates/navbutton_template.latte");
        }
        else
            $latte->render('templates/form.latte');
    }




?>