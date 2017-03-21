#!/bin/sh

UPLOAD_URL=https://upload.e-hentai.org/image_lookup.php
SIMILAR=''
COVER=''
EXPUNGED=''

# The last option is the file to be searched (ignore it for now)
while test $# -gt 1
do
  case $1 in
    -s)
        SIMILAR='-F fs_similar=1'
        shift
        ;;
    -c)
        COVER='-F fs_covers=1'
        shift
        ;;
    -e)
        EXPUNGED='-F fs_exp=1'
        shift
        ;;
    *)
        echo "WARNING: unknown option: $1"
        shift
        ;;
  esac
done

if test "x$1" != "x" -a -r "$1"
then
    base=`basename "$1"`
    # Note that `file` is not part of POSIX, may not be available
    img_type=`file --mime-type "$1" | cut -d: -f2 | xargs echo`
    curl -i -F "sfile=@\"$1\";filename=\"$base\";type=$img_type" \
            $SIMILAR $COVER $EXPUNGED $UPLOAD_URL
else
    echo "Usage: $0 [-s] [-c] [-e] file-to-seach-for"
    echo "       -s  similarity search"
    echo "       -c  search covers only"
    echo "       -e  show expunged"
fi

