import pygame
import random
import runner

FPS = 60

VASO_W            = 120
VASO_H            = 160
PELOTA_W          = 60

SPEED_INICIAL     = 350
SPEED_INCREMENTO  = 80
RONDAS_PARA_GANAR = 3

LEVANTAR_DIST = 90
LEVANTAR_VEL  = 280

FASE_LEVANTAR  = 'levantar'
FASE_MOSTRAR   = 'mostrar'
FASE_BAJAR     = 'bajar'
FASE_MEZCLAR   = 'mezclar'
FASE_ELEGIR    = 'elegir'
FASE_REVELAR   = 'revelar'
FASE_RESULTADO = 'resultado'


def run(screen, clock, W, H) -> bool:

    vaso_img   = runner.load_image('assets/vaso.png',   scale=(VASO_W, VASO_H))
    pelota_img = runner.load_image('assets/pelota.png', scale=(PELOTA_W, PELOTA_W))

    font_big   = pygame.font.SysFont('monospace', 36, bold=True)
    font_small = pygame.font.SysFont('monospace', 22)

    if not runner.wait_for_start(screen, clock, W, H, 'Seguí la pelota'):
        return False

    ronda     = 0
    acertadas = 0

    def nueva_ronda():
        nonlocal ronda
        ronda += 1
        y       = H // 2 - VASO_H // 2
        espacio = W // 4
        pos_x   = [
            espacio     - VASO_W // 2,
            W // 2      - VASO_W // 2,
            W - espacio - VASO_W // 2,
        ]
        vasos = [{'x':        float(pos_x[i]),
                  'y':        float(y),
                  'target_x': float(pos_x[i]),
                  'offset_y': 0.0,
                  'tiene_pelota': False}
                 for i in range(3)]
        # Marcar cuál tiene la pelota por referencia directa al objeto
        idx = random.randint(0, 2)
        vasos[idx]['tiene_pelota'] = True
        return vasos, vasos[idx]   # retornamos lista y referencia al vaso con pelota

    vasos, vaso_pelota = nueva_ronda()
    speed              = SPEED_INICIAL
    fase               = FASE_LEVANTAR
    fase_timer         = 0.0
    movimientos        = []
    vaso_elegido       = None
    resultado_correcto = None

    def generar_movimientos(n):
        pares = [(0, 1), (1, 2), (0, 2)]
        return [random.choice(pares) for _ in range(n)]

    def pelota_screen_pos():
        """
        Lee directamente del objeto vaso que tiene la pelota.
        Como es una referencia al dict, siempre tiene la x y offset_y actuales.
        """
        px = vaso_pelota['x'] + VASO_W // 2 - PELOTA_W // 2
        py = vaso_pelota['y'] + VASO_H - PELOTA_W - 4
        return px, py

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and fase == FASE_ELEGIR:
                mx, my = event.pos
                for v in vasos:
                    if pygame.Rect(v['x'], v['y'], VASO_W, VASO_H).collidepoint(mx, my):
                        vaso_elegido       = v
                        resultado_correcto = v['tiene_pelota']
                        fase               = FASE_REVELAR
                        break

        # ── Update ────────────────────────────────────────────────

        if fase == FASE_LEVANTAR:
            vaso_pelota['offset_y'] -= LEVANTAR_VEL * dt
            if vaso_pelota['offset_y'] <= -LEVANTAR_DIST:
                vaso_pelota['offset_y'] = -LEVANTAR_DIST
                fase                    = FASE_MOSTRAR
                fase_timer              = 1.4

        elif fase == FASE_MOSTRAR:
            fase_timer -= dt
            if fase_timer <= 0:
                fase = FASE_BAJAR

        elif fase == FASE_BAJAR:
            vaso_pelota['offset_y'] += LEVANTAR_VEL * dt
            if vaso_pelota['offset_y'] >= 0:
                vaso_pelota['offset_y'] = 0.0
                n_mov                   = 4 + ronda * 2
                movimientos             = generar_movimientos(n_mov)
                fase                    = FASE_MEZCLAR

        elif fase == FASE_MEZCLAR:
            todos_llegaron = True
            for v in vasos:
                diff = v['target_x'] - v['x']
                if abs(diff) > 2:
                    todos_llegaron = False
                    paso = speed * dt
                    v['x'] += paso if diff > 0 else -paso
                    if abs(v['target_x'] - v['x']) < paso:
                        v['x'] = v['target_x']

            if todos_llegaron:
                if movimientos:
                    i, j = movimientos.pop(0)
                    # Intercambiar target_x entre los dos vasos por índice de lista
                    vasos[i]['target_x'], vasos[j]['target_x'] = \
                        vasos[j]['target_x'], vasos[i]['target_x']
                    # NO hay que actualizar vaso_pelota — sigue siendo
                    # la misma referencia al mismo dict, que se mueve solo
                else:
                    fase = FASE_ELEGIR

        elif fase == FASE_REVELAR:
            todos_arriba = True
            for v in vasos:
                v['offset_y'] -= LEVANTAR_VEL * dt
                if v['offset_y'] > -LEVANTAR_DIST:
                    todos_arriba = False
                else:
                    v['offset_y'] = -LEVANTAR_DIST
            if todos_arriba:
                fase       = FASE_RESULTADO
                fase_timer = 1.5

        elif fase == FASE_RESULTADO:
            fase_timer -= dt
            if fase_timer <= 0:
                if resultado_correcto:
                    acertadas += 1
                    if acertadas >= RONDAS_PARA_GANAR:
                        runner.play_result(screen, clock, W, H, gano=True)
                        return True
                else:
                    runner.play_result(screen, clock, W, H, gano=False)
                    return False

                for v in vasos:
                    v['offset_y'] = 0.0
                speed               += SPEED_INCREMENTO
                vasos, vaso_pelota   = nueva_ronda()
                vaso_elegido         = None
                resultado_correcto   = None
                fase                 = FASE_LEVANTAR

        # ── Draw ──────────────────────────────────────────────────
        runner.clear(screen)

        # Pelota visible cuando el vaso que la tiene está levantado
        if fase in (FASE_LEVANTAR, FASE_MOSTRAR, FASE_BAJAR,
                    FASE_REVELAR, FASE_RESULTADO):
            px, py = pelota_screen_pos()
            screen.blit(pelota_img, (int(px), int(py)))

        for v in vasos:
            draw_y = int(v['y'] + v['offset_y'])
            screen.blit(vaso_img, (int(v['x']), draw_y))

            # Resaltar vaso elegido en resultado
            if fase == FASE_RESULTADO and v is vaso_elegido:
                color = (80, 220, 80) if resultado_correcto else (220, 80, 80)
                pygame.draw.rect(
                    screen, color,
                    pygame.Rect(int(v['x']), draw_y, VASO_W, VASO_H),
                    3, border_radius=6
                )

            # Resaltar vaso con pelota en resultado (para que el jugador vea dónde era)
            if fase == FASE_RESULTADO and v['tiene_pelota'] and not resultado_correcto:
                pygame.draw.rect(
                    screen, (80, 220, 80),
                    pygame.Rect(int(v['x']), draw_y, VASO_W, VASO_H),
                    3, border_radius=6
                )

        hud = font_small.render(
            f'Ronda {ronda}  ·  Acertadas: {acertadas}/{RONDAS_PARA_GANAR}',
            True, (230, 230, 230)
        )
        screen.blit(hud, (20, 20))

        if fase == FASE_ELEGIR:
            hint = font_big.render('¿Dónde está la pelota?', True, (255, 255, 255))
            screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 80))

        if fase in (FASE_MOSTRAR, FASE_LEVANTAR):
            hint = font_small.render('Memorizá la posición...', True, (200, 200, 200))
            screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 55))

        runner.flip()

    return False