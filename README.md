# Rinha de Compilers 

Essa solucão utiliza o framework LLVM para gerar uma representação intermediaria da [AST da rinha](https://github.com/aripiprazole/rinha-de-compiler/blob/main/SPECS.md), aplica otimizacões e gera o executável para a maquina alvo

## requirements

- python3
- llvm
- clang

## run

### local

```
pip install llvmlite
```

```
python main.py
```

:warning: **tenha certeza de ter o arquivo /var/rinha/source.rinha.json antes de executar o script**

### docker

```
docker build -t rinha .
```

```
docker run --rm -v ./files/fib.json:/var/rinha/source.rinha.json rinha
```