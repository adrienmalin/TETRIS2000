for /F %%n in  ('dir /B *.ts') do pylupdate5 ..\game_gui.py -ts -noobsolete %%n
pause
