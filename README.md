# Steps to running project localhost

[Link docs TMDB](https://developer.themoviedb.org/docs/getting-started)

0. Clone to project
```https://github.com/miguel-124C/back-six-degrees-separation```

1. Copiar el ```.env.example``` y renombrarlo a ```.env``` y poner sus propias environments

2. Created environment virtual
```bash
python -m venv venv
```

3. Activated

- 1. In Windows
```bash
.\venv\Scripts\Activate
```
- 2. In Linux/Mac
```bash
source venv/bin/activate
```

4. Install dependecies
```bash
pip install -r requirements.txt
```

5. Levantar DB
```bash
docker compose up -d
```
Una vez levantado, si quiere ver la DB en la web, ir a http://localhost:8080

6. Execute app
```bash
py app.py
```

## Notas
Se requiere tener: Docker, Node v22, Python 3
Tambien tener un token de TMDB para hacer las busquedas