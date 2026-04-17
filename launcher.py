import os

os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = '0'
os.environ['SDL_VIDEODRIVER'] = 'x11'

import pygame
import sys
import random
import importlib
import glob


WIDTH, HEIGHT = 800, 600


def get_games():
    archivos = glob.glob('games/*.py')
    return [
        os.path.splitext(os.path.basename(f))[0]
        for f in archivos
        if not os.path.basename(f).startswith('_')
    ]


def set_window_transparent():
    """
    Intenta activar transparencia real de ventana vía xdotool.
    Falla silenciosamente si no está disponible.
    """
    try:
        import subprocess
        info = pygame.display.get_wm_info()
        wid  = info.get('window')
        if wid:
            subprocess.Popen(
                ['xdotool', 'set_window', '--name', 'minijuegos', str(wid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    except Exception:
        pass


def pantalla_error(screen, clock, mensaje):
    """Muestra un mensaje de error hasta que el usuario cierre."""
    font = pygame.font.SysFont('monospace', 24)
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                return
        screen.fill((20, 20, 20))
        surf = font.render(mensaje, True, (220, 80, 80))
        screen.blit(surf, (WIDTH  // 2 - surf.get_width()  // 2,
                           HEIGHT // 2 - surf.get_height() // 2))
        pygame.display.flip()


def main():
    pygame.init()

    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT),
        pygame.NOFRAME
    )
    pygame.display.set_caption('minijuegos')

    set_window_transparent()

    clock = pygame.time.Clock()

    juegos = get_games()
    if not juegos:
        pantalla_error(screen, clock, 'No hay juegos en games/')
        pygame.quit()
        sys.exit(1)

    jugados = []   # para no repetir hasta haber pasado por todos

    while True:
        # Rotar por todos los juegos antes de repetir
        disponibles = [j for j in juegos if j not in jugados]
        if not disponibles:
            jugados     = []
            disponibles = juegos[:]

        nombre = random.choice(disponibles)
        jugados.append(nombre)

        try:
            modulo = importlib.import_module(f'games.{nombre}')
            importlib.reload(modulo)
        except Exception as e:
            pantalla_error(screen, clock, f'Error cargando {nombre}: {e}')
            continue

        pygame.display.set_caption(nombre)

        try:
            gano = modulo.run(screen, clock, WIDTH, HEIGHT)
        except Exception as e:
            pantalla_error(screen, clock, f'Error en {nombre}: {e}')
            continue

        if gano:
            break
        # perdió → siguiente juego random

    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    main()