#!/bin/sh

# super dirty chan crawler, downloads all images in a thread.

#cat 211.html |
curl $1 |
sed 's/File:/\nFile:/g' |
egrep 'File:\s*<a' |
sed 's/^File:\s*<a\s*href="/wget https:\/\/guroch.org\//;s/">.*/; sleep 1/' |
#cat
sh

