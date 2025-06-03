# Használj egy egyszerű Python image-et
FROM python:3.9-slim

# Munkakönyvtár beállítása a konténeren belül
WORKDIR /usr/src/app

# Ide másolhatod a tesztelő segédprogramot az image buildeléskor
COPY test_harness.py .
# A fenti sor a test_harness.py-t a build kontextusból (ahol a Dockerfile van)
# a WORKDIR-be (/usr/src/app) másolja az image-en belül.

# Hozz létre egy nem-root felhasználót a biztonság növelése érdekében
RUN useradd -ms /bin/bash -u 1001 code_runner
# USER code_runner # Futtatás ezzel a userrel (a docker run parancsban is megadható)