import pygame
import random
import math
import runner

FPS = 60

MOSCA_W        = 64
MOSCA_H        = 64
ALAS_FPS       = 18
SPEED_INICIAL  = 420
SPEED_MAX      = 720
SPEED_INC      = 60
INTENTOS       = 1

RASTRO_LEN     = 28
RASTRO_COLOR   = (255, 255, 255)
RASTRO_W_MAX   = 10
RASTRO_W_MIN   = 1

TIEMPO_LIMITE  = 5.0


def run(screen, clock, W, H) -> bool:

    sprite_a = runner.load_image('assets/mosca_a.png', scale=(MOSCA_W, MOSCA_H))
    sprite_b = runner.load_image('assets/mosca_b.png', scale=(MOSCA_W, MOSCA_H))

    font_small = pygame.font.SysFont('monospace', 22)

    if not runner.wait_for_start(screen, clock, W, H, 'Atrapa la mosca'):
        return False

    mosca_x = float(random.randint(MOSCA_W, W - MOSCA_W))
    mosca_y = float(random.randint(MOSCA_H, H - MOSCA_H))
    angulo  = random.uniform(0, 2 * math.pi)
    speed   = float(SPEED_INICIAL)

    tiempo_restante = TIEMPO_LIMITE

    ala_timer     = 0.0
    ala_frame     = 0
    ala_intervalo = 1.0 / ALAS_FPS

    rastro = []

    giro_timer     = 0.0
    giro_intervalo = 0.30
    giro_max       = 0.8

    cache_sprites = {}

    def get_sprite_rotado(frame, ang):
        # El sprite apunta hacia arriba (270° en coordenadas pygame).
        # Para que la cabeza mire hacia donde va (eje X positivo = 0 rad),
        # sumamos 90° de offset antes de convertir a grados de rotación pygame.
        grados_offset = 90
        grados = int((math.degrees(-ang) + grados_offset) % 360 // 10) * 10
        key = (frame, grados)
        if key not in cache_sprites:
            base = sprite_a if frame == 0 else sprite_b
            cache_sprites[key] = pygame.transform.rotate(base, grados)
        return cache_sprites[key]

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                cx = mosca_x + MOSCA_W / 2
                cy = mosca_y + MOSCA_H / 2
                if math.hypot(mx - cx, my - cy) <= MOSCA_W * 0.55:
                    runner.play_result(screen, clock, W, H, gano=True)
                    return True
                else:
                    runner.play_result(screen, clock, W, H, gano=False)
                    return False

        tiempo_restante -= dt
        if tiempo_restante <= 0:
            runner.play_result(screen, clock, W, H, gano=False)
            return False

        giro_timer += dt
        if giro_timer >= giro_intervalo:
            giro_timer = 0.0
            angulo += random.uniform(-giro_max, giro_max)

        mosca_x += math.cos(angulo) * speed * dt
        mosca_y += math.sin(angulo) * speed * dt

        if mosca_x < 0:
            mosca_x = 0
            angulo  = math.pi - angulo
        elif mosca_x > W - MOSCA_W:
            mosca_x = W - MOSCA_W
            angulo  = math.pi - angulo

        if mosca_y < 0:
            mosca_y = 0
            angulo  = -angulo
        elif mosca_y > H - MOSCA_H:
            mosca_y = H - MOSCA_H
            angulo  = -angulo

        angulo = angulo % (2 * math.pi)

        cx = mosca_x + MOSCA_W / 2
        cy = mosca_y + MOSCA_H / 2
        rastro.append((cx, cy))
        if len(rastro) > RASTRO_LEN:
            rastro.pop(0)

        ala_timer += dt
        if ala_timer >= ala_intervalo:
            ala_timer = 0.0
            ala_frame = 1 - ala_frame

        runner.clear(screen)

        n = len(rastro)
        for i in range(1, n):
            t      = i / (n - 1) if n > 1 else 1.0
            grosor = max(1, round(RASTRO_W_MIN + t * (RASTRO_W_MAX - RASTRO_W_MIN)))
            alpha  = int(60 + t * 180)
            p1, p2 = rastro[i - 1], rastro[i]

            sx = int(min(p1[0], p2[0])) - grosor - 1
            sy = int(min(p1[1], p2[1])) - grosor - 1
            sw = max(1, int(abs(p2[0] - p1[0])) + grosor * 2 + 2)
            sh = max(1, int(abs(p2[1] - p1[1])) + grosor * 2 + 2)

            seg_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.line(
                seg_surf,
                (*RASTRO_COLOR, alpha),
                (int(p1[0]) - sx, int(p1[1]) - sy),
                (int(p2[0]) - sx, int(p2[1]) - sy),
                grosor
            )
            screen.blit(seg_surf, (sx, sy))

        sprite_rot = get_sprite_rotado(ala_frame, angulo)
        rx = int(mosca_x + MOSCA_W / 2 - sprite_rot.get_width()  / 2)
        ry = int(mosca_y + MOSCA_H / 2 - sprite_rot.get_height() / 2)
        screen.blit(sprite_rot, (rx, ry))

        tiempo_color = (220, 80, 80) if tiempo_restante < 2 else (230, 230, 230)
        t_surf = font_small.render(
            f'Tiempo: {max(0, tiempo_restante):.1f}s', True, tiempo_color
        )
        screen.blit(t_surf, (20, 20))

        hint = font_small.render('¡Tenés un solo click!', True, (255, 200, 80))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 50))

        runner.flip()

    return False