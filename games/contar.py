import pygame
import sys
import random
import runner

FPS = 60

# Diccionario de colores permitidos
COLORES = {
    'AMARILLAS': (255, 220, 50),
    'ROJAS':     (220, 50, 50),
    'AZULES':    (50, 100, 255),
    'VERDES':    (50, 220, 80)
}

class Pelota:
    def __init__(self, W, H, speed_mult):
        self.color_name = random.choice(list(COLORES.keys()))
        self.color = COLORES[self.color_name]
        self.radio = random.randint(20, 40)
        
        # Las pelotas pasan más o menos por el medio de la pantalla
        self.y = random.randint(H // 4, 3 * H // 4)
        
        # Dirección aleatoria: de izquierda a derecha o viceversa
        if random.choice([True, False]):
            self.x = -self.radio - 10
            self.vx = random.uniform(150, 300) * speed_mult
        else:
            self.x = W + self.radio + 10
            self.vx = random.uniform(-300, -150) * speed_mult
            
        # Ligera variación vertical para que se crucen entre ellas
        self.vy = random.uniform(-40, 40) * speed_mult

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, screen):
        # Cuerpo de la pelota
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radio)
        # Brillo suave
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x - self.radio*0.3), int(self.y - self.radio*0.3)), self.radio // 4)
        # Borde oscuro
        pygame.draw.circle(screen, (20, 20, 20), (int(self.x), int(self.y)), self.radio, 2)

    def fuera_de_pantalla(self, W, H):
        # Verifica si ya salió por completo de los bordes
        return (self.x < -self.radio - 50 or self.x > W + self.radio + 50 or
                self.y < -self.radio - 50 or self.y > H + self.radio + 50)

def run(screen, clock, W, H) -> bool:
    # ── Pantalla de inicio ────────────────────────────────────────────────────
    if not runner.wait_for_start(screen, clock, W, H, 'Contar'):
        return False

    # ── Ruleta de dificultad ──────────────────────────────────────────────────
    dificultad = runner.spin_ruleta(screen, clock, W, H)
    
    # ── Configuraciones según dificultad ──────────────────────────────────────
    # Dificultad 1: Pocas pelotas, lentas
    # Dificultad 6: Muchas pelotas, muy rápidas, se amontonan
    cantidad_total  = (10 + dificultad * 8) // 4
    speed_mult      = 0.7 + (dificultad * 0.35)
    spawn_rate_base = (max(0.08, 1.2 - dificultad * 0.18) / 2)
    
    # Elegir el objetivo de la partida
    target_color_name = random.choice(list(COLORES.keys()))
    
    # Pre-generar todas las pelotas que van a pasar
    pelotas_pendientes = [Pelota(W, H, speed_mult) for _ in range(cantidad_total)]
    respuesta_correcta = sum(1 for p in pelotas_pendientes if p.color_name == target_color_name)
    
    pelotas_activas = []
    
    # ── Control de Fases ──────────────────────────────────────────────────────
    fase = 'MOSTRAR_OBJETIVO'
    fase_timer  = 1.5
    spawn_timer = 0.5 
    
    # ── UI y Texto ────────────────────────────────────────────────────────────
    texto_input   = ''
    input_activo  = True
    error_timer   = 0.0
    mensaje_error = ''
    
    font_titulo = pygame.font.SysFont('monospace', 42, bold=True)
    font_input  = pygame.font.SysFont('monospace', 36)
    font_hint   = pygame.font.SysFont('monospace', 20)
    
    input_rect = pygame.Rect(W // 2 - 200, H // 2 + 20, 400, 60)

    # ── Bucle Principal ───────────────────────────────────────────────────────
    while True:
        dt = clock.tick(FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
                
            if fase == 'INPUT':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    input_activo = input_rect.collidepoint(event.pos)
                    
                if event.type == pygame.KEYDOWN and input_activo:
                    if event.key == pygame.K_BACKSPACE:
                        texto_input = texto_input[:-1]
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if not texto_input:
                            continue
                        try:
                            valor = int(texto_input)
                            if valor == respuesta_correcta:
                                runner.play_result(screen, clock, W, H, gano=True)
                                return True
                            else:
                                # Respuesta incorrecta equivale a derrota instantánea
                                runner.play_result(screen, clock, W, H, gano=False)
                                return False
                        except ValueError:
                            mensaje_error = 'Ingresá un número entero'
                            error_timer   = 1.5
                            texto_input   = ''
                    else:
                        # Solo permitir ingresar números
                        car = event.unicode
                        if car in '0123456789':
                            texto_input += car

        runner.clear(screen)
        
        # ── Lógica Visual por Fases ───────────────────────────────────────────
        if fase == 'MOSTRAR_OBJETIVO':
            fase_timer -= dt
            if fase_timer <= 0:
                fase = 'JUGANDO'
                
            txt = font_titulo.render(f'¡Contá todas las pelotas!', True, COLORES[target_color_name])
            screen.blit(txt, (W // 2 - txt.get_width() // 2, H // 2 - txt.get_height() // 2))
            
            hint = font_hint.render('Preparate...', True, (180, 180, 180))
            screen.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 50))
            
        elif fase == 'JUGANDO':
            spawn_timer -= dt
            # Soltar nuevas pelotas
            if spawn_timer <= 0 and pelotas_pendientes:
                pelotas_activas.append(pelotas_pendientes.pop())
                spawn_timer = spawn_rate_base * random.uniform(0.5, 1.5)
                
            # Actualizar y dibujar
            for p in pelotas_activas:
                p.update(dt)
                p.draw(screen)
                
            # Limpiar las que ya salieron de pantalla
            pelotas_activas = [p for p in pelotas_activas if not p.fuera_de_pantalla(W, H)]
            
            # Pasar a respuesta cuando no quede ninguna
            if not pelotas_pendientes and not pelotas_activas:
                fase = 'INPUT'
                
        elif fase == 'INPUT':
            if error_timer > 0:
                error_timer -= dt
                
            pregunta = font_titulo.render(f'¿Cuántas {target_color_name} pasaron?', True, COLORES[target_color_name])
            screen.blit(pregunta, (W // 2 - pregunta.get_width() // 2, H // 2 - 80))
            
            # Dibujo de la caja de texto
            color_borde = (100, 180, 255) if input_activo else (120, 120, 120)
            fondo_input = pygame.Surface((input_rect.w, input_rect.h), pygame.SRCALPHA)
            fondo_input.fill((255, 255, 255, 30) if input_activo else (255, 255, 255, 15))
            screen.blit(fondo_input, input_rect.topleft)
            pygame.draw.rect(screen, color_borde, input_rect, 2, border_radius=8)

            if texto_input:
                inp_surf = font_input.render(texto_input, True, (255, 255, 255))
            else:
                inp_surf = font_input.render('ingresá cantidad...' if not input_activo else '', True, (120, 120, 120))
                
            screen.blit(inp_surf, (
                input_rect.x + 16, 
                input_rect.y + input_rect.h // 2 - inp_surf.get_height() // 2
            ))

            # Cursor parpadeante
            if input_activo and int(pygame.time.get_ticks() / 500) % 2 == 0:
                cursor_x = input_rect.x + 16 + font_input.size(texto_input)[0]
                pygame.draw.line(screen, (255, 255, 255), (cursor_x, input_rect.y + 12), (cursor_x, input_rect.y + input_rect.h - 12), 2)

            # Mensaje de error (si tipea letras o algo inválido)
            if error_timer > 0:
                err_surf = font_hint.render(mensaje_error, True, (220, 80, 80))
                screen.blit(err_surf, (W // 2 - err_surf.get_width() // 2, input_rect.bottom + 20))

        runner.flip()

    return False

if __name__ == '__main__':
    pygame.init()
    main_screen = pygame.display.set_mode((800, 600))
    main_clock  = pygame.time.Clock()
    run(main_screen, main_clock, 800, 600)
