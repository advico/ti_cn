# Estoque TI — CN

Aplicativo desktop para controle de materiais e equipamentos de TI, desenvolvido em Python, com interface Tkinter e banco SQLite local. Permite consultar o estoque, registrar recebimentos e entregas e acompanhar o histórico de cada produto.

## Funcionalidades

- Cadastro de produto com nome, quantidade inicial e código do Intraweb opcional.
- Busca por nome ou código e edição do cadastro por botão ou duplo clique.
- Recebimento de estoque com origem obrigatória e observação opcional.
- Baixa por entrega com destinatário/setor obrigatórios, número do chamado opcional e observação adicional.
- Confirmação antes de efetivar entradas e saídas.
- Bloqueio de saídas maiores que o saldo disponível.
- Histórico por produto com saldo inicial, entradas, saídas, data, hora e observação.
- Persistência dos dados ao fechar o aplicativo.

## Tecnologias e organização

| Componente | Responsabilidade |
| --- | --- |
| Python | Lógica do aplicativo |
| Tkinter e ttk | Interface desktop |
| sqlite3 / SQLite | Consultas SQL, persistência e transações |
| `main.py` | Janelas, formulários e ações do usuário |
| `banco.py` | Criação das tabelas e operações no banco |
| `docs/UML.md` | Diagramas de sequência e modelo ER |
| `docs/casos-de-uso.puml` | Diagrama UML de casos de uso em PlantUML |

O programa usa a biblioteca padrão do Python; a execução não exige pacotes instalados por pip. O ambiente Python precisa incluir Tkinter.

## Como executar no Windows

Coloque `main.py` e `banco.py` na mesma pasta. Abra o terminal nessa pasta e crie um ambiente virtual:

```bash
python -m venv .venv
```

No Git Bash, execute diretamente o Python desse ambiente:

```bash
./.venv/Scripts/python.exe main.py
```

No PowerShell:

```powershell
.\.venv\Scripts\python.exe main.py
```

Se o ambiente já estiver ativado, basta `python main.py`. A primeira execução cria o banco e abre uma lista vazia para cadastro.

## Uso

1. Clique em **Novo**, informe produto, quantidade inicial e, se disponível, código do Intraweb; salve.
2. Selecione o produto e use **Receber estoque** para informar quantidade, origem e observação. Confirme o resumo.
3. Use **Dar baixa / Entregar** para informar quantidade, destinatário/setor, chamado e observação. Confirme a entrega.
4. Clique em **Histórico** para consultar os registros, do mais recente ao mais antigo.

Cancelar qualquer etapa anterior à confirmação final não altera o saldo. No formulário de edição, a quantidade é somente leitura: após o cadastro, alterações no saldo são feitas pelas movimentações.

## Regras de dados

- O nome é obrigatório. Nomes iguais são permitidos pela estrutura atual.
- Quantidades são inteiras; saldo e quantidade inicial não podem ser negativos.
- Entradas e saídas exigem quantidade maior que zero.
- O código do Intraweb é texto, preservando zeros à esquerda. Quando preenchido, é único; vários produtos podem ficar sem código.
- Saldo e registro no histórico são gravados na mesma transação. Se ocorrer uma falha, ambas as alterações são desfeitas.
- Só é permitida a exclusão de um cadastro com saldo zero e sem movimentações reais, cujo registro inicial também seja zero.
- Produtos existentes sem histórico recebem um registro inicial com seu saldo atual. Movimentações anteriores à implantação do histórico não são reconstruídas.

## Banco e backup

O arquivo é criado em `Path.home() / "EstoqueTI" / "estoque.db"`. No Windows, normalmente corresponde a:

```text
C:\Users\SEU_USUARIO\EstoqueTI\estoque.db
```

O banco fica separado do código. Para um backup manual, feche todas as instâncias do aplicativo e copie `estoque.db` para um local seguro. Para restaurar, feche o aplicativo, preserve uma cópia do banco atual e substitua-o pelo backup.

## Modelo e limitações atuais

Um produto possui vários registros em `movimentacoes`. O saldo atual é armazenado em `produtos.quantidade`. Destinatário, setor, origem e número do chamado são concatenados em `observacao`; ainda não são colunas separadas.

As datas são armazenadas em UTC e apresentadas no horário local do computador. A aplicação foi concebida para uso local; não possui autenticação, identificação do operador, sincronização entre computadores ou controle individual por número de série. O histórico exibe o nome atual do produto, sem guardar versões anteriores desse nome.

A busca usa `LOWER` do SQLite, que possui limitações de conversão de maiúsculas/minúsculas para caracteres acentuados. Não há busca sem acentos implementada.

## Diagramas

Consulte [UML e modelo de dados](docs/UML.md). Os diagramas Mermaid desse documento podem ser visualizados em renderizadores compatíveis. O [caso de uso em PlantUML](docs/casos-de-uso.puml) é fornecido como fonte editável e exige um renderizador PlantUML.

## Verificação manual

Use um banco de teste separado dos dados reais para conferir:

| Cenário | Resultado esperado |
| --- | --- |
| Cadastro com saldo 5 | Produto e registro inicial com 5 |
| Entrada de 3 | Saldo 8 e nova entrada no histórico |
| Saída de 2 com chamado | Saldo 6 e chamado na observação |
| Tentativa de saída de 7 | Operação bloqueada; saldo e histórico inalterados |
| Cancelar uma movimentação | Nenhuma alteração |
| Reabrir o aplicativo | Dados preservados; saldo inicial não duplicado |
| Repetir código do Intraweb | Cadastro rejeitado |
| Abrir Novo/Editar várias vezes | Botões de estoque não se multiplicam |

## Publicação e próximos passos

O `.gitignore` incluído exclui ambientes virtuais, bancos locais e artefatos de empacotamento. Publique apenas código e documentação; use dados fictícios em imagens de demonstração. O executável Windows será preparado e testado em uma etapa posterior e poderá ser distribuído em uma Release.

Possíveis evoluções: campos próprios para chamado e destinatário, arquivamento de produtos, exportação de relatórios e backup pela interface.

## Autoria

Adrian Correa — projeto de estudo e portfólio aplicado à rotina de suporte de TI.
