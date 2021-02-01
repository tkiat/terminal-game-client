#!/usr/bin/env python3
"""Simple CLI game client."""
from datetime import datetime
from pathlib import Path
import configparser
import curses
import curses.textpad
import json
import math
import os
import subprocess
import sys

def create_file_if_not_exist(path, content):
    '''Create file if and only if it does not exist'''
    pathlib = Path(path)
    if not pathlib.is_file():
        pathlib.touch()
        pathlib.write_text(content)

def draw_main_box(stdscr):
    '''Draw main box (below menu).'''
    height, width = stdscr.getmaxyx()
    win_main = curses.newwin(height - 3, width, 3, 0)
    win_main.border(0)
    win_main.refresh()
    return win_main

def draw_menu_box(cur):
    '''Draw menu box and highlight the current selection.'''
    x_pos = 0
    for index, text in enumerate(MENU):
        box = curses.newwin(3, len(text) + 2, 0, x_pos)
        box.addstr(1, 1, text)
        x_pos += len(text) + 3
        if index == cur:
            box.bkgd(' ', curses.color_pair(1))
        box.refresh()

def hhmmss_to_sec(hhmmss):
    '''Convert HH:MM:SS to seconds.'''
    hour, minute, second = hhmmss.split(':')
    return int(hour) * 3600 + int(minute) * 60 + int(second)

def play_game_and_record_time(row, cmd):
    '''Execute game and then record playtime thereafter.'''
    start = datetime.now()
    subprocess.Popen(cmd, stderr=subprocess.PIPE, \
            stdout=subprocess.DEVNULL).wait()
    playtime_sec = math.floor((datetime.now() - start).total_seconds())
    # update playtime
    GAMES[row]['playtime'] = \
            sec_to_hhmmss(hhmmss_to_sec(GAMES[row]['playtime']) + playtime_sec)
    RECORD_JSON[GAMES[row]['title']] = GAMES[row]['playtime']
    Path(RECORD_PATH).write_text(json.dumps(RECORD_JSON, sort_keys=True, indent=2))

def print_game_entries(window, cmd_game_prefix, row):
    '''Print all games entries.'''
    height, _ = window.getmaxyx()
    offset_x = MAX_PLAYTIME_DIGIT - len('hh:mm:ss')
    window.addstr(1, 2, 'Command Prefix: ' + cmd_game_prefix)
    window.addstr(3, 2 + offset_x, 'Playtime Title')
    linenum = 5

    max_game_per_page = height - 6  # height - 2 (top and bottom borders) - 4 (non-game entries)
    start_index = math.floor(row/max_game_per_page) * (max_game_per_page)
    end_index = min(len(GAMES) - 1, start_index + max_game_per_page - 1)

    for index in range(start_index, end_index + 1):
        if index == row: # highlight current row
            window.attron(curses.color_pair(1))
        offset_x = 2 + MAX_PLAYTIME_DIGIT - len(GAMES[index]['playtime'])
        window.addstr(linenum, offset_x, GAMES[index]['playtime'] + ' ' + GAMES[index]['title'])
        linenum += 1
        if index == row:
            window.attroff(curses.color_pair(1))
    window.refresh()

def sec_to_hhmmss(sec):
    '''Convert seconds to HH:MM:SS format.'''
    minute, second = divmod(sec, 60)
    hour, minute = divmod(minute, 60)
    return str(hour).zfill(2) + ":" + str(minute).zfill(2) + ":" + str(second).zfill(2)

def set_cmd_game_prefix():
    '''Enable textbox where user can type prefix command like wine64'''
    win = curses.newwin(1, 40, 4, 18)
    textbox = curses.textpad.Textbox(win)
    prefix = textbox.edit()
    del win
    return prefix

def clamp(number, range_min, range_max):
    '''Limit a number to a range.'''
    return max(min(number, range_max), range_min)
# --------------------------------------------------------------------------------------------------
def main(stdscr):
    '''Main function'''
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.mousemask(1)
    curses.curs_set(0)
    col_cur = 0
    row_game_cur = 0
    main_box = draw_main_box(stdscr)
    cmd_game_prefix = ""
    while 1:
        stdscr.keypad(1)
        stdscr.refresh()
        draw_menu_box(col_cur)
        main_box.clear()
        main_box.border(0)
        if MENU[col_cur] == "Games":
            print_game_entries(main_box, cmd_game_prefix, row_game_cur)
        elif MENU[col_cur] == "Record" or MENU[col_cur] == "Config" or MENU[col_cur] == "Help":
            main_box.addstr(1, 2, "Press ENTER to open file in " + str(EDITOR) + ".")
        main_box.refresh()

        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            break
        if key == 10 and MENU[col_cur] == "Games": # 10 = ENTER
            realpath = os.path.realpath(GAMES[row_game_cur]['path'])
            command = cmd_game_prefix + realpath
            play_game_and_record_time(row_game_cur, command)
        elif key == 10 and MENU[col_cur] == "Exit":
            break
        elif key == 10:
            subprocess.run([EDITOR, FILE_LIST[MENU[col_cur]]])
        elif key == curses.KEY_RESIZE:
            stdscr.erase()
            main_box = draw_main_box(stdscr)
        elif key in COL_VECTOR_MAP and GAMES:
            col_cur = clamp(col_cur + COL_VECTOR_MAP[key], 0, len(MENU) - 1)
        elif key in ROW_VECTOR_MAP and GAMES:
            row_game_cur = clamp(row_game_cur + ROW_VECTOR_MAP[key], 0, len(GAMES) - 1)
        elif key == ord('e'):
            cmd_game_prefix = set_cmd_game_prefix()
# --------------------------------------------------------------------------------------------------
# declare paths
FOLDER_PATH = os.path.expanduser("~") + "/.local/share/terminal-game-client/"
CONFIG_PATH = FOLDER_PATH + "config.conf"
RECORD_PATH = FOLDER_PATH + "playtime.json"
HELP_PATH = FOLDER_PATH + "help"
# create if not exist
os.makedirs(FOLDER_PATH, 0o755, exist_ok=True)
create_file_if_not_exist(CONFIG_PATH, """[DEFAULT]
# directoried containing symlinks to the game executables, put at least one space in front
directories =
 /home/tkiat/itch-io/Game
 /home/tkiat/GOG/Game
# editor to edit config or log files
editor = gedit
""")
create_file_if_not_exist(RECORD_PATH, """{}
""")
create_file_if_not_exist(HELP_PATH, """How to use
- Add Game: Make a folder entry in the configuration file.
This folder must contain symlinks to the actual game executables.
- Key Bindings: h (left), j (down), k (up), l (right), CTRL+d (down 20 lines),
CTRL+u (up 20 lines), ENTER (perform action).
- Configuration File: You can change game directories and editor in
~/.local/share/terminal-game-client/config.conf.
You should restart the application after changing it.
- Record File: You should restart the application after changing it.
- Command Prefix: Some games does not run without some prefixes like wine64.
Enter that in 'Command Prefix' section on the "Games" tab (press e, type command, then press ENTER).
""")
# read configs
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)
CONF = CONFIG['DEFAULT']
DIRECTORIES = list(filter(None, CONF.get("directories").split('\n')))
EDITOR = CONF.get("editor")
# read record
try:
    RECORD_JSON = json.loads(Path(RECORD_PATH).read_text())
except ValueError:
    print(RECORD_PATH + " is not a valid JSON. At least try to make it {}.")
    sys.exit()
MAX_PLAYTIME_DIGIT = 8 # hh:mm:ss
# iterate all directories
GAMES = []
for game_dir in DIRECTORIES:
    if os.path.isdir(game_dir):
        for f in os.listdir(game_dir):
            if f in RECORD_JSON and len(RECORD_JSON[f]) > MAX_PLAYTIME_DIGIT:
                MAX_PLAYTIME_DIGIT = len(RECORD_JSON[f])
            GAMES += [{'title': f, 'path': game_dir + '/' +  f, 'playtime': '00:00:00' \
                    if not f in RECORD_JSON else RECORD_JSON[f]}]
GAMES = sorted(GAMES, key=lambda i: i['title'].lower()) # sort by title
MENU = ["Games", "Record", "Config", "Help", "Exit"]
FILE_LIST = {"Record": RECORD_PATH, "Config": CONFIG_PATH, "Help": HELP_PATH}
# keymap
ROW_VECTOR_MAP = {curses.KEY_DOWN: 1, ord('j'): 1, curses.KEY_UP: -1, ord('k'): -1,\
        curses.ascii.ctrl(ord('d')): 20, curses.ascii.ctrl(ord('u')): -20}
COL_VECTOR_MAP = {curses.KEY_LEFT: -1, curses.KEY_RIGHT: 1, ord('h'): -1, ord('l'): 1}

if __name__ == '__main__':
    curses.wrapper(main)
