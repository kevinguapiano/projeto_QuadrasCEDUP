import flet as ft
import urllib.parse

# =====================================================================
# BANCO DE DADOS (EM MEMÓRIA)
# Lista global começa vazia, onde as quadras cadastradas pelo gestor ficam armazenadas
# =====================================================================
bd_quadras = []

# Variável global pra guardar a sessão do usuário logado:
# Pode ser: None (não logado), "jogador" ou "gestor"
sessao_usuario = {"tipo": None}

def main(page: ft.Page):
    # Configurações globais da janela do Flet (Design e Tema)
    page.title = "Quadra Search - Lages"
    page.theme_mode = ft.ThemeMode.DARK 
    
    # Estado da busca na tela inicial (texto digitado e filtro de categoria ativo)
    estado_busca = {"filtro_ativo": None, "texto": ""}

    # Função auxiliar para trocar de rota/página de forma segura e forçar atualização da tela
    def navegar(rota):
        page.route = rota
        page.update()
        mudar_rota(None)

    # Função para excluir uma quadra pelo seu ID do banco de dados fake, exclusiva do perfil gestor
    def excluir_quadra(e, q_id):
        global bd_quadras
        # Mantém na lista apenas as quadras cujo ID seja diferente do ID selecionado pelo gestor para exclusão
        bd_quadras = [q for q in bd_quadras if q["id"] != q_id]
        mudar_rota(None)

    # Função de logout: limpa a sessão e retorna à tela de login
    def fazer_logout(e):
        sessao_usuario["tipo"] = None
        navegar("/")

    # =====================================================================
    # TELA 0: LOGIN E AUTENTICAÇÃO DE USUÁRIO
    # =====================================================================
    def construir_tela_login():
        # Campos de entrada de dados para credenciais
        input_usuario = ft.TextField(label="Usuário", border_radius=10, prefix_icon=ft.Icons.PERSON)
        input_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, border_radius=10, prefix_icon=ft.Icons.LOCK)
        txt_erro = ft.Text("", color=ft.Colors.RED_400, size=13)

        # Validação do login de acordo com o perfil
        def auteticar(e):
            usr = (input_usuario.value or "").strip().lower()
            pwd = (input_senha.value or "").strip()

            if usr == "jogador" and pwd == "jogador1":
                sessao_usuario["tipo"] = "jogador"
                txt_erro.value = ""
                navegar("/home") # Redireciona jogador para a tela de busca de quadras
            elif usr == "gestor" and pwd == "gestor1":
                sessao_usuario["tipo"] = "gestor"
                txt_erro.value = ""
                navegar("/gestor") # Redireciona gestor para o painel administrativo
            else:
                txt_erro.value = "Login incorreto! Tente novamente."
                page.update()

        # Cartão centralizado contendo o formulário de login
        card_login = ft.Container(
            padding=25, 
            bgcolor=ft.Colors.GREY_900, 
            border_radius=15,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            content=ft.Column([
                ft.Icon(ft.Icons.SPORTS_SOCCER, size=50, color=ft.Colors.ORANGE_500),
                ft.Text("Quadra Search", size=26, weight="bold"),
                ft.Text("Entre com suas credenciais de acesso", color=ft.Colors.GREY_400, size=13),
                ft.Container(height=10),
                input_usuario,
                input_senha,
                txt_erro,
                ft.Container(
                    content=ft.Text("Entrar no Sistema", color=ft.Colors.WHITE, weight="bold"),
                    bgcolor=ft.Colors.ORANGE_700, 
                    padding=15, 
                    border_radius=10, 
                    alignment=ft.Alignment(0, 0),
                    on_click=auteticar
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
        )

        return ft.View(
            [
                ft.Container(
                    content=card_login,
                    alignment=ft.Alignment(0, 0),
                    expand=True
                )
            ],
            route="/",
            padding=20
        )

    # =====================================================================
    # TELA 1: HOME (Listagem, Pesquisa e Filtros de Quadras)
    # =====================================================================
    def construir_tela_home():
        # Column onde os cartões das quadras serão desenhados
        coluna_cartoes = ft.Column(spacing=20)

        # Função para reconstruir a lista de quadras na tela
        def atualizar_lista():
            coluna_cartoes.controls.clear()
            
            # Caso o banco de dados esteja vazio, exibe uma mensagem informativa sobre a falta de quadras cadastradas
            if not bd_quadras:
                coluna_cartoes.controls.append(
                    ft.Container(
                        padding=30,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column([
                            ft.Icon(ft.Icons.SEARCH_OFF, size=50, color=ft.Colors.GREY_600),
                            ft.Text("Nenhuma quadra cadastrada no momento.", color=ft.Colors.GREY_400, size=16),
                            ft.Text("Aguarde um Gestor adicionar novos espaços.", color=ft.Colors.GREY_600, size=12) if sessao_usuario["tipo"] == "jogador" else ft.Container()
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
                    )
                )
                page.update()
                return

            quadras_encontradas = 0
            for quadra in bd_quadras:
                # REQUISITO (R4): Lógica do filtro de categoria
                if estado_busca["filtro_ativo"] and estado_busca["filtro_ativo"] not in quadra["categorias"]:
                    continue
                # REQUISITO (R4): Lógica do filtro por nome (busca em tempo real)
                if estado_busca["texto"] != "" and estado_busca["texto"] not in quadra["nome"].lower():
                    continue
                
                quadras_encontradas += 1
                imagem_fake = ft.Container(
                    width=100, 
                    height=100, 
                    bgcolor=ft.Colors.GREY_800, 
                    border_radius=10,
                    content=ft.Icon(ft.Icons.CLOSE, color=ft.Colors.GREY_600, size=50),
                    alignment=ft.Alignment(0, 0)
                )

                lista_estrelas = [ft.Icon(ft.Icons.STAR, color=ft.Colors.AMBER_400, size=20) for _ in range(quadra["estrelas"])]
                
                dados_direita = ft.Column([
                    ft.Text(quadra["nome"], size=18, weight="bold"),
                    ft.Text(f"R$ {quadra['preco_hora']}/h", color=ft.Colors.ORANGE_400, weight="bold"),
                    ft.Row(lista_estrelas, spacing=2)
                ], spacing=5, expand=True)

                elementos_cartao = [imagem_fake, dados_direita]

                # REQUISITO (R6): O ícone de excluir (lixeira) só aparece se o usuário logado for GESTOR
                if sessao_usuario["tipo"] == "gestor":
                    btn_deletar = ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.RED_400,
                        tooltip="Excluir Quadra",
                        on_click=lambda e, q_id=quadra["id"]: excluir_quadra(e, q_id)
                    )
                    elementos_cartao.append(btn_deletar)

                cartao = ft.Container(
                    padding=15, 
                    bgcolor=ft.Colors.GREY_900, 
                    border_radius=10,
                    content=ft.Row(elementos_cartao, spacing=15),
                    # Clique no cartão resumo redireciona para a tela de detalhes da quadra
                    on_click=lambda e, q_id=quadra["id"]: navegar(f"/quadra/{q_id}")
                )
                
                coluna_cartoes.controls.append(cartao)

            if quadras_encontradas == 0 and bd_quadras:
                coluna_cartoes.controls.append(
                    ft.Text("Nenhuma quadra encontrada para os filtros selecionados.", color=ft.Colors.GREY_400)
                )

            page.update()

        # Evento disparado quando o usuário digita na barra de pesquisa (busca dinâmica)
        def ao_digitar(e):
            estado_busca["texto"] = e.control.value.lower()
            atualizar_lista()

        # Evento disparado ao clicar nos botões de filtro por categoria (com alternância de cores)
        def clicar_filtro(e):
            filtro = e.control.data
            estado_busca["filtro_ativo"] = None if estado_busca["filtro_ativo"] == filtro else filtro
            for btn in filtros.controls:
                btn.bgcolor = ft.Colors.ORANGE_700 if btn.data == estado_busca["filtro_ativo"] else ft.Colors.GREY_800 
            atualizar_lista()

        campo_busca = ft.TextField(label="Buscar quadras em Lages...", prefix_icon=ft.Icons.SEARCH, border_radius=20, on_change=ao_digitar)

        filtros = ft.Row([
            ft.Container(
                content=ft.Text(nome, color=ft.Colors.WHITE, weight="bold"), 
                data=nome, 
                bgcolor=ft.Colors.GREY_800, 
                padding=10, 
                border_radius=20, 
                on_click=clicar_filtro
            )
            for nome in ["Sintético", "Salão", "Areia", "Espaço Gourmet"]
        ], scroll=ft.ScrollMode.AUTO)

        atualizar_lista()
        
        return ft.View(
            [
                ft.AppBar(
                    title=ft.Text("Buscar Quadras"),
                    bgcolor=ft.Colors.TRANSPARENT,
                    actions=[ft.IconButton(ft.Icons.LOGOUT, tooltip="Sair", on_click=fazer_logout)]
                ),
                campo_busca, filtros, coluna_cartoes
            ],
            route="/home",
            padding=20, spacing=20
        )

    # =====================================================================
    # TELA 2: DETALHES DA QUADRA E HORÁRIOS
    # =====================================================================
    def construir_tela_detalhes(quadra_id):
        # Busca a quadra específica pelo ID passado na rota
        quadra = next((q for q in bd_quadras if q["id"] == quadra_id), None)
        if not quadra:
            return ft.View([ft.Text("Quadra não encontrada")], route="/home")
            
        selecao = {"dia": None, "hora": None}
        # Converte o endereço para formato de URL e cria o link para o Google Maps
        url_maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(quadra['endereco'])}"

        imagem_topo = ft.Container(
            height=200, 
            bgcolor=ft.Colors.GREY_800, 
            border_radius=10,
            content=ft.Icon(ft.Icons.CLOSE, color=ft.Colors.GREY_600, size=80),
            alignment=ft.Alignment(0, 0)
        )

        # Botão clicável de endereço que abre o navegador no Google Maps
        botao_endereco = ft.TextButton(
            content=ft.Row([
                ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.ORANGE_400, size=18),
                ft.Text(quadra["endereco"], color=ft.Colors.ORANGE_400)
            ]),
            url=url_maps
        )

        infos_textuais = ft.Column([
            ft.Text(quadra["nome"], size=30, weight="bold"),
            botao_endereco,
            ft.Text(quadra["descricao"], color=ft.Colors.GREY_400),
            ft.Row([
                *[ft.Icon(ft.Icons.STAR, color=ft.Colors.AMBER_400, size=20) for _ in range(quadra["estrelas"])],
                ft.Text(f"({quadra['nota']})", color=ft.Colors.GREY_400)
            ])
        ], spacing=10)

        grade_interface = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=15)

        # Monta os blocos com a matriz de horários disponíveis/ocupados
        def redesenhar_horarios():
            grade_interface.controls.clear()
            for dia in quadra["grade_horarios"]:
                coluna_dia = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                coluna_dia.controls.append(ft.Column([
                    ft.Text(dia["dia"], weight="bold"),
                    ft.Text(dia["data"], color=ft.Colors.GREY_400, size=12)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0))
                
                for slot in dia["slots"]:
                    esta_selecionado = (selecao["dia"] == dia["data"] and selecao["hora"] == slot["hora"])
                    
                    if slot["livre"]:
                        cor_fundo = ft.Colors.ORANGE_600 if not esta_selecionado else ft.Colors.ORANGE_300
                        icone = None
                    else:
                        cor_fundo = ft.Colors.TRANSPARENT
                        icone = ft.Icons.CLOSE

                    btn = ft.Container(
                        content=ft.Row([
                            ft.Icon(icone, size=14, color=ft.Colors.GREY_600) if icone else ft.Container(),
                            ft.Text(slot["hora"], weight="bold", color=ft.Colors.WHITE if slot["livre"] else ft.Colors.GREY_600)
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        bgcolor=cor_fundo,
                        border=ft.Border.all(1, ft.Colors.GREY_800) if not slot["livre"] else None,
                        border_radius=10, 
                        padding=10, 
                        width=90,
                        # Permite clicar e selecionar o horário somente se o slot estiver livre
                        on_click=lambda e, 
                        d=dia["data"], 
                        h=slot["hora"], 
                        livre=slot["livre"]: selecionar_horario(d, h) if livre else None
                    )
                    coluna_dia.controls.append(btn)
                    
                grade_interface.controls.append(
                    ft.Container(
                        content=coluna_dia, 
                        border=ft.Border.all(1, ft.Colors.GREY_800), 
                        border_radius=10, 
                        padding=15
                    )
                )
            page.update()

        def selecionar_horario(data, hora):
            selecao["dia"] = data
            selecao["hora"] = hora
            redesenhar_horarios()

        bloco_disponibilidade = ft.Container(
            bgcolor=ft.Colors.GREY_900, 
            padding=20, 
            border_radius=15,
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.ORANGE_400), ft.Text("Verificar disponibilidade", weight="bold", size=18)]),
                grade_interface
            ], spacing=20)
        )

        redesenhar_horarios()

        return ft.View(
            [
                ft.AppBar(title=ft.Text("Detalhes da Quadra"), bgcolor=ft.Colors.TRANSPARENT),
                imagem_topo,
                infos_textuais,
                bloco_disponibilidade,
                ft.Container(
                    content=ft.Row([ft.Text("Selecionar Horário", size=16, color=ft.Colors.WHITE, weight="bold"), ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=ft.Colors.ORANGE_600, 
                    padding=15, 
                    border_radius=10,
                    on_click=lambda e: print("Horário Selecionado!")
                )
            ],
            route=f"/quadra/{quadra_id}",
            scroll=ft.ScrollMode.AUTO, padding=20, spacing=25
        )

    # =====================================================================
    # TELA 3: CADASTRO DE NOVA QUADRA (R2 / R3)
    # =====================================================================
    def construir_tela_cadastro():
        # REQUISITO (R2): Campos de entrada para cadastrar uma quadra
        input_nome = ft.TextField(label="Nome da Quadra", border_radius=10)
        input_preco = ft.TextField(label="Preço por Hora (R$)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10)
        input_categorias = ft.TextField(label="Categorias (Ex: Sintético, Areia)", border_radius=10)
        input_endereco = ft.TextField(label="Endereço Completo", border_radius=10)
        input_descricao = ft.TextField(label="Descrição", multiline=True, min_lines=2, border_radius=10)

        # REQUISITO (R3): Função de ação atrelada ao evento onClick para inserir no banco de dados
        def salvar_nova_quadra(e):
            if not input_nome.value or not input_preco.value:
                page.snack_bar = ft.SnackBar(ft.Text("Preencha Nome e Preço!"))
                page.snack_bar.open = True
                page.update()
                return

            # Gera um ID sequencial dinâmico
            novo_id = max([q["id"] for q in bd_quadras], default=-1) + 1
            cats = [c.strip() for c in (input_categorias.value or "Outros").split(",")]

            # Monta o dicionário com as informações inseridas no formulário
            nova_quadra = {
                "id": novo_id,
                "nome": input_nome.value,
                "preco_hora": float(input_preco.value or 0),
                "estrelas": 0,      # Quadra nova começa com nota zerada
                "nota": "0,0",
                "categorias": cats,
                "endereco": input_endereco.value or "Lages/SC",
                "descricao": input_descricao.value or "Nova quadra cadastrada no sistema.",
                "grade_horarios":[
                    {"dia": "Seg", "data": "26/05", "slots": [{"hora": "18:00", "livre": True}, {"hora": "19:00", "livre": False}, {"hora": "20:00", "livre": True}]},
                    {"dia": "Ter", "data": "27/05", "slots": [{"hora": "18:00", "livre": True}, {"hora": "19:00", "livre": True}, {"hora": "20:00", "livre": False}]},
                    {"dia": "Qua", "data": "28/05", "slots": [{"hora": "18:00", "livre": True}, {"hora": "19:00", "livre": False}, {"hora": "20:00", "livre": True}]},
                    {"dia": "Qui", "data": "29/05", "slots": [{"hora": "18:00", "livre": False}, {"hora": "19:00", "livre": False}, {"hora": "20:00", "livre": False}]},
                    {"dia": "Sex", "data": "30/05", "slots": [{"hora": "18:00", "livre": True}, {"hora": "19:00", "livre": True}, {"hora": "20:00", "livre": True}]}
                ]

            }

            # Insere no banco em memória e retorna ao painel do gestor
            bd_quadras.append(nova_quadra)
            navegar("/gestor")

        return ft.View(
            [
                ft.AppBar(title=ft.Text("Cadastrar Nova Quadra"), bgcolor=ft.Colors.TRANSPARENT),
                ft.Text("Formulário de Cadastro", size=22, weight="bold"),
                input_nome, input_preco, input_categorias, input_endereco, input_descricao,
                ft.Container(
                    content=ft.Text("Salvar e Publicar Quadra", color=ft.Colors.WHITE, weight="bold"),
                    bgcolor=ft.Colors.GREEN_600, 
                    padding=15, 
                    border_radius=10, 
                    alignment=ft.Alignment(0, 0),
                    on_click=salvar_nova_quadra
                )
            ],
            route="/cadastrar",
            scroll=ft.ScrollMode.AUTO, padding=20, spacing=15
        )

    # =====================================================================
    # TELA 4: PAINEL ADMINISTRATIVO DO GESTOR
    # =====================================================================
    def construir_tela_gestor():
        header_gestor = ft.Container(
            padding=15, 
            bgcolor=ft.Colors.GREY_900, 
            border_radius=15,
            content=ft.Row([
                ft.Container(
                    padding=10, 
                    bgcolor=ft.Colors.GREY_800, 
                    border_radius=10,
                    content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=ft.Colors.GREEN_400, size=30)
                ),
                ft.Column([
                    ft.Text("Painel do Gestor", size=22, weight="bold"),
                    ft.Text("Gerenciamento de reservas e estrutura", size=12, color=ft.Colors.GREY_400)
                ], spacing=0)
            ], spacing=15)
        )

        botoes_gestao = ft.Row([
            ft.Container(
                expand=True, 
                padding=15, 
                bgcolor=ft.Colors.ORANGE_700, 
                border_radius=10,
                content=ft.Row([ft.Icon(ft.Icons.ADD_BUSINESS, color=ft.Colors.WHITE), ft.Text("Cadastrar Quadra", color=ft.Colors.WHITE, weight="bold")]),
                on_click=lambda e: navegar("/cadastrar")
            ),
            ft.Container(
                expand=True, 
                padding=15, 
                bgcolor=ft.Colors.GREY_800, 
                border_radius=10,
                content=ft.Row([ft.Icon(ft.Icons.LIST_ALT, color=ft.Colors.WHITE), ft.Text("Ver / Excluir Quadras", color=ft.Colors.WHITE, weight="bold")]),
                on_click=lambda e: navegar("/home")
            )
        ], spacing=15)

        # Dados simulados para o painel diário de agendamentos
        horarios_hoje = [
            {"hora": "18:00", "status": "Livre", "cor": ft.Colors.GREEN_700},
            {"hora": "19:00", "status": "Daniel Cruz - Fixo", "cor": ft.Colors.BLUE_700},
            {"hora": "20:00", "status": "Pendente", "cor": ft.Colors.AMBER_700}
        ]

        lista_slots = ft.Column(spacing=10)
        for item in horarios_hoje:
            lista_slots.controls.append(
                ft.Container(
                    padding=12, 
                    bgcolor=ft.Colors.GREY_900, 
                    border_radius=10,
                    border=ft.Border.all(1, ft.Colors.GREY_800),
                    content=ft.Row([
                        ft.Row([ft.Icon(ft.Icons.SCHEDULE, size=18, color=ft.Colors.GREY_400), ft.Text(item["hora"], weight="bold", size=16)]),
                        ft.Container(content=ft.Text(item["status"], color=ft.Colors.WHITE, size=12, weight="bold"), bgcolor=item["cor"], padding=8, border_radius=15)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            )

        card_horarios = ft.Container(
            padding=20, 
            bgcolor=ft.Colors.GREY_900, 
            border_radius=15,
            border=ft.Border.all(1, ft.Colors.GREY_800),
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH, color=ft.Colors.GREEN_400), ft.Text("Horários do Dia", size=18, weight="bold")]),
                lista_slots
            ], spacing=15)
        )

        botoes_acao = ft.Row([
            ft.Container(
                expand=True, padding=15, bgcolor=ft.Colors.RED_900, border_radius=12,
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCK, color=ft.Colors.WHITE),
                    ft.Text("Bloquear Horário", weight="bold", color=ft.Colors.WHITE, size=13)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                on_click=lambda e: None
            ),
            ft.Container(
                expand=True, padding=15, bgcolor=ft.Colors.GREEN_700, border_radius=12,
                content=ft.Column([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.WHITE),
                    ft.Text("Aprovar Reservas", weight="bold", color=ft.Colors.WHITE, size=13)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                on_click=lambda e: None
            )
        ], spacing=15)

        return ft.View(
            [
                ft.AppBar(
                    title=ft.Text("Painel do Gestor"),
                    bgcolor=ft.Colors.TRANSPARENT,
                    actions=[ft.IconButton(ft.Icons.LOGOUT, tooltip="Sair", on_click=fazer_logout)]
                ),
                header_gestor,
                botoes_gestao,
                card_horarios,
                botoes_acao
            ],
            route="/gestor",
            scroll=ft.ScrollMode.AUTO, padding=20, spacing=20
        )

    # =====================================================================
    # MOTOR DE GERENCIAMENTO DE ROTAS E PILHA DE NAVEGAÇÃO
    # =====================================================================
    def mudar_rota(e):
        page.views.clear()
        
        # Proteção de rotas: se não houver login efetuado, força exibição da tela de Login
        if sessao_usuario["tipo"] is None:
            page.views.append(construir_tela_login())
            page.update()
            return

        # Pilha de telas para o perfil GESTOR
        if sessao_usuario["tipo"] == "gestor":
            page.views.append(construir_tela_gestor()) # Base da pilha
            if page.route == "/cadastrar":
                page.views.append(construir_tela_cadastro())
            elif page.route == "/home":
                page.views.append(construir_tela_home())
            elif page.route.startswith("/quadra/"):
                quadra_id = int(page.route.split("/")[2])
                page.views.append(construir_tela_detalhes(quadra_id))

        # Pilha de telas para o perfil JOGADOR
        elif sessao_usuario["tipo"] == "jogador":
            page.views.append(construir_tela_home()) # Base da pilha
            if page.route.startswith("/quadra/"):
                quadra_id = int(page.route.split("/")[2])
                page.views.append(construir_tela_detalhes(quadra_id))

        page.update()

    # Trata o botão "Voltar" nativo das telas empilhadas no Flet
    def voltar_tela(e):
        page.views.pop()
        rota_anterior = page.views[-1].route
        navegar(rota_anterior)

    page.on_route_change = mudar_rota
    page.on_view_pop = voltar_tela
    
    # Execução inicial partindo da rota raiz
    navegar("/")

# Inicialização da aplicação no Flet 1.0
ft.run(main)