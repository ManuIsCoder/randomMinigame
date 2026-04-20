import pygame
import sys
import random
import math
import runner

FPS = 60

DIFICULTADES_DE_TIEMPO = [60.0, 55.0, 50.0, 40.0, 30.0, 20.0]


# ── Generador de problemas ─────────────────────────────────────────────────────

def crear_problema(dificultad):
    """
    Genera una ecuación y su respuesta según la dificultad (1–6).
    Reglas:
      - La respuesta no puede ser periódica.
      - Máximo 3 decimales.
      - Dificultad 6: respuesta puede llegar a 1000 y ser tan pequeña como 0.125
    Retorna (texto_ecuacion, respuesta_float).
    """
    def fraccion_limpia(num, den):
        """Verifica que num/den no sea periódica y tenga máx 3 decimales."""
        if den == 0:
            return False
        r = num / den
        # Verificar que al redondear a 3 decimales sea exacto
        return abs(round(r, 3) - r) < 1e-9

    def entero(lo, hi):
        return random.randint(lo, hi)

    ops_por_dif = {
        1: [('+', 1, 20,  1, 20),
            ('-', 5, 30,  1, 10)],
        2: [('+', 1, 50,  1, 50),
            ('-', 10, 60, 1, 30),
            ('*', 2, 9,   2, 9)],
        3: [('+', 10, 100, 10, 100),
            ('-', 20, 100, 10,  80),
            ('*', 2,  12,  2,  12),
            ('/', 'simple')],
        4: [('+', 50, 300, 50, 300),
            ('-', 50, 300, 10, 200),
            ('*', 10,  30,  2,  20),
            ('/', 'media'),
            ('**', 2, 15, 2, 3)],
        5: [('+', 100, 600, 100, 600),
            ('-', 200, 800, 100, 500),
            ('*',  20,  80,  10,  50),
            ('/', 'dificil'),
            ('**', 5, 30, 2, 4)],
        6: [('+', 500, 999, 500, 999),
            ('-', 500, 999, 100, 800),
            ('*',  50, 200,  10, 100),
            ('/', 'extremo'),
            ('**', 10, 60, 2, 4)],
    }

    intentos = 0
    while intentos < 200:
        intentos += 1
        op_def = random.choice(ops_por_dif[dificultad])
        op = op_def[0]

        if op == '+':
            a = entero(op_def[1], op_def[2])
            b = entero(op_def[3], op_def[4])
            res = a + b
            texto = f'{a} + {b}'

        elif op == '-':
            a = entero(op_def[1], op_def[2])
            b = entero(op_def[3], op_def[4])
            if b > a:
                a, b = b, a
            res = a - b
            texto = f'{a} - {b}'

        elif op == '*':
            a = entero(op_def[1], op_def[2])
            b = entero(op_def[3], op_def[4])
            res = a * b
            texto = f'{a} x {b}'

        elif op == '/':
            modo = op_def[1]
            # Generamos divisiones exactas o con hasta 3 decimales no periódicos
            # usando denominadores que solo tienen factores 2 y 5
            denominadores_validos = [1, 2, 4, 5, 8, 10, 20, 25, 40, 50, 100, 125, 200]
            if modo == 'simple':
                den = random.choice([1, 2, 4, 5])
                num = entero(2, 20) * den
            elif modo == 'media':
                den = random.choice([2, 4, 5, 10, 20])
                num = entero(2, 40) * den + random.choice([0, den // 2])
            elif modo == 'dificil':
                den = random.choice([4, 5, 8, 10, 20, 25])
                num = entero(5, 80) * den + random.randint(0, den - 1)
            else:  # extremo
                den = random.choice(denominadores_validos)
                num = entero(10, 200) * den + random.randint(0, den - 1)

            if den == 0 or not fraccion_limpia(num, den):
                continue

            res    = round(num / den, 3)
            res_int = int(res)
            # Formatear: entero si no tiene decimales
            if res == res_int:
                texto = f'{num} ÷ {den}'
            else:
                texto = f'{num} ÷ {den}'

        elif op == '**':
            a = entero(op_def[1], op_def[2])
            b = entero(op_def[3], op_def[4])
            res = a ** b
            if res > 1000:
                continue
            texto = f'{a} ^ {b}'

        else:
            continue

        # Validación final
        res = float(res)
        if abs(round(res, 3) - res) > 1e-9:
            continue   # periódica
        if res > 1000 or res < -1000:
            continue
        if dificultad == 6 and res != 0 and abs(res) < 0.125:
            continue

        return texto, round(res, 3)

    # Fallback seguro
    a = entero(1, 20)
    b = entero(1, 20)
    return f'{a} + {b}', float(a + b)


# ── Juego principal ────────────────────────────────────────────────────────────

def run(screen, clock, W, H) -> bool:

    # ── Pantalla de inicio ────────────────────────────────────────────────────
    if not runner.wait_for_start(screen, clock, W, H, 'Cálculo mental'):
        return False

    # ── Ruleta de dificultad ──────────────────────────────────────────────────
    dificultad = runner.spin_ruleta(screen, clock, W, H)
    tiempo_limite = DIFICULTADES_DE_TIEMPO[dificultad - 1]

    # ── Fuentes ───────────────────────────────────────────────────────────────
    font_timer    = pygame.font.SysFont('monospace', 48, bold=True)
    font_ecuacion = pygame.font.SysFont('monospace', 56, bold=True)
    font_input    = pygame.font.SysFont('monospace', 36)
    font_hint     = pygame.font.SysFont('monospace', 20)

    # ── Estado ────────────────────────────────────────────────────────────────
    ecuacion, respuesta_correcta = crear_problema(dificultad)
    tiempo_restante = tiempo_limite

    texto_input   = ''      # lo que escribe el jugador
    input_activo  = False   # si el campo tiene foco
    mensaje_error = ''      # "Incorrecto" mostrado brevemente
    error_timer   = 0.0

    # Rect del campo de input — centrado debajo de la ecuación
    input_rect = pygame.Rect(W // 2 - 200, H // 2 + 80, 400, 60)

    while True:
        dt = clock.tick(FPS) / 1000.0

        # ── Eventos ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

            # Click en el campo de input → activarlo
            if event.type == pygame.MOUSEBUTTONDOWN:
                input_activo = input_rect.collidepoint(event.pos)

            if event.type == pygame.KEYDOWN and input_activo:

                if event.key == pygame.K_BACKSPACE:
                    texto_input = texto_input[:-1]

                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # Validar respuesta
                    try:
                        # Aceptar coma o punto como separador decimal
                        valor = float(texto_input.replace(',', '.'))
                        if abs(valor - respuesta_correcta) < 0.001:
                            runner.play_result(screen, clock, W, H, gano=True)
                            return True
                        else:
                            mensaje_error = f'Incorrecto  (resp: NO)'
                            error_timer   = 2.5
                            texto_input   = ''
                    except ValueError:
                        mensaje_error = 'Ingresá un número válido'
                        error_timer   = 1.5
                        texto_input   = ''

                else:
                    # Solo permitir dígitos, punto, coma y signo negativo al inicio
                    car = event.unicode
                    if car in '0123456789':
                        texto_input += car
                    elif car in '.,':
                        # Solo un separador decimal
                        if '.' not in texto_input and ',' not in texto_input:
                            texto_input += car
                    elif car == '-' and texto_input == '':
                        texto_input += '-'

        # ── Update ────────────────────────────────────────────────────────────
        tiempo_restante -= dt
        if tiempo_restante <= 0:
            runner.play_result(screen, clock, W, H, gano=False)
            return False

        if error_timer > 0:
            error_timer -= dt

        # ── Draw ──────────────────────────────────────────────────────────────
        runner.clear(screen)

        # Temporizador — cambia de color al acercarse al límite
        pct = tiempo_restante / tiempo_limite
        if pct > 0.5:
            color_timer = (255, 255, 255)
        elif pct > 0.25:
            color_timer = (255, 200, 50)
        else:
            color_timer = (220, 60, 60)

        t_surf = font_timer.render(
            f'{max(0, tiempo_restante):.1f}s', True, color_timer
        )
        screen.blit(t_surf, (W // 2 - t_surf.get_width() // 2, 40))

        # Barra de tiempo debajo del número
        barra_w = int((W - 100) * max(0, pct))
        pygame.draw.rect(screen, (50, 50, 50),  (50, 110, W - 100, 10), border_radius=5)
        pygame.draw.rect(screen, color_timer,    (50, 110, barra_w,  10), border_radius=5)

        # Dificultad
        dif_nombres = {1:'Muy Fácil', 2:'Fácil', 3:'Normal',
                       4:'Difícil',   5:'Muy Difícil', 6:'EXTREMO'}
        dif_surf = font_hint.render(
            f'Dificultad {dificultad} — {dif_nombres[dificultad]}',
            True, (180, 180, 180)
        )
        screen.blit(dif_surf, (W // 2 - dif_surf.get_width() // 2, 130))

        # Ecuación centrada
        ec_surf = font_ecuacion.render(ecuacion, True, (255, 255, 255))
        screen.blit(ec_surf, (W // 2 - ec_surf.get_width() // 2,
                               H // 2 - ec_surf.get_height() // 2 - 40))

        # Campo de input
        color_borde = (100, 180, 255) if input_activo else (120, 120, 120)
        fondo_input = pygame.Surface((input_rect.w, input_rect.h), pygame.SRCALPHA)
        fondo_input.fill((255, 255, 255, 30) if input_activo else (255, 255, 255, 15))
        screen.blit(fondo_input, input_rect.topleft)
        pygame.draw.rect(screen, color_borde, input_rect, 2, border_radius=8)

        if texto_input:
            inp_surf = font_input.render(texto_input, True, (255, 255, 255))
        else:
            # Placeholder
            inp_surf = font_input.render(
                'respuesta...' if not input_activo else '',
                True, (120, 120, 120)
            )
        screen.blit(inp_surf, (
            input_rect.x + 16,
            input_rect.y + input_rect.h // 2 - inp_surf.get_height() // 2
        ))

        # Cursor parpadeante cuando el campo está activo
        if input_activo and int(pygame.time.get_ticks() / 500) % 2 == 0:
            cursor_x = input_rect.x + 16 + font_input.size(texto_input)[0]
            cursor_y1 = input_rect.y + 12
            cursor_y2 = input_rect.y + input_rect.h - 12
            pygame.draw.line(screen, (255, 255, 255),
                             (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

        # Hint bajo el input
        hint = font_hint.render('ENTER para confirmar · click en el campo para escribir',
                                True, (150, 150, 150))
        screen.blit(hint, (W // 2 - hint.get_width() // 2,
                           input_rect.bottom + 14))

        # Mensaje de error
        if error_timer > 0:
            err_surf = font_hint.render(mensaje_error, True, (220, 80, 80))
            screen.blit(err_surf, (W // 2 - err_surf.get_width() // 2,
                                   input_rect.bottom + 44))

        runner.flip()

    return False


if __name__ == '__main__':
    pygame.init()
    main_screen = pygame.display.set_mode((800, 600))
    main_clock  = pygame.time.Clock()
    run(main_screen, main_clock, 800, 600)