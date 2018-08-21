#   ![T](../raw/master/icons/48.png "T") TETRIS 2000

Yet another Tetris clone, with Qt5 on Python 3

![Screenshot](../raw/gh-pages/screenshots/Tetris2000.png "Screenshot")

## Installation

* [Download archive](../archive/master.zip) (34 Mo)
* Extract the archive
* Launch Tetris2000

## Build

* Install [Python 3](https://www.python.org) with pip

* Install PyQt5 or PySide2, qdarkstyle, and nuitka: (Nota: qdarkstyle don't support PySIde2 yet)

    ```bash
    pip3 install --user PyQt5
    pip3 install --user qdarkstyle
    pip3 install --user nuitka
    ```
  
* Clone repository:

    ```bash
    mkdir TETRIS2000
    cd TETRIS2000
    git clone https://github.com/adrienmalin/Tetris2000
    ```
    
* Build:

    ```bash
    python3 -m nuitka  Tetris2000.py --recurse-all
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
