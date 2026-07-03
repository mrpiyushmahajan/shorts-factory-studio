@echo off
:: Windows Task Scheduler — Shorts Factory Studio
:: Run once to activate all loops.

set PYTHON=%~dp0..\venv\Scripts\python.exe
set ROOT=%~dp0..

echo Setting up Task Scheduler jobs...

:: ── Did You Know channel ────────────────────────────────────────────────────
schtasks /Create /TN "ShortsStudio_DYK_Noon"  /TR "\"%PYTHON%\" \"%ROOT%\daily_shorts.py\" --channel did_you_know" /SC DAILY /ST 12:00 /RL LIMITED /F
schtasks /Create /TN "ShortsStudio_DYK_5PM"   /TR "\"%PYTHON%\" \"%ROOT%\daily_shorts.py\" --channel did_you_know" /SC DAILY /ST 17:00 /RL LIMITED /F
schtasks /Create /TN "ShortsStudio_DYK_9PM"   /TR "\"%PYTHON%\" \"%ROOT%\daily_shorts.py\" --channel did_you_know" /SC DAILY /ST 21:00 /RL LIMITED /F

:: ── Desi Memes channel ──────────────────────────────────────────────────────
schtasks /Create /TN "ShortsStudio_Memes_1330" /TR "\"%PYTHON%\" \"%ROOT%\daily_shorts.py\" --channel desi_memes" /SC DAILY /ST 13:30 /RL LIMITED /F
schtasks /Create /TN "ShortsStudio_Memes_1830" /TR "\"%PYTHON%\" \"%ROOT%\daily_shorts.py\" --channel desi_memes" /SC DAILY /ST 18:30 /RL LIMITED /F
schtasks /Create /TN "ShortsStudio_Memes_2230" /TR "\"%PYTHON%\" \"%ROOT%\daily_shorts.py\" --channel desi_memes" /SC DAILY /ST 22:30 /RL LIMITED /F

:: ── Support loops ───────────────────────────────────────────────────────────
schtasks /Create /TN "ShortsStudio_CreatorStudy_DYK"   /TR "\"%PYTHON%\" \"%ROOT%\creator_study.py\" --channel did_you_know" /SC DAILY /ST 10:00 /RL LIMITED /F
schtasks /Create /TN "ShortsStudio_CreatorStudy_Memes" /TR "\"%PYTHON%\" \"%ROOT%\creator_study.py\" --channel desi_memes"  /SC DAILY /ST 10:30 /RL LIMITED /F
schtasks /Create /TN "ShortsStudio_Digest"    /TR "\"%PYTHON%\" \"%ROOT%\shorts_digest.py\""         /SC DAILY /ST 22:00 /RL LIMITED /F
schtasks /Create /TN "ShortsStudio_Learn_DYK" /TR "\"%PYTHON%\" \"%ROOT%\learn_and_improve.py\" --channel did_you_know" /SC WEEKLY /D SUN /ST 09:00 /RL LIMITED /F
schtasks /Create /TN "ShortsStudio_Learn_Memes"/TR "\"%PYTHON%\" \"%ROOT%\learn_and_improve.py\" --channel desi_memes"  /SC WEEKLY /D SUN /ST 09:30 /RL LIMITED /F

echo.
echo ✅ All tasks scheduled. Full schedule:
echo.
echo   12:00 / 17:00 / 21:00  →  Did You Know (facts)
echo   13:30 / 18:30 / 22:30  →  Desi Memes Daily (Hindi)
echo   10:00 / 10:30           →  CreatorStudy (each channel)
echo   22:00                   →  ShortsDigest email
echo   Sun 09:00 / 09:30       →  Weekly learning loop
echo.
echo To run a video manually:
echo   venv\Scripts\python daily_shorts.py --channel did_you_know
echo   venv\Scripts\python daily_shorts.py --channel desi_memes
echo.
pause
