# Yorkie

[Yorkie](https://yorkie.city) is a fast, accurate train tracking service for New York City built with React, Flask, and SQLite. It utilizes [Andrew Dickinson's excellent Python wrapper](https://github.com/Andrew-Dickinson/nyct-gtfs/tree/master/nyct_gtfs) for official [official MTA API](https://api.mta.info/#/landing). Users can register accounts and track up to four stations at a time.

![Photo of a Yorkie monitor at De Kalb avenue](https://i.imgur.com/qMcBX6j.png) 

# Local use

If you would like to run Yorkie locally, you will need to host:
  - This repository (Satisfy package requirements via `requirements.txt` and then run `flask --app flaskr run`)
  - The [front-end](https://github.com/jajego/yorkie-frontend)

You will also need to get a free MTA API Key at https://api.mta.info/.




