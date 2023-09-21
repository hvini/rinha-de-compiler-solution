# Rinha de Compilers 

This solution uses llvm to generate a IR representation of [rinha AST](https://github.com/aripiprazole/rinha-de-compiler/blob/main/SPECS.md), optimizes the generated IR and finally generates the target code

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

### docker

```
docker build -t rinha .
```

```
docker run --rm -v ./files/fib.json:/var/rinha/source.rinha.json rinha
```