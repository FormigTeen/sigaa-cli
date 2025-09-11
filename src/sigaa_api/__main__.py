import argparse
from sigaa_api.core import saudacao   # import relativo dentro do pacote

def main():
    p = argparse.ArgumentParser(prog="formigteen-bot")
    p.add_argument("--nome", default="mundo")
    args = p.parse_args()
    print(saudacao(args.nome))

if __name__ == "__main__":
    main()
