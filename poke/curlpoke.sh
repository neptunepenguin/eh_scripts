#!/bin/sh
# Script that pokes a website with a visit.
#   curlpoke.sh <cookie-file> <url>

# This must be a mozilla cookie file
COOKIES=${1:-curlpoke-cookies}
URL=${2:-http://example.com}

DATE=`date +%Y%m%d%H%M`

curl -b "$COOKIES"\
     -A "Mozilla/5.0 (X11; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0"\
     "$URL" > "poke-$DATE"
