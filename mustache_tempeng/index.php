<?php
    require '../vendor/autoload.php';

    $m = new Mustache_Engine(array('entity_flags' => ENT_QUOTES));

    /*
    $options = array('extension' => '.php');
    $m_dir = new Mustache_Engine(array(
        'loader' => new Mustache_Loader_FilesystemLoader('C:/Users/matte/PycharmProjects/SSTI_Thesis/plates_tempeng/php_templates', $options),
    ));
    */
    #echo $m->render('Hello {{planet}}', array('planet' => 'World!')); // "Hello World!"

    # ${ } works with {{user_input}}, {{{...}}}, {{$...} and so on

    /*
    $user_input = "${7*7}";
    #$str_template = "Hello, {{{\$user_input}}}";
    $str_template = "Hello, {{user_input}}";
    #echo $m->render($str_template);
    echo $m->render($str_template, array('user_input' => $user_input)); // "Hello World!"
    */



    $form_template = "<h1>Enter your name!</h1>
    <form method=\"post\" action=\"/index.php\">
        <input type=\"text\" name=\"name\" placeholder=\"Your Name\"> <br><br>
        <input type=\"text\" name=\"surname\" placeholder=\"Your Surname\"> <br><br>
        <input type=\"submit\" name=\"identity_form\" value=\"Send\">
    </form>
    <form method=\"post\" action=\"/index.php\">
        <input type=\"text\" name=\"username\" placeholder=\"Your username\"> <br><br>
        <input type=\"text\" name=\"email\" placeholder=\"Your e-mail\"> <br><br>
        <input type=\"submit\" name=\"credentials_form\" value=\"Send\">
    </form>";



    if ($_POST) {
        if ($_POST["identity_form"]) {
            $name = $_POST["name"];

            $surname = $_POST["surname"];

            /*
            $str_template = "<h1>User Profile</h1>
            <p>Hello, <?php echo \"${name}\" ?></p>
            <p>Your surname is: $surname</p>";
            #echo $m->render($str_template);
            */

            $str_template = "<h1>User Profile</h1>
            <p>Hello, $name </p>
            <p>Your surname is: $surname</p>";
            echo $m->render($str_template);

        }
        else if ($_POST["credentials_form"]) {
            $user = $_POST["username"];
            $email = $_POST["email"];

            echo $m->render($str_template, array('input_1' => $user, 'input_2' => $email));
        }



    }
    else {
        echo $m->render($form_template);
    }


?>