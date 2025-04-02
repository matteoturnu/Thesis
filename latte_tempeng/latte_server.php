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

                /*$new_template = "<h1>User Profile</h1>
                <p>Hello, <?php echo \"$name\" ?></p>";
                <?*/

                /*$new_template = "<h1>User Profile</h1>
                                <p>Hello, <?php echo \$user ?></p>";*/

                /*$new_template = "<h1>User Profile</h1>
                                <p>Hello, <?php echo \"${name}\" ?></p>
                                <p>Your surname is: <?php echo \"${surname}\" ?></p>";*/
            $new_template = "<h1>User Profile</h1>
                                <p>Hello, $name </p>
                                <p>Your other data: </p>
                                <p>Surname: $surname </p>
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
                                <p>Hello, $user </p>
                                <p>Your email is: $email</p>";
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
    else {

        if (isset($_GET["title"])) {
            $title = $_GET["title"];
            $message = $_GET["message"];
            $link_template = "<h1>Value of query parameter in the first link </h1>
                                <p>Query: $title</p>
                                <p>Query: $message</p>";
            file_put_contents("templates/link_template.latte", $link_template);
            $latte->render("templates/link_template.latte");
        }
        if (isset($_GET["greeting"])) {
            $greeting = $_GET["greeting"];
            $clap = $_GET["clap"];
            $link_template = "<h1>Value of query parameter in the second link </h1>
                                <p>Query: $greeting</p>
                                <p>Query: $clap</p>";
            file_put_contents("templates/link_template.latte", $link_template);
            $latte->render("templates/link_template.latte");
        }
        else
            $latte->render('templates/form.latte');
    }




?>