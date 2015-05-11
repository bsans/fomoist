# Fomo-ist

*Fomoist:*

*One who suffers from FOMO.  Easily detectable by RSVPs to 2 or more conflicting events.*

## Problem:

People RSVP as "attending" to events when they can't possibly attend all of them.

## Solution:

**Shame them.**

People believe they are under the radar with their rampant rsvp-ing.  

Until now.

`fomoist` is a tool that surfaces *public* data about who claims they are attending events on Facebook that conflict in time.

# Installation

(also requires `git`...)

1. Install `pip`

   ```
   $ sudo easy_install pip
   ```

2. Install `virtualenv`

   ```
   $ sudo pip install virtualenv
   ```

3. Clone `fomoist`

   ```
   $ git clone git@github.com:bsans/fomoist.git
   ```

4. Start the `virtualenv`

   (in the dir where you put the cloned project)
   
   ```
   $ source bin/activate
   ```
   

5. Install dependencies

	(in the dir where you put the cloned project)
	
   ```
   $ pip install -r requirements.txt
   ```


6. Initialize the db

   ```
   $ python 
   
   >>> from fomoist import init_db
   >>> init_db()
   ```
   (then `ctrl-D` to exit the python shell)

7. Get a FB auth token.  Go to [the Facebook Graph Explorer](https://developers.facebook.com/tools/explorer), log into FB, and then click on the right under *Get Token*.  Probably just give yourself all the access permissions (click all the checkboxes).  Copy the long access token.  In the source code, for the variable `AUTH_TOKEN`, assign it to this string.

8. Enter a source event id.  Say the event you're interested in using for source times of conflicts is [https://www.facebook.com/events/1567576990198712/](https://www.facebook.com/events/1567576990198712/).  The event id is `1567576990198712`.  Assign this to the `EVENT_ID` variable, as an int or a string.

9. Run the local server

	```
	$ python fomoist.py
	```

# Usage

1. The first run will be slow, because we need to do all the Facebook querying.  Go to [http://127.0.0.1:5000/write_to_cache](http://127.0.0.1:5000/write_to_cache) and wait...
2. Once you see "Done!" in the browser, go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/).
3. Shame on these fomoists!
4. If you want to change the source event id, you'll have to hit [http://127.0.0.1:5000/write_to_cache](http://127.0.0.1:5000/write_to_cache) again because you need to write new data to the db.
5. Auth tokens expire every couple hours.  When yours does, get a new one and replace the variable assignment.



# TODO

- [ ] Dynamic source event ID
- [ ] UI
- [ ] Display and link to conflicting events for each discovered fomoist
- [ ] Dynamic location, not hard-coded lat/lon
- [ ] Filter to friends
- [ ] Show conflicts only with a specific source event (most useful for event organizers)
- [ ] Make into a real FB app

# Made by

* [bsans](https://github.com/bsans)
* [ibrt](https://github.com/ibrt)
* [alex](alex)
* [jeremy](jeremy)

This project was made as part of the [Stupid Shit No One Needs & Terrible Ideas Hackathon](http://stupidhackathon.github.io/) in San Francisco, May 9-10, 2015.

It's useless and fantastic.

### License

[Beer-ware](http://en.wikipedia.org/wiki/Beerware)

```
/*
 * ----------------------------------------------------------------------------
 * "THE BEER-WARE LICENSE" (Revision 42):
 * bsans wrote this file.  As long as you retain this notice you
 * can do whatever you want with this stuff. If we meet some day, and you think
 * this stuff is worth it, you can buy me a beer in return.   Bodhi
 * ----------------------------------------------------------------------------
 */
 ```
