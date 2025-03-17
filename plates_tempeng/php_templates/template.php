<!-- Title and content are set dynamically: they are passed from
the template that inherits "template.php" -->
<html>
    <head>
        <title><?=$this->e($title)?></title>
    </head>
    <body>
        <?=$this->section('content')?>
    </body>
</html>