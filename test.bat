@echo off
:: ─── Запуск тестов для всех сервисов (Windows) ───────────────────────────
:: Использование:
::   test.bat              — все сервисы
::   test.bat menu         — только menu-service
::   test.bat warehouse    — только warehouse-service
::   test.bat order        — только order-service
::   test.bat auth         — только auth-service

setlocal

if "%1"=="menu"      goto menu
if "%1"=="warehouse" goto warehouse
if "%1"=="order"     goto order
if "%1"=="auth"      goto auth
if "%1"==""          goto all

echo Неизвестный аргумент: %1
echo Использование: test.bat [menu^|warehouse^|order^|auth]
exit /b 1

:all
echo === menu-service ===
call :run_tests menu-service
if errorlevel 1 exit /b 1

echo.
echo === warehouse-service ===
call :run_tests warehouse-service
if errorlevel 1 exit /b 1

echo.
echo === order-service ===
call :run_tests order-service
if errorlevel 1 exit /b 1

echo.
echo === auth-service ===
call :run_tests auth-service
if errorlevel 1 exit /b 1

echo.
echo Testi proshli uspeshno.
exit /b 0

:menu
call :run_tests menu-service
exit /b %errorlevel%

:warehouse
call :run_tests warehouse-service
exit /b %errorlevel%

:order
call :run_tests order-service
exit /b %errorlevel%

:auth
call :run_tests auth-service
exit /b %errorlevel%

:run_tests
pushd services\%1
python -m pytest tests\ -v --no-cov --tb=short
popd
exit /b %errorlevel%
