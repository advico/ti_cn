import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import banco


def atualizar_lista(*_):
    try:
        produtos = banco.listar(busca.get().strip())
    except sqlite3.Error as erro:
        messagebox.showerror("Erro ao consultar", str(erro), parent=janela)
        return

    for linha in tabela.get_children():
        tabela.delete(linha)

    for produto in produtos:
        tabela.insert(
            "",
            "end",
            iid=str(produto["id"]),
            values=(
                produto["nome"],
                produto["quantidade"],
                produto["codigo_intraweb"] or "",
            ),
        )

    status.set(f"{len(produtos)} produto(s) na lista")


def obter_selecionado():
    selecao = tabela.selection()

    if not selecao:
        messagebox.showinfo(
            "Selecione um produto",
            "Clique em um produto da tabela primeiro.",
            parent=janela,
        )
        return None

    return selecao[0]


def abrir_formulario(editar=False):
    produto_id = None
    valores = ("", 0, "")

    if editar:
        selecionado = obter_selecionado()
        if selecionado is None:
            return

        produto_id = int(selecionado)
        valores = tabela.item(selecionado, "values")

    formulario = tk.Toplevel(janela)
    formulario.title("Editar produto" if editar else "Novo produto")
    formulario.resizable(False, False)
    formulario.transient(janela)
    formulario.grab_set()

    campos = ttk.Frame(formulario, padding=20)
    campos.pack(fill="both", expand=True)

    nome_var = tk.StringVar(value=valores[0])
    quantidade_var = tk.StringVar(value=str(valores[1]))
    codigo_var = tk.StringVar(value=valores[2])

    ttk.Label(campos, text="Produto").grid(
        row=0, column=0, sticky="w"
    )
    entrada_nome = ttk.Entry(campos, textvariable=nome_var, width=45)
    entrada_nome.grid(row=1, column=0, sticky="ew", pady=(4, 12))

    ttk.Label(campos, text="Quantidade").grid(
        row=2, column=0, sticky="w"
    )
    ttk.Entry(
    campos,
    textvariable=quantidade_var,
    state="readonly" if editar else "normal",
    ).grid(
    row=3, column=0, sticky="ew", pady=(4, 12)
     )

    ttk.Label(campos, text="Código do Intraweb (opcional)").grid(
        row=4, column=0, sticky="w"
    )
    ttk.Entry(campos, textvariable=codigo_var).grid(
        row=5, column=0, sticky="ew", pady=(4, 16)
    )

    def confirmar():
        nome = nome_var.get().strip()
        codigo = codigo_var.get().strip()

        if not nome:
            messagebox.showwarning(
                "Nome obrigatório",
                "Informe o nome do produto.",
                parent=formulario,
            )
            return

        try:
            quantidade = int(quantidade_var.get().strip())
            if quantidade < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Quantidade inválida",
                "Informe um número inteiro igual ou maior que zero.",
                parent=formulario,
            )
            return

        try:
            banco.salvar(nome, quantidade, codigo, produto_id)
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Cadastro não salvo",
                "Verifique os dados. O código do Intraweb "
                "não pode estar cadastrado em outro produto.",
                parent=formulario,
            )
            return
        except (sqlite3.Error, OverflowError) as erro:
            messagebox.showerror(
                "Erro ao salvar", str(erro), parent=formulario
            )
            return

        formulario.destroy()
        atualizar_lista()

    botoes = ttk.Frame(campos)
    botoes.grid(row=6, column=0, sticky="e")

    ttk.Button(
        botoes,
        text="Cancelar",
        command=formulario.destroy,
    ).pack(side="left", padx=(0, 8))

    ttk.Button(
        botoes,
        text="Salvar",
        command=confirmar,
    ).pack(side="left")

    formulario.bind("<Return>", lambda evento: confirmar())
    formulario.bind("<Escape>", lambda evento: formulario.destroy())
    entrada_nome.focus_set()


def excluir_produto():
    selecionado = obter_selecionado()
    if selecionado is None:
        return

    nome = tabela.item(selecionado, "values")[0]

    confirmar = messagebox.askyesno(
        "Excluir produto",
        f'Deseja excluir "{nome}"?\n\nEssa ação não pode ser desfeita.',
        parent=janela,
    )

    if confirmar:
        try:
            banco.excluir(int(selecionado))
        except sqlite3.Error as erro:
            messagebox.showerror(
                "Erro ao excluir", str(erro), parent=janela
            )
            return

        atualizar_lista()

def movimentar_estoque(tipo):
    selecionado = obter_selecionado()
    if selecionado is None:
        return

    nome = tabela.item(selecionado, "values")[0]
    saida = tipo == "saida"

    titulo = "Dar baixa / Entregar" if saida else "Receber estoque"

    quantidade = simpledialog.askinteger(
        titulo,
        f"Produto: {nome}\n\nQuantidade de unidades:",
        parent=janela,
        minvalue=1,
        maxvalue=2147483647,
    )

    if quantidade is None:
        return

    # Solicita quem recebeu ou de onde veio o material.
    pergunta = (
        "Informe o nome do usuário que recebeu e o setor:"
        if saida
        else "Informe a origem: fornecedor, compra ou devolução:"
    )

    while True:
        identificacao = simpledialog.askstring(
            titulo,
            pergunta,
            parent=janela,
        )

        if identificacao is None:
            return

        identificacao = identificacao.strip()

        if identificacao:
            break

        messagebox.showwarning(
            "Informação obrigatória",
            "Preencha essa informação para registrar a movimentação.",
            parent=janela,
        )

    numero_chamado = ""

    if saida:
        numero_chamado = simpledialog.askstring(
            "Nº do chamado",
            "Informe o número do chamado (opcional):",
            parent=janela,
        )

        if numero_chamado is None:
            return

        numero_chamado = numero_chamado.strip()

    detalhe = simpledialog.askstring(
        titulo,
        "Observação adicional (opcional):\n"
        "Ex.: chamado, nota fiscal, patrimônio ou motivo.",
        parent=janela,
    )

    if detalhe is None:
        return

    prefixo = "Entregue para" if saida else "Origem"
    observacao = f"{prefixo}: {identificacao}"
    if numero_chamado:
        observacao += f" | Nº do chamado: {numero_chamado}"

    if detalhe.strip():
        observacao += f" | {detalhe.strip()}"

    confirmar = messagebox.askyesno(
        "Confirmar movimentação",
        f"Produto: {nome}\n"
        f"Operação: {'Saída' if saida else 'Entrada'}\n"
        f"Quantidade: {quantidade}\n\n"
        f"{observacao}\n\n"
        "Confirmar o registro?",
        parent=janela,
    )

    if not confirmar:
        return

    try:
        banco.movimentar(
            int(selecionado),
            quantidade,
            tipo,
            observacao,
        )
    except ValueError as erro:
        messagebox.showwarning(
            "Movimentação não realizada",
            str(erro),
            parent=janela,
        )
        return
    except sqlite3.Error as erro:
        messagebox.showerror(
            "Erro ao registrar",
            str(erro),
            parent=janela,
        )
        return

    atualizar_lista()

    if tabela.exists(selecionado):
        tabela.selection_set(selecionado)
        tabela.focus(selecionado)
        tabela.see(selecionado)

    messagebox.showinfo(
        "Movimentação registrada",
        "O estoque foi atualizado e o registro foi salvo no histórico.",
        parent=janela,
    )


def mostrar_historico():
    selecionado = obter_selecionado()
    if selecionado is None:
        return

    produto_id = int(selecionado)
    nome = tabela.item(selecionado, "values")[0]

    try:
        registros = banco.historico(produto_id)
    except sqlite3.Error as erro:
        messagebox.showerror(
            "Erro ao consultar histórico", str(erro), parent=janela
        )
        return

    tela = tk.Toplevel(janela)
    tela.title(f"Histórico — {nome}")
    tela.geometry("850x450")
    tela.transient(janela)

    ttk.Label(
        tela,
        text=nome,
        font=("Segoe UI", 14, "bold"),
    ).pack(anchor="w", padx=16, pady=16)

    area = ttk.Frame(tela)
    area.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    lista = ttk.Treeview(
        area,
        columns=("data", "tipo", "quantidade", "observacao"),
        show="headings",
    )

    for coluna, titulo, largura in [
        ("data", "Data e hora", 160),
        ("tipo", "Tipo", 100),
        ("quantidade", "Quantidade", 90),
        ("observacao", "Observação", 350),
    ]:
        lista.heading(coluna, text=titulo)
        lista.column(coluna, width=largura, minwidth=70)

    lista.column("quantidade", anchor="center")

    rolagem = ttk.Scrollbar(
        area, orient="vertical", command=lista.yview
    )
    lista.configure(yscrollcommand=rolagem.set)

    rolagem.pack(side="right", fill="y")
    lista.pack(side="left", fill="both", expand=True)

    nomes_tipos = {
        "inicial": "Saldo inicial",
        "entrada": "Entrada",
        "saida": "Saída",
    }

    for registro in registros:
        lista.insert(
            "",
            "end",
            values=(
                registro["data"],
                nomes_tipos[registro["tipo"]],
                registro["quantidade"],
                registro["observacao"],
            ),
        )

janela = tk.Tk()
janela.title("Estoque TI — CN")
janela.geometry("950x600")
janela.minsize(750, 400)

estilo = ttk.Style()
estilo.configure("Treeview", rowheight=28)

conteudo = ttk.Frame(janela, padding=20)
conteudo.pack(fill="both", expand=True)

ttk.Label(
    conteudo,
    text="Estoque de TI",
    font=("Segoe UI", 20, "bold"),
).pack(anchor="w", pady=(0, 16))

# Barra de busca e ações.
barra = ttk.Frame(conteudo)
barra.pack(fill="x", pady=(0, 12))

ttk.Label(barra, text="Buscar:").pack(side="left", padx=(0, 8))

busca = tk.StringVar()
ttk.Entry(barra, textvariable=busca).pack(
    side="left", fill="x", expand=True, padx=(0, 12)
)

ttk.Button(
    barra, text="Novo", command=abrir_formulario
).pack(side="left", padx=4)

ttk.Button(
    barra, text="Editar", command=lambda: abrir_formulario(True)
).pack(side="left", padx=4)

ttk.Button(
    barra, text="Excluir", command=excluir_produto
).pack(side="left", padx=(4, 0))

# Tabela.
area_tabela = ttk.Frame(conteudo)
area_tabela.pack(fill="both", expand=True)

tabela = ttk.Treeview(
    area_tabela,
    columns=("produto", "quantidade", "codigo"),
    show="headings",
    selectmode="browse",
)

tabela.heading("produto", text="Produto")
tabela.heading("quantidade", text="Quantidade")
tabela.heading("codigo", text="Código do Intraweb")

tabela.column("produto", width=450, minwidth=250)
tabela.column(
    "quantidade", width=100, minwidth=90,
    anchor="center", stretch=False
)
tabela.column("codigo", width=200, minwidth=150, anchor="center")

rolagem = ttk.Scrollbar(
    area_tabela, orient="vertical", command=tabela.yview
)
tabela.configure(yscrollcommand=rolagem.set)

rolagem.pack(side="right", fill="y")
tabela.pack(side="left", fill="both", expand=True)

tabela.bind("<Double-1>", lambda evento: abrir_formulario(True))

acoes_estoque = ttk.Frame(conteudo)
acoes_estoque.pack(fill="x", pady=(12, 0))

ttk.Button(
    acoes_estoque,
    text="+ Receber estoque",
    command=lambda: movimentar_estoque("entrada"),
).pack(side="left", padx=(0, 8))

ttk.Button(
    acoes_estoque,
    text="− Dar baixa / Entregar",
    command=lambda: movimentar_estoque("saida"),
).pack(side="left")

ttk.Button(
    acoes_estoque,
    text="Histórico",
    command=mostrar_historico,
).pack(side="left", padx=(8, 0))

status = tk.StringVar()
ttk.Label(conteudo, textvariable=status).pack(
    anchor="w", pady=(12, 0)
)

busca.trace_add("write", atualizar_lista)

if __name__ == "__main__":
    try:
        banco.inicializar()
    except sqlite3.Error as erro:
        messagebox.showerror(
            "Erro ao abrir o banco", str(erro), parent=janela
        )
        janela.destroy()
    else:
        atualizar_lista()
        janela.mainloop()