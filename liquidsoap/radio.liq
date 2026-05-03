#!/usr/bin/liquidsoap

settings.init.allow_root := true
source = mksafe(playlist("music/"))

output.icecast(
  %mp3,
  host = "localhost",
  port = 8000,
  password = "mds",
  mount = "/radio",
  source
)
