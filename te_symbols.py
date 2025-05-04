# TODO: study code context for asymmetric symbols ($, #, etc.)
te_symbols = {
    " ": {
        "Any": "Any" # code context
    },

    "$ ": {
        "Cheetah": "Python",
        "Genshi and Kid": "Python",
        "Mako": "Python",
        "Velocity": "Java"
    },

    "# ": {
        "Cheetah": "Python",
        "Velocity": "Java",
        "Handlebars": "JavaScript"
    },

    "@ ": {
        "SquirrellyJS": "JavaScript",
        "Plates": "PHP"     # code context for "<?= $input ?>"
    },

    "#set@a= :@a": {
        "Quik": "Python",
    },

    "| ": {
        "SquirrellyJS": "JavaScript",
    },

    "= ": {
        "Slim": "Ruby"
    },

    "( )": {       # TODO: problem: always successful when used in code context (treated as Python brackets)
        "Razor": ".NET"
    },

    ")( ": {
        "Razor": ".NET"
    },

    "{ }": {
        "Smarty": "PHP",
        "Latte": "PHP",
        "Dust": "JavaScript",
        "Razor": ".NET"
    },
    "}{ ": {
        "Smarty": "PHP",
        "Latte": "PHP",
        "Dust": "JavaScript",
        "Razor": ".NET"
    },

    "{@ }": {
        "Latte": "PHP",
        "Dust": "JavaScript"
    },

    "}{@ ": {
        "Latte": "PHP",
        "Dust": "JavaScript"
    },

    "{= }": {
        "Latte": "PHP"
    },

    "}{= ": {
        "Latte": "PHP"
    },

    "${ }": {
        "Chameleon": "Python",
        "Evoque": "Python",
        "Thymeleaf": "Java",
        "FreeMarker": "Java",
        "Marko": "JavaScript",
        "Plates": "PHP"     # code context for "<?= $input ?>"
    },

    "}${ ": {
        "Chameleon": "Python",
        "Evoque": "Python",
        "Thymeleaf": "Java",
        "FreeMarker": "Java",
        "Marko": "JavaScript"
    },

    "${int( )}": {
        "Spitfire": "Python",
        "Evoque": "Python"
    },

    "}${int( )": {
        "Spitfire": "Python",
        "Evoque": "Python"
    },

    "#set $num= #$num": {
        "Spitfire": "Python"
    },

    "#{ }": {
        "Thymeleaf": "Java",
        "Pug and Jade": "JavaScript"
    },

    "}#{ ": {
        "Thymeleaf": "Java",
        "Pug and Jade": "JavaScript"
    },

    "{{= }}": {
        "web2py": "Python",
        "doT": "JavaScript"
    },

    "}}{{= ": {
        "web2py": "Python",
        "doT": "JavaScript"
    },

    "{{ }}": {
        "Jinja2": "Python",
        "Django": "Python",
        "Tornado": "Python",
        "Twig": "PHP",
        "Blade": "PHP",
        "Jinjava": "Java",
        "JsRender": "JavaScript",
        "Handlebars": "JavaScript",
        "Nunjucks": "JavaScript",
        "Vue": "JavaScript",
        "SquirrellyJS": "JavaScript",
        "Template7": "JavaScript",
        "Golang": "Default Engine"
    },

    "}}{{ ": {
        "Jinja2": "Python",
        "Django": "Python",
        "Tornado": "Python",
        "Twig": "PHP",
        "Blade": "PHP",
        "Jinjava": "Java",
        "JsRender": "JavaScript",
        "Handlebars": "JavaScript",
        "Nunjucks": "JavaScript",
        "Vue": "JavaScript",
        "SquirrellyJS": "JavaScript",
        "Template7": "JavaScript",
        "Golang": "Default Engine"
    },

    "{{# }}": {
        "Template7": "JavaScript"
    },

    "}}{{# ": {
        "Template7": "JavaScript"
    },

    "{{: }}": {
        "JsRender": "JavaScript"
    },

    "}}{{: ": {
        "JsRender": "JavaScript"
    },

    "<? ?>": {
        "Genshi and Kid": "Python",
    },

    "?><? ": {
        "Genshi and Kid": "Python",
    },

    "<?= ?>": {
        "Plates": "PHP"  # Note: short notation for echo. Functions work as well
    },

    "1?><?= ": {    # can't close first statement without outputting something (1 in this case)
        "Plates": "PHP"    # code context for "<?= $input ?>"
    },

    "<% %>": {
        "Mako": "Python"
    },

    "%><% ": {
        "Mako": "Python"
    },

    "<%= %>": {
        "EJS": "JavaScript",
        "ERB": "Ruby",
        "Mojolicious": "Perl",
        "ASP": ".NET"
    },

    "%><%= ": {
        "EJS": "JavaScript",
        "ERB": "Ruby",
        "Mojolicious": "Perl",
        "ASP": ".NET"
    },

    "{% %}": {
        "Tornado": "Python",
        "Pebble": "Java"
    },

    "%}{% ": {
        "Tornado": "Python",
        "Pebble": "Java"
    },

    "@! !@": {
        "Pyratemp": "Python"
    },

    "!@@! ": {
        "Pyratemp": "Python"
    },

    "[[ ]]": {
        "Thymeleaf": "Java"
    },

    "]][[ ": {
        "Thymeleaf": "Java"
    }
}
