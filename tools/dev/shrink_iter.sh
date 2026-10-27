#!/bin/sh
# usage: it.sh scene cutbytes -> writes shr/<scene>.py, compiles to shrc
S=$1; C=$2
mkdir -p shr$S shrc$S
python3 /home/claude/h/work/tools/shrink_scene.py /home/claude/h/work/orig/psp/scripts_SN/$S.py al/$S.py shr$S/$S.py $C
sh /home/claude/h/work/tools/compile_all.sh /home/claude/w/shr$S /home/claude/w/shrc$S >/dev/null
ls -l shrc$S/$S._SN | awk '{print $5}'
