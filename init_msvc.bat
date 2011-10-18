set path=%cd%\msys\1.0\bin;%cd%\shedskin;%PATH%
set SHEDSKIN_ROOT=%cd%\shedskin
set EXTRA_INCLUDE=%cd%\shedskin\extra_include
set EXTRA_LIB=%cd%\shedskin\extra_lib
cd %SHEDSKIN_ROOT%
%comspec% /k ""C:\Program Files\VC\vcvarsall.bat"" x86

