<?php
    // require '../vendor/autoload.php';
    require 'raintpl3/library/Rain/autoload.php';
    use Rain\Tpl;

    $config = array(
                     "tpl_dir" => "C:/Users/matte/PycharmProjects/SSTI_Thesis/raintpl_tempeng/templates/",
                     "cache_dir" => "vendor/rain/raintpl/cache/"
    );
    Tpl::configure( $config );
    $t = new Tpl;

    if ($_POST) {
        if (isset($_POST["identity_form"])) {
            $name = $_POST["name"];
            //escape name (htmlspecialchars() not working...)
            # $name = htmlspecialchars($name, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
            $name = htmlentities($name);
            $surname = $_POST["surname"];

            $plain_context_template = "<h1>User Profile</h1>
                            <p>Hello, $name </p>
                            <p>Your surname is: $surname</p>";
            $code_context_template = "<h1>User Profile</h1>
                            <p>Hello, {$name} </p>
                            <p>Your surname is: {$surname} </p>";

        }
        else if (isset($_POST["credentials_form"])) {
            $user = $_POST["username"];
            $email = $_POST["email"];

            $plain_context_template = "<h1>User Profile</h1>
                            <p>Hello, $user </p>
                            <p>Your email is: $email </p>";
            /*$code_context_template = "<h1>User Profile</h1>
                            <p>Hello, { $user } </p>
                            <p>Your email is: { $email } </p>";*/
            $code_context_template = "<h1>User Profile</h1>";
            $code_context_template .= '<p>Hello, {$' . $user . '} </p>';
            $code_context_template .= '<p>Your email is: {$' . $email . '} </p>';
        }

        # create a file with the template
        //echo "Template start: $code_context_template";
        //echo "Template end";
        file_put_contents("templates/template.html", $plain_context_template);
        echo $t->draw('template');

    }
    else {
        echo $t->draw('form');
    }

    /*
    $str = "ciao";
    # $user_input = "{function=\"print(7*7)\"}";
    $user_input = "{$str}";
    $tpl_string = "Welcome, $user_input";
    //echo $tpl_string;
    file_put_contents("templates/test.html", $tpl_string);
    $t->draw('test');
    */



?>