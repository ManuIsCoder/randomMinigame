import pygame
import random
import math
import glob


TRANSPARENT = (1, 1, 1)


# ── Imágenes ──────────────────────────────────────────────────────────────────

def load_image(path, scale=None):
    """Carga un PNG con alpha. scale=(w, h) opcional."""
    img = pygame.image.load(path).convert_alpha()
    if scale:
        img = pygame.transform.scale(img, scale)
    return img


def load_frames(pattern):
    """
    Carga frames de animación desde archivos que matcheen el patrón.
    Ejemplo: 'assets/win_*.png'
    Retorna lista de surfaces ordenada por nombre de archivo.
    """
    archivos = sorted(glob.glob(pattern))
    if not archivos:
        return []
    return [pygame.image.load(f).convert_alpha() for f in archivos]


# ── Pantalla ──────────────────────────────────────────────────────────────────

def clear(screen):
    """Limpia la pantalla con el color transparente."""
    screen.fill(TRANSPARENT)
    screen.set_colorkey(TRANSPARENT)


def flip():
    """Manda el buffer a la pantalla."""
    pygame.display.flip()


# ── UI compartida ─────────────────────────────────────────────────────────────

def draw_button(screen, font, text, rect, hover=False):
    """
    Dibuja un botón con fondo semitransparente.
    hover=True lo hace más opaco.
    """
    alpha = 200 if hover else 130
    surf  = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    surf.fill((255, 255, 255, alpha))
    screen.blit(surf, rect.topleft)

    pygame.draw.rect(screen, (60, 60, 60), rect, 2, border_radius=8)

    label = font.render(text, True, (20, 20, 20))
    screen.blit(label, (
        rect.x + rect.width  // 2 - label.get_width()  // 2,
        rect.y + rect.height // 2 - label.get_height() // 2,
    ))


def wait_for_start(screen, clock, W, H, titulo):
    """
    Pantalla de inicio con título y botón JUGAR.
    Retorna True si el jugador presionó JUGAR o ENTER.
    Retorna False si cerró la ventana o presionó ESC.
    """
    font_title  = pygame.font.SysFont('monospace', 42, bold=True)
    font_button = pygame.font.SysFont('monospace', 28)
    font_hint   = pygame.font.SysFont('monospace', 18)

    btn = pygame.Rect(W // 2 - 110, H // 2 + 20, 220, 56)

    while True:
        clock.tick(60)
        mx, my = pygame.mouse.get_pos()
        hover  = btn.collidepoint(mx, my)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_RETURN:
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN and hover:
                return True

        clear(screen)

        title_surf = font_title.render(titulo, True, (255, 255, 255))
        screen.blit(title_surf, (
            W // 2 - title_surf.get_width()  // 2,
            H // 2 - 80
        ))

        draw_button(screen, font_button, 'JUGAR', btn, hover)

        hint = font_hint.render('o presioná ENTER', True, (180, 180, 180))
        screen.blit(hint, (
            W // 2 - hint.get_width() // 2,
            btn.bottom + 14
        ))

        flip()


# ── Animación confetti ────────────────────────────────────────────────────────

class _Confetti:
    COLORES = [
        (255, 80,  80),
        (80,  180, 255),
        (80,  220, 100),
        (255, 220, 50),
        (220, 80,  255),
        (255, 160, 40),
        (40,  240, 220),
    ]

    def __init__(self, W, H):
        self.W = W
        self.H = H
        self.x     = random.uniform(0, W)
        self.y     = random.uniform(-H * 0.5, -8)   # empieza fuera de pantalla
        self.size  = random.randint(6, 14)
        self.color = random.choice(self.COLORES)
        self.vel_y = random.uniform(180, 340)        # px/seg hacia abajo
        self.vel_x = random.uniform(-60, 60)         # deriva lateral
        self.rot   = random.uniform(0, 360)          # rotación inicial
        self.rot_vel = random.uniform(-200, 200)     # velocidad de rotación

    def update(self, dt):
        self.y   += self.vel_y * dt
        self.x   += self.vel_x * dt
        self.rot  = (self.rot + self.rot_vel * dt) % 360

    def draw(self, screen):
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        surf.fill((*self.color, 220))
        rotada = pygame.transform.rotate(surf, self.rot)
        screen.blit(rotada, (
            int(self.x) - rotada.get_width()  // 2,
            int(self.y) - rotada.get_height() // 2,
        ))

    def fuera(self):
        return self.y > self.H + 20 or self.x < -20 or self.x > self.W + 20


def _animar_victoria(screen, clock, W, H):
    """Confetti cayendo durante 2 segundos, luego espera input."""
    font_big   = pygame.font.SysFont('monospace', 64, bold=True)
    font_small = pygame.font.SysFont('monospace', 24)

    particulas  = []
    spawn_timer = 0.0
    spawn_rate  = 0.022   # segundos entre cada confetti nuevo
    duracion    = 2.0     # segundos generando confetti
    elapsed     = 0.0
    waiting     = True

    while waiting:
        dt = clock.tick(60) / 1000.0
        elapsed += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if elapsed > duracion:
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                    waiting = False

        # Spawnear confetti solo durante los primeros `duracion` segundos
        if elapsed <= duracion:
            spawn_timer += dt
            while spawn_timer >= spawn_rate:
                spawn_timer -= spawn_rate
                particulas.append(_Confetti(W, H))

        # Actualizar y limpiar las que salieron de pantalla
        for p in particulas:
            p.update(dt)
        particulas = [p for p in particulas if not p.fuera()]

        # Si ya no quedan partículas después de `duracion`, forzar salida
        if elapsed > duracion and not particulas:
            waiting = False

        clear(screen)

        for p in particulas:
            p.draw(screen)

        txt = font_big.render('¡GANASTE!', True, (80, 220, 100))
        screen.blit(txt, (W // 2 - txt.get_width() // 2, H // 2 - 60))

        if elapsed > duracion:
            hint = font_small.render('click o cualquier tecla para continuar', True, (200, 200, 200))
            screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 50))

        flip()


# ── Animación calavera ────────────────────────────────────────────────────────

def _animar_derrota(screen, clock, W, H):
    """
    Carga calavera.png y la anima subiendo y bajando durante 2 segundos.
    Usa una función seno para el movimiento vertical.
    """
    font_big   = pygame.font.SysFont('monospace', 64, bold=True)
    font_small = pygame.font.SysFont('monospace', 24)

    try:
        calavera = load_image('assets/calavera.png')
        # Escalar a un tamaño razonable manteniendo proporción
        max_dim  = min(W, H) // 3
        cw, ch   = calavera.get_width(), calavera.get_height()
        factor   = max_dim / max(cw, ch)
        calavera = pygame.transform.scale(
            calavera, (int(cw * factor), int(ch * factor))
        )
    except FileNotFoundError:
        calavera = None

    AMPLITUD   = 18      # px de recorrido arriba/abajo
    FRECUENCIA = 2.5     # ciclos por segundo
    DURACION   = 2.0     # segundos animando

    elapsed = 0.0
    waiting = True

    # Centro base de la calavera
    base_y = H // 2 - (calavera.get_height() // 2 if calavera else 0) + 20

    while waiting:
        dt = clock.tick(60) / 1000.0
        elapsed += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if elapsed > DURACION:
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                    waiting = False

        clear(screen)

        # Movimiento senoidal vertical
        offset_y = int(math.sin(elapsed * FRECUENCIA * 2 * math.pi) * AMPLITUD)

        if calavera:
            cx = W // 2 - calavera.get_width() // 2
            cy = base_y + offset_y
            screen.blit(calavera, (cx, cy))

        txt = font_big.render('¡PERDISTE!', True, (220, 80, 80))
        screen.blit(txt, (W // 2 - txt.get_width() // 2, H // 2 - 160))

        if elapsed > DURACION:
            hint = font_small.render('click o cualquier tecla para continuar', True, (200, 200, 200))
            screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 50))

        flip()


# ── Punto de entrada único para resultados ────────────────────────────────────

def play_result(screen, clock, W, H, gano: bool):
    """
    Llama a la animación correspondiente según resultado.
    gano=True  → confetti
    gano=False → calavera flotante
    """
    if gano:
        _animar_victoria(screen, clock, W, H)
    else:
        _animar_derrota(screen, clock, W, H)


# ── Ruleta de dificultad ───────────────────────────────────────────────────────

def spin_ruleta(screen, clock, W, H):
    """
    Muestra una ruleta animada con 6 dificultades.
    Orden de sectores (sentido horario): 1, 6, 2, 5, 3, 4.
    La paleta/puntero está a la IZQUIERDA de la rueda.
    Retorna el número de dificultad (1–6) seleccionado.
    """
    # ── Sectores y colores ──────────────────────────────────────────────────
    SECTORES   = [1, 6, 2, 5, 3, 4]          # orden horario
    N          = len(SECTORES)
    DEG_SEC    = 360 / N                      # 60° por sector

    # Colores del verde (fácil) al rojo (difícil)
    COLORS = {
        1: (50,  210,  80),   # verde brillante
        2: (130, 210,  50),   # verde-lima
        3: (220, 210,  30),   # amarillo
        4: (255, 150,  20),   # naranja
        5: (255,  75,  20),   # rojo-naranja
        6: (210,  25,  25),   # rojo intenso
    }
    NOMBRES = {
        1: 'Muy Fácil',
        2: 'Fácil',
        3: 'Normal',
        4: 'Difícil',
        5: 'Muy Difícil',
        6: 'EXTREMO',
    }

    # ── Geometría ───────────────────────────────────────────────────────────
    radius  = min(W, H) // 3
    cx      = W // 2 + 50           # rueda centrada/desplazada a la derecha
    cy      = H // 2

    # ── Elegir resultado y calcular ángulo de parada ─────────────────────────
    # wheel_angle: cuántos grados ha rotado la rueda (sentido horario)
    # Los sectores se dibujan desde (wheel_angle - 90)°, así el sector 0
    # empieza en la parte superior cuando wheel_angle=0.
    # La paleta apunta a 180° (izquierda), por lo que queremos que el centro
    # del sector elegido esté en 180°:
    #   wheel_angle - 90 + (idx + 0.5) * DEG_SEC = 180  →
    #   wheel_angle = 270 - (idx + 0.5) * DEG_SEC
    resultado_idx   = random.randint(0, N - 1)
    resultado       = SECTORES[resultado_idx]
    extra_giros     = random.randint(4, 6) * 360
    angulo_final    = (270 - (resultado_idx + 0.5) * DEG_SEC) % 360
    total_spin      = extra_giros + angulo_final

    # ── Tipografías ─────────────────────────────────────────────────────────
    font_titulo  = pygame.font.SysFont('monospace', 30, bold=True)
    font_num     = pygame.font.SysFont('monospace', 34, bold=True)
    font_result  = pygame.font.SysFont('monospace', 32, bold=True)
    font_nombre  = pygame.font.SysFont('monospace', 22, bold=True)
    font_hint    = pygame.font.SysFont('monospace', 18)

    # ── Estado de la animación ───────────────────────────────────────────────
    DURACION  = 3.5          # segundos girando
    wheel_angle = 0.0
    elapsed     = 0.0
    spinning    = True
    done        = False

    # ── Helper: dibuja un sector de la rueda ─────────────────────────────────
    def draw_sector(idx, angle_offset):
        dif = SECTORES[idx]
        a0  = math.radians(idx * DEG_SEC + angle_offset - 90)
        a1  = math.radians((idx + 1) * DEG_SEC + angle_offset - 90)
        steps  = 30
        points = [(cx, cy)]
        for s in range(steps + 1):
            a = a0 + (a1 - a0) * s / steps
            points.append((cx + radius * math.cos(a),
                           cy + radius * math.sin(a)))

        # Relleno del sector
        pygame.draw.polygon(screen, COLORS[dif], points)
        # Borde del sector
        pygame.draw.polygon(screen, (15, 15, 15), points, 2)

        # Número en el sector
        mid_a  = math.radians((idx + 0.5) * DEG_SEC + angle_offset - 90)
        tx = cx + radius * 0.62 * math.cos(mid_a)
        ty = cy + radius * 0.62 * math.sin(mid_a)
        num_surf = font_num.render(str(dif), True, (255, 255, 255))
        # Sombra suave
        shadow = font_num.render(str(dif), True, (0, 0, 0))
        screen.blit(shadow, (int(tx) - num_surf.get_width() // 2 + 2,
                             int(ty) - num_surf.get_height() // 2 + 2))
        screen.blit(num_surf, (int(tx) - num_surf.get_width() // 2,
                               int(ty) - num_surf.get_height() // 2))

    # ── Bucle principal ───────────────────────────────────────────────────────
    while not done:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if not spinning:
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                    done = True

        # Avanzar animación con ease-out cúbico
        if spinning:
            elapsed += dt
            t          = min(elapsed / DURACION, 1.0)
            ease       = 1 - (1 - t) ** 3
            wheel_angle = total_spin * ease
            if t >= 1.0:
                spinning    = False
                wheel_angle = total_spin  # fijar exacto

        # ── Fondo oscuro ─────────────────────────────────────────────────────
        clear(screen)
        panel = pygame.Surface((W, H), pygame.SRCALPHA)
        panel.fill((10, 10, 20, 210))
        screen.blit(panel, (0, 0))

        # ── Título ───────────────────────────────────────────────────────────
        titulo = font_titulo.render('¡GIRANDO LA RULETA!', True, (220, 220, 255))
        screen.blit(titulo, (W // 2 - titulo.get_width() // 2, 32))

        # ── Sombra exterior de la rueda ───────────────────────────────────────
        pygame.draw.circle(screen, (0, 0, 0, 160), (cx + 4, cy + 4), radius + 6)

        # ── Sectores ─────────────────────────────────────────────────────────
        for i in range(N):
            draw_sector(i, wheel_angle)

        # ── Borde exterior de la rueda ────────────────────────────────────────
        pygame.draw.circle(screen, (220, 220, 220), (cx, cy), radius, 4)

        # ── Círculo central ───────────────────────────────────────────────────
        pygame.draw.circle(screen, (30,  30,  40), (cx, cy), 22)
        pygame.draw.circle(screen, (180, 180, 200), (cx, cy), 22, 3)

        # ── Marcas exteriores cada 60° ────────────────────────────────────────
        for i in range(N):
            a = math.radians(i * DEG_SEC + wheel_angle - 90)
            mx0 = cx + (radius - 1) * math.cos(a)
            my0 = cy + (radius - 1) * math.sin(a)
            mx1 = cx + (radius + 10) * math.cos(a)
            my1 = cy + (radius + 10) * math.sin(a)
            pygame.draw.line(screen, (220, 220, 220), (int(mx0), int(my0)),
                             (int(mx1), int(my1)), 3)

        # ── Paleta/puntero (IZQUIERDA) ────────────────────────────────────────
        px   = cx - radius - 4   # punta del puntero (toca la rueda)
        py   = cy
        ps   = 28                 # tamaño del triángulo
        tip  = (px, py)
        base1 = (px - ps, py - ps // 2)
        base2 = (px - ps, py + ps // 2)
        # Sombra
        sofs = 3
        pygame.draw.polygon(screen, (0, 0, 0),
                            [(tip[0]+sofs, tip[1]+sofs),
                             (base1[0]+sofs, base1[1]+sofs),
                             (base2[0]+sofs, base2[1]+sofs)])
        # Cuerpo dorado
        pygame.draw.polygon(screen, (255, 210, 40), [tip, base1, base2])
        # Borde
        pygame.draw.polygon(screen, (180, 130, 10), [tip, base1, base2], 2)

        # ── Resultado ─────────────────────────────────────────────────────────
        if not spinning:
            col = COLORS[resultado]
            # Recuadro del resultado
            res_text  = f'Dificultad {resultado}  —  {NOMBRES[resultado]}'
            res_surf  = font_result.render(res_text, True, col)
            rw, rh    = res_surf.get_width() + 40, res_surf.get_height() + 20
            rx        = W // 2 - rw // 2
            ry        = H - 120
            box = pygame.Surface((rw, rh), pygame.SRCALPHA)
            box.fill((0, 0, 0, 170))
            screen.blit(box, (rx, ry))
            pygame.draw.rect(screen, col, (rx, ry, rw, rh), 3, border_radius=8)
            screen.blit(res_surf, (rx + 20, ry + 10))

            hint = font_hint.render('click o cualquier tecla para continuar',
                                    True, (160, 160, 180))
            screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 52))

        flip()

    return resultado