import sqlite3
from contextlib import contextmanager
from pathlib import Path

PASTA_DADOS = Path.home() / "EstoqueTI"
PASTA_DADOS.mkdir(parents=True, exist_ok=True)
CAMINHO_BANCO = PASTA_DADOS / "estoque.db"


@contextmanager
def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    try:
        with conexao:
            yield conexao
    finally:
        conexao.close()


def inicializar():
    with conectar() as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL CHECK (TRIM(nome) <> ''),
                quantidade INTEGER NOT NULL DEFAULT 0
                    CHECK (
                        typeof(quantidade) = 'integer'
                        AND quantidade >= 0
                    ),
                codigo_intraweb TEXT UNIQUE
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY,
                produto_id INTEGER NOT NULL
                    REFERENCES produtos(id) ON DELETE RESTRICT,
                tipo TEXT NOT NULL
                    CHECK (tipo IN ('inicial', 'entrada', 'saida')),
                quantidade INTEGER NOT NULL
                    CHECK (
                        typeof(quantidade) = 'integer'
                        AND (
                            (tipo = 'inicial' AND quantidade >= 0)
                            OR
                            (tipo IN ('entrada', 'saida') AND quantidade > 0)
                        )
                    ),
                data_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                observacao TEXT NOT NULL DEFAULT ''
            )
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_movimentacoes_produto
            ON movimentacoes(produto_id)
        """)

        # Registra o saldo atual apenas para produtos sem histórico.
        conexao.execute("""
            INSERT INTO movimentacoes
                (produto_id, tipo, quantidade, observacao)
            SELECT p.id, 'inicial', p.quantidade,
                   'Saldo existente ao iniciar o histórico'
            FROM produtos AS p
            WHERE NOT EXISTS (
                SELECT 1
                FROM movimentacoes AS m
                WHERE m.produto_id = p.id
            )
        """)


def listar(busca=""):
    with conectar() as conexao:
        return conexao.execute("""
            SELECT id, nome, quantidade, codigo_intraweb
            FROM produtos
            WHERE INSTR(LOWER(nome), LOWER(?)) > 0
               OR INSTR(COALESCE(codigo_intraweb, ''), ?) > 0
            ORDER BY nome COLLATE NOCASE, id
        """, (busca, busca)).fetchall()


def salvar(nome, quantidade, codigo, produto_id=None):
    codigo = codigo or None

    with conectar() as conexao:
        if produto_id is None:
            resultado = conexao.execute("""
                INSERT INTO produtos (nome, quantidade, codigo_intraweb)
                VALUES (?, ?, ?)
            """, (nome, quantidade, codigo))

            conexao.execute("""
                INSERT INTO movimentacoes
                    (produto_id, tipo, quantidade, observacao)
                VALUES (?, 'inicial', ?, 'Saldo no cadastro do produto')
            """, (resultado.lastrowid, quantidade))
        else:
            # A edição do cadastro não modifica o saldo.
            conexao.execute("""
                UPDATE produtos
                SET nome = ?, codigo_intraweb = ?
                WHERE id = ?
            """, (nome, codigo, produto_id))


def excluir(produto_id):
    with conectar() as conexao:
        produto = conexao.execute(
            "SELECT quantidade FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()

        if produto is None:
            raise sqlite3.IntegrityError("Produto não encontrado.")

        registros = conexao.execute("""
            SELECT 1
            FROM movimentacoes
            WHERE produto_id = ?
              AND (tipo <> 'inicial' OR quantidade <> 0)
            LIMIT 1
        """, (produto_id,)).fetchone()

        if produto["quantidade"] != 0 or registros:
            raise sqlite3.IntegrityError(
                "Este produto possui saldo ou histórico de movimentações "
                "e não pode ser excluído."
            )

        # Permite excluir um cadastro vazio, sem movimentações reais.
        conexao.execute(
            "DELETE FROM movimentacoes WHERE produto_id = ?",
            (produto_id,),
        )
        conexao.execute(
            "DELETE FROM produtos WHERE id = ?",
            (produto_id,),
        )


def movimentar(produto_id, quantidade, tipo, observacao=""):
    if not isinstance(quantidade, int) or quantidade <= 0:
        raise ValueError("Informe uma quantidade inteira maior que zero.")

    if tipo not in ("entrada", "saida"):
        raise ValueError("Tipo de movimentação inválido.")

    with conectar() as conexao:
        if tipo == "entrada":
            resultado = conexao.execute("""
                UPDATE produtos
                SET quantidade = quantidade + ?
                WHERE id = ?
            """, (quantidade, produto_id))
        else:
            resultado = conexao.execute("""
                UPDATE produtos
                SET quantidade = quantidade - ?
                WHERE id = ? AND quantidade >= ?
            """, (quantidade, produto_id, quantidade))

        if resultado.rowcount == 0:
            raise ValueError(
                "Produto não encontrado ou saldo insuficiente."
            )

        conexao.execute("""
            INSERT INTO movimentacoes
                (produto_id, tipo, quantidade, observacao)
            VALUES (?, ?, ?, ?)
        """, (produto_id, tipo, quantidade, observacao.strip()))


def historico(produto_id):
    with conectar() as conexao:
        return conexao.execute("""
            SELECT
                strftime(
                    '%d/%m/%Y %H:%M:%S', data_hora, 'localtime'
                ) AS data,
                tipo,
                quantidade,
                observacao
            FROM movimentacoes
            WHERE produto_id = ?
            ORDER BY id DESC
        """, (produto_id,)).fetchall()