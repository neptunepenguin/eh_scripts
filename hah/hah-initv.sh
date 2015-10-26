#!/bin/sh

HHPATH=/path/to/hath
LOG=$HHPATH/hhrestart.log

start () {
  local d=$(date +%Y%m%d%H%M%S)
  if ! ps -afe | grep [H]entaiAtHome >/dev/null; then
    echo "$d: restarting H@H, as it is not running" >> $LOG
    cd $HHPATH
    java -jar HentaiAtHome.jar --use_more_memory &
  else
    # you may wish to kill this entire else
    echo "$d: H@H running, all is OK" >> $LOG
  fi
}

stop () {
  local pid=$(ps -afe | grep [H]entaiAtHome | tr -s ' ' | cut -d ' ' -f 2)
  local d=$(date +%Y%m%d%H%M%S)
  echo "$d: killed H@H ($pid) because the cache cannot be found" >> $LOG
  kill $pid
}

while ((1)); do
  if [[ -d $HHPATH/cache ]]; then
    start
  else
    stop
  fi
  sleep 30
done

