#!/usr/bin/env python3
from datetime import date, datetime
from pathlib import Path
import configparser
import curses
import curses.textpad
import json
import math
import os
import subprocess
import sys
import time

def create_file_if_not_exist(path, content):
    p = Path(path)
    if not p.is_file():
        p.touch()
        p.write_text(content)

def draw_main_box(stdscr):
    h, w = stdscr.getmaxyx()
    win_main = curses.newwin(h - 3, w, 3, 0)
    win_main.border(0)
    win_main.refresh()
    return win_main

def draw_menu_box(stdscr, cur):
    x = 0
    boxes = []
    for index, text in enumerate(menu):
        box = curses.newwin(3, len(text) + 2, 0, x)
        box.addstr(1, 1, text)
        x += len(text) + 3
        if index == cur:
            box.bkgd(' ', curses.color_pair(1))
        box.refresh()

def hhmmss_to_sec(hhmmss):
    h, m, s = hhmmss.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def print_game_entries(window, cmd_game_prefix, row):
    global games
    h, w = window.getmaxyx()
    offset_x = max_playtime_digit - len('hh:mm:ss')
    window.addstr(1, 2, 'Command Prefix: ' + cmd_game_prefix)
    window.addstr(3, 2 + offset_x, 'Playtime Title')
    linenum = 5

    max_game_per_page = h - 6  # h - 2 (top and bottom borders) - 4 (non-game entries)
    start_index = math.floor(row/max_game_per_page) * (max_game_per_page)
    end_index = min(len(games) - 1, start_index + max_game_per_page - 1)

    for index in range(start_index, end_index + 1):
        if index == row: # highlight current row
            window.attron(curses.color_pair(1))
        offset_x = 2 + max_playtime_digit - len(games[index]['playtime'])
        window.addstr(linenum, offset_x, games[index]['playtime'] + ' ' + games[index]['title'])
        linenum += 1
        if index == row:
            window.attroff(curses.color_pair(1))
    window.refresh()

def sec_to_hhmmss(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return str(h).zfill(2) + ":" + str(m).zfill(2) + ":" + str(s).zfill(2)
# ----------------------------------------------------------------------------------------------------
def main(stdscr):
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
        draw_menu_box(stdscr, col_cur)

        main_box.clear()
        main_box.border(0)
        if menu[col_cur] == "Games":
            print_game_entries(main_box, cmd_game_prefix, row_game_cur)
        elif menu[col_cur] == "Exit":
            pass
        else:
            main_box.addstr(1, 2, "Press ENTER to open file in " + str(editor) + ".")
        main_box.refresh()

        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            break

        if key == 10: # ENTER
            if menu[col_cur] == "Games":
                start = datetime.now()
                realpath = os.path.realpath(games[row_game_cur]['path'])
                cmd = cmd_game_prefix + realpath
                subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL).wait()
                playtime_sec = math.floor((datetime.now() - start).total_seconds())
                title = games[row_game_cur]['title']
                games[row_game_cur]['playtime'] = sec_to_hhmmss(hhmmss_to_sec(games[row_game_cur]['playtime']) + playtime_sec)
                record_json[title] = games[row_game_cur]['playtime']
                Path(record_path).write_text(json.dumps(record_json, sort_keys=True, indent=2))
            elif menu[col_cur] == "Record":
                subprocess.run([editor, record_path])
            elif menu[col_cur] == "Config":
                subprocess.run([editor, config_path])
            elif menu[col_cur] == "Help":
                subprocess.run([editor, help_path])
            elif menu[col_cur] == "Exit":
                break
        elif key == curses.KEY_RESIZE:
            stdscr.erase()
            main_box = draw_main_box(stdscr)
        elif (key == curses.KEY_LEFT or key == ord('h')):
            col_cur = (col_cur - 1) % len(menu)
        elif (key == curses.KEY_RIGHT or key == ord('l')):
            col_cur = (col_cur + 1) % len(menu)
        elif (key == curses.KEY_DOWN or key == ord('j')) and len(games) > 0:
            row_game_cur = (row_game_cur + 1) % len(games)
        elif (key == curses.KEY_UP or key == ord('k')) and len(games) > 0:
            row_game_cur = (row_game_cur - 1) % len(games)
        elif key == curses.ascii.ctrl(ord('d')) and len(games) > 0:
            row_game_cur = (row_game_cur + 20) % len(games)
        elif key == curses.ascii.ctrl(ord('u')) and len(games) > 0:
            row_game_cur = (row_game_cur - 20) % len(games)
        elif key == ord('e'):
            win = curses.newwin(1, 40, 4, 18)
            tb = curses.textpad.Textbox(win)
            cmd_game_prefix = tb.edit()
            del win
# ----------------------------------------------------------------------------------------------------
# declare paths
folder_path = os.path.expanduser("~") + "/.local/share/terminal-game-client/"
config_path = folder_path + "config.conf"
record_path = folder_path + "playtime.json"
help_path = folder_path + "help"
# create if not exist
os.makedirs(folder_path, 0o755, exist_ok=True)
create_file_if_not_exist(config_path, """[DEFAULT]
# directoried containing symlinks to the game executables, put at least one space in front
directories =
 /home/tkiat/itch-io/Game
 /home/tkiat/GOG/Game
# editor to edit config or log files
editor = gedit
""")
create_file_if_not_exist(record_path, """{}
""")
create_file_if_not_exist(help_path,"""How to use
- Add Game: Make a folder entry in the configuration file. This folder must contain symlinks to the actual game executables.
- Key Bindings: h (left), j (down), k (up), l (right), CTRL+d (down 20 lines), CTRL+u (up 20 lines), ENTER (perform action).
- Configuration File: You can change game directories and editor in ~/.local/share/terminal-game-client/config.conf. You should restart the application after changing it.
- Record File: You should restart the application after changing it.
- Prefix Command: Some games does not run without some prefixes like wine64. Enter that in 'Command Prefix' section on the "Games" tab (press e, type command, then press ENTER).
""")
# read configs
config = configparser.ConfigParser()
config.read(config_path)
conf = config['DEFAULT']
directories = list(filter(None, conf.get("directories").split('\n')))
editor = conf.get("editor")
# read record
record_content = Path(record_path).read_text()
try:
    record_json = json.loads(record_content)
except ValueError:
    print(record_path + " is not a valid JSON. At least try to make it {}.")
    sys.exit()
max_playtime_digit = 8 # hh:mm:ss
# iterate all directories
games = []
for game_dir in directories:
    if os.path.isdir(game_dir):
        for f in os.listdir(game_dir):
            if f in record_json and len(record_json[f]) > max_playtime_digit:
                max_playtime_digit = len(record_json[f])
            games += [{'title': f, 'path': game_dir + '/' +  f, 'playtime': '00:00:00' if not f in record_json else record_json[f]}]
# sort by title
games = sorted(games, key = lambda i : i['title'].lower())
menu = ["Games", "Record", "Config", "Help", "Exit"]

if __name__ == '__main__':
    curses.wrapper(main)
