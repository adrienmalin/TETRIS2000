for /F %%n in  ('dir /B *.ts') do pylupdate5 -verbose ..\..\..\python\game_gui.py -ts -noobsolete %%n
echo You may need to edit *.ts files with a text editor to correct special characters
pause
