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
        $name = $_POST["name"];

        # if I don't create everytime the template SSTI doesn't work
        # it would give "undefined variable $name"
        # vulnerable to SSTI

        $new_template = "<h1>Welcome, {$name}</h1>";
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
        $latte->render('templates/form.latte');
    }




?>