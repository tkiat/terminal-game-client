# Terminal Game Client

### Motivation
- Game client like Steam doesn't show playtime in detail (hh:mm:ss) so I, a command-line junkie, build this script.

### Requirement
- Linux. Python 3. curses library.

### Feature
- **Simple and Lightweight**: A terminal-based app with only 5 menus.
- **Simple Yet Detailed Stats**: Playtime by game in hh:mm:ss.
- **Easy Configs**: Open config and record files directly from the application. You can supply additional commands like wine64 with ease.

### How to use
- **Add Game**: Make a folder entry in the configuration file. This folder must contain symlinks to the actual game executables.
- **Key Bindings**: h (left), j (down), k (up), l (right), CTRL+d (down 20 lines), CTRL+u (up 20 lines), ENTER (perform action).
- **Configuration File**: You can change game directories and editor in ~/.local/share/terminal-game-client/config.conf.
- **Record File**: You should restart the application after changing it.
- **Prefix Command**: Some games does not run without some prefixes like wine64. Enter that in 'Command Prefix' section on the "Games" tab (press e, type command, then press ENTER).

### Screenshots

![img](/screenshots/1.png)
![img](/screenshots/2.png)
![img](/screenshots/3.png)
