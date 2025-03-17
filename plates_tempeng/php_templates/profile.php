<?php $this->layout('template', ['title' => 'User Profile']) ?>

<h1>User Profile</h1>
<p>Hello, <?= $name ?></p>

<!-- it seems it's safe as long as user input is passed to the template through render() -->
<!--<p>Hello, <?php echo "$name" ?></p>-->