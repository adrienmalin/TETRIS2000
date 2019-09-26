#   ![icon](https://git.malingrey.fr/adrien/TETRIS2000/raw/branch/master/src/main/icons/linux/48.png "T") TETRIS 2000

Yet another Tetris clone, with Qt5 on Python 3

![screenshot](https://raw.githubusercontent.com/adrienmalin/TETRIS2000/gh-pages/screenshots/Tetris2000.png "Screenshot")

## Downloads

* [Linux archive](https://git.malingrey.fr/adrien/TETRIS2000/archive/V0.3.1_fbs.tar.gz) (78.3 MB)
* [Windows installer](https://github.com/adrienmalin/TETRIS2000/releases/download/V0.3.1_fbs/TETRIS2000Setup.exe) (53.6 MB)

## Build

* On Linux:

  ```shell
  mkdir TETRIS2000                                          # Create folder
  cd TETRIS2000                                             # Enter folder
  git clone https://git.malingrey.fr/adrien/TETRIS2000.git  # Clone repository
  python3 -m venv venv                                      # Create a virtual environment
  source venv/bin/activate                                  # Activate the virtual environment
  pip3 install -r requirements.txt                          # Install requirements
  python -m fbs run                                         # Run application
  python -m fbs freeze                                      # Freeze
  ```

* On Windows:

    Download and extract [source](https://git.malingrey.fr/adrien/TETRIS2000/archive/V0.3.1_fbs.zip).
    Open a command prompt and go to extracted directory
    
  ```batch
  REM Create and activate a virtual environment
  python -m venv venv
  call venv\scripts\activate.bat
  REM Install requirements
  pip install -r requirements.txt
  REM Run application
  python -m fbs run
  REM Create installer
  python -m fbs installer
  ```

## Credits

* [Tetris](https://tetris.com) Game Design by Alekseï Pajitnov
* Graphism inspired by [Tetris Effect](https://www.tetriseffect.game)
* Window style sheet: [qdarkstyle by Colin Duquesnoy](https://github.com/ColinDuquesnoy/QDarkStyleSheet)
* Fonts by [Markus Koellmann](http://markus-designs.com), [Peter Wiegel](http://www.peter-wiegel.de)
* Images from:<br>
  [OpenGameArt.org](https://opengameart.org) by beren77, Duion<br>
  [Pexels](https://www.pexels.com) by Min An, Jaymantri, Felix Mittermeier<br>
  [Pixabay](https://pixabay.com) by LoganArt<br>
  [PIXNIO](https://pixnio.com) by Adrian Pelletier<br>
  [Unsplash](https://unsplash.com) by Aron, Patrick Fore, Ilnur Kalimullin, Gabriel Garcia Marengo, Adnanta Raharja<br>
  [StockSnap.io](https://stocksnap.io) by Nathan Anderson, José Ignacio Pompé
* Musics from [Overclocked Remix](https://ocremix.org/game/510/tetris-gb) by:<br>
  CheDDer Nardz, djpretzel, MkVaff, Sir_NutS, R3FORGED, Sir_NutS
* Sound effects made with [voc-one by Simple-Media](http://www.simple-media.co.uk/vsti.htm)

## Thanks

Thanks to my pythonista friends [krakozaure](https://github.com/krakozaure) and ABR
