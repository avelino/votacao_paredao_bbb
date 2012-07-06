## The really serious and relevant points

### Our goals here

- Calling the great holy rabbit from the mountains
- Sending the black night ninjas to Avalon
- Stop killing fat whales
- Rescuing the enchanted princess from the dark castle
- Killing the ORM monster
- Saving the world

... and, if we get enough time:

- To use HTML5 as the big-main-thing
- To use the best SEO practices
- To come out with Ajax and JavaScript love
- To support Python 3 (finally)
- To work friendly with NoSQL (otherwise we should stop talking about them)
- To handle asynchronous requests properly

### Testing, running, etc.

Start a virtualenv

    $ cd the-root-folder-of-this-repository
    $ virtualenv env
    $ source env/bin/activate

    $ pip install -r requirements.txt
    $ python setup.py develop
    $ cd test_project

    $ london-admin.py run public # For the public website
    $ london-admin.py run ws # In another window, for the WebSockets

### In a Unix-like operating system with just Python, you can run:

    $ curl -o /tmp/x -L -O http://tinyurl.com/london-start ; python /tmp/x
    ... inform the project name
    ... inform the London version
    ... bazinga!

To run the public service instance

    $ cd PROJECT_NAME/root
    $ source ../env/bin/activate
    $ london-admin.py run public

### About dependencies

London is free software and tries to get the best ideas from other free software. So...

- it was designed to work on Python 2.6 or higher version
- some code blocks were copied from Django (especially most of london.utils.\*)
- some of syntax were copied or inspired on Django's syntax or Tornado's syntax
- Tornado is the default server, but Eventlet is stable as well
- At this moment, you must run it under a reverse proxy server, like Nginx
- jQuery is used for everything on JavaScript and Ajax requests
- Templates are done by **Jinja2**
- virtualenv
- pip
- distribute
- PyDispatcher
- BeautifulSoup
- python-money
- nose
- simplejson

