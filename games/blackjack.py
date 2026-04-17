import pygame
import random
import runner

FPS = 60

# 120% de 80x120 = 176x264 — sin smoothscale para evitar blur
CARTA_W   = 176
CARTA_H   = 264
CARTA_GAP = 18

PALOS   = ['p', 'c', 'd', 't']
VALORES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


def valor_mano(mano):
    total = 0
    ases  = 0
    for carta in mano:
        v = carta[0]
        if v in ('J', 'Q', 'K'):
            total += 10
        elif v == 'A':
            total += 11
            ases  += 1
        else:
            total += int(v)
    while total > 21 and ases:
        total -= 10
        ases  -= 1
    return total


def cargar_cartas():
    """
    Carga cada PNG en su resolución nativa y lo escala UNA sola vez
    con transform.scale (sin interpolación) para máxima nitidez.
    """
    cartas = {}
    for p in PALOS:
        for v in VALORES:
            key  = f'{v}_{p}'
            path = f'assets/cartas/{key}.png'
            try:
                raw = pygame.image.load(path)
                # convert() sin alpha primero para evitar doble conversión
                raw = raw.convert_alpha()
                # scale sin smooth = sin blur
                cartas[key] = pygame.transform.scale(raw, (CARTA_W, CARTA_H))
            except FileNotFoundError:
                cartas[key] = _fallback_carta(v, p)
    return cartas


def _fallback_carta(v, p):
    """Genera una carta vectorial cuando falta el PNG."""
    surf = pygame.Surface((CARTA_W, CARTA_H), pygame.SRCALPHA)
    pygame.draw.rect(surf, (245, 245, 245),
                     (0, 0, CARTA_W, CARTA_H), border_radius=10)
    pygame.draw.rect(surf, (140, 140, 140),
                     (0, 0, CARTA_W, CARTA_H), 2, border_radius=10)

    color   = (200, 40, 40) if p in ('c', 'd') else (20, 20, 20)
    simbolo = {'p': '♠', 'c': '♥', 'd': '♦', 't': '♣'}[p]

    font_val = pygame.font.SysFont('monospace', 28, bold=True)
    font_sym = pygame.font.SysFont('monospace', 54, bold=True)

    # Valor arriba izquierda
    txt = font_val.render(v, True, color)
    surf.blit(txt, (9, 9))

    # Símbolo del palo bajo el valor
    stxt = font_val.render(simbolo, True, color)
    surf.blit(stxt, (9, 9 + txt.get_height()))

    # Símbolo grande centrado
    sym = font_sym.render(simbolo, True, color)
    surf.blit(sym, (CARTA_W // 2 - sym.get_width()  // 2,
                    CARTA_H // 2 - sym.get_height() // 2))

    # Valor abajo derecha (rotado 180°)
    txt2  = font_val.render(v, True, color)
    stxt2 = font_val.render(simbolo, True, color)
    txt2r  = pygame.transform.rotate(txt2,  180)
    stxt2r = pygame.transform.rotate(stxt2, 180)
    surf.blit(stxt2r, (CARTA_W - stxt2r.get_width() - 9, CARTA_H - stxt2r.get_height() - 9))
    surf.blit(txt2r,  (CARTA_W - txt2r.get_width()  - 9,
                       CARTA_H - stxt2r.get_height() - txt2r.get_height() - 9))

    return surf


def run(screen, clock, W, H) -> bool:

    cartas_img = cargar_cartas()

    try:
        raw   = pygame.image.load('assets/cartas/dorso.png').convert_alpha()
        dorso = pygame.transform.scale(raw, (CARTA_W, CARTA_H))
    except FileNotFoundError:
        dorso = pygame.Surface((CARTA_W, CARTA_H), pygame.SRCALPHA)
        pygame.draw.rect(dorso, (30, 80, 180),
                         (0, 0, CARTA_W, CARTA_H), border_radius=10)
        pygame.draw.rect(dorso, (20, 50, 130),
                         (0, 0, CARTA_W, CARTA_H), 2, border_radius=10)

    font_big   = pygame.font.SysFont('monospace', 36, bold=True)
    font_med   = pygame.font.SysFont('monospace', 28)
    font_small = pygame.font.SysFont('monospace', 20)
    font_btn   = pygame.font.SysFont('monospace', 24)

    if not runner.wait_for_start(screen, clock, W, H, 'Blackjack'):
        return False

    def draw_mano(mano, x_start, y, ocultar_primera=False):
        for i, carta in enumerate(mano):
            x = x_start + i * (CARTA_W + CARTA_GAP)
            if i == 0 and ocultar_primera:
                screen.blit(dorso, (x, y))
            else:
                screen.blit(cartas_img[f'{carta[0]}_{carta[1]}'], (x, y))

    def x_mano(n):
        ancho = n * CARTA_W + (n - 1) * CARTA_GAP
        return W // 2 - ancho // 2

    def nueva_partida():
        mazo = [(v, p) for p in PALOS for v in VALORES]
        random.shuffle(mazo)
        return mazo, [mazo.pop(), mazo.pop()], [mazo.pop(), mazo.pop()]

    mazo, mano_jugador, mano_dealer = nueva_partida()

    fase         = 'jugando'
    dealer_timer = 0.0
    mensaje_fin  = ''
    gano_partida = False

    btn_pedir     = pygame.Rect(W // 2 - 185, H - 72, 170, 50)
    btn_plantarse = pygame.Rect(W // 2 + 15,  H - 72, 170, 50)

    while True:
        dt = clock.tick(FPS) / 1000.0
        mx, my = pygame.mouse.get_pos()

        hover_pedir     = btn_pedir.collidepoint(mx, my)    and fase == 'jugando'
        hover_plantarse = btn_plantarse.collidepoint(mx, my) and fase == 'jugando'

        # ── Eventos ───────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and fase == 'jugando':
                if hover_pedir:
                    mano_jugador.append(mazo.pop())
                    pj = valor_mano(mano_jugador)
                    if pj >= 21:
                        # 21 exacto o pasado — pasar turno al dealer
                        fase         = 'dealer'
                        dealer_timer = 0.6
                elif hover_plantarse:
                    fase         = 'dealer'
                    dealer_timer = 0.6

            if fase == 'fin' and event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False
                runner.play_result(screen, clock, W, H, gano=gano_partida)
                return gano_partida

        # ── Update ────────────────────────────────────────────────

        # Recalcular puntaje del jugador en cada frame (no solo al pedir)
        pj = valor_mano(mano_jugador)

        # Si se pasó de 21 mientras era turno del jugador, terminar
        if fase == 'jugando' and pj > 21:
            mensaje_fin  = '¡Te pasaste!'
            gano_partida = False
            fase         = 'fin'

        if fase == 'dealer':
            dealer_timer -= dt
            if dealer_timer <= 0:
                pd = valor_mano(mano_dealer)
                if pd < 17:
                    mano_dealer.append(mazo.pop())
                    dealer_timer = 0.8
                else:
                    pd = valor_mano(mano_dealer)
                    pj = valor_mano(mano_jugador)
                    if pd > 21:
                        mensaje_fin, gano_partida = '¡El dealer se pasó! Ganaste', True
                    elif pj > pd:
                        mensaje_fin, gano_partida = '¡Ganaste!', True
                    elif pj == pd:
                        mensaje_fin, gano_partida = 'Empate — perdiste', False
                    else:
                        mensaje_fin, gano_partida = 'Ganó el dealer', False
                    fase = 'fin'

        # ── Draw ──────────────────────────────────────────────────
        runner.clear(screen)

        y_dealer  = H // 4 - CARTA_H // 2
        y_jugador = H * 3 // 4 - CARTA_H // 2

        lbl_d = font_small.render('Dealer', True, (200, 200, 200))
        screen.blit(lbl_d, (W // 2 - lbl_d.get_width() // 2, y_dealer - 28))

        lbl_j = font_small.render('Vos', True, (200, 200, 200))
        screen.blit(lbl_j, (W // 2 - lbl_j.get_width() // 2, y_jugador - 28))

        ocultar = fase == 'jugando'
        draw_mano(mano_dealer,  x_mano(len(mano_dealer)),  y_dealer,  ocultar)
        draw_mano(mano_jugador, x_mano(len(mano_jugador)), y_jugador)

        # Puntaje jugador — siempre visible y siempre actualizado
        pj_surf = font_med.render(
            str(pj), True, (255, 220, 80) if pj <= 21 else (220, 80, 80)
        )
        screen.blit(pj_surf, (W // 2 - pj_surf.get_width() // 2,
                               y_jugador + CARTA_H + 10))

        # Puntaje dealer — solo visible cuando no es turno del jugador
        if not ocultar:
            pd = valor_mano(mano_dealer)
            pd_surf = font_med.render(
                str(pd), True, (255, 220, 80) if pd <= 21 else (220, 80, 80)
            )
            screen.blit(pd_surf, (W // 2 - pd_surf.get_width() // 2,
                                   y_dealer + CARTA_H + 10))

        if fase == 'jugando':
            runner.draw_button(screen, font_btn, 'Pedir',     btn_pedir,     hover_pedir)
            runner.draw_button(screen, font_btn, 'Plantarse', btn_plantarse, hover_plantarse)

        if fase == 'fin':
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))

            msg = font_big.render(mensaje_fin, True,
                                   (80, 220, 100) if gano_partida else (220, 80, 80))
            screen.blit(msg, (W // 2 - msg.get_width() // 2, H // 2 - 50))

            hint = font_small.render('click o tecla para continuar', True, (200, 200, 200))
            screen.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 16))

        runner.flip()

    return False