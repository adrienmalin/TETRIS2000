for /F %%n in  ('dir /B *.ts') do pylupdate5 -verbose ..\window.py ..\settings.py ..\stats.py ..\matrix.py ..\frames.py -ts %%n
echo You may need to edit *.ts files with a text editor to correct special characters
pause
