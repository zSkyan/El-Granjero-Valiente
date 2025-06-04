# Bibliotecas necesarias para el juego
import pygame
import sys
import random
import os

# Inicialización de Pygame
pygame.init()

# Constantes
ANCHO_PANTALLA = 800 # (en pixeles)
ALTO_PANTALLA = 600 # (en pixeles)
COLOR_BLANCO = (255, 255, 255)
COLOR_NEGRO = (0, 0, 0)
COLOR_FONDO_DEFECTO = (160, 120, 80) # en tal caso de no cargar la asset del background

# Configuración de la pantalla al iniciar
pantalla = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA)) 
pygame.display.set_caption("El granjero valiente")

# Reloj para controlar FPS, más que todo para limitarlo y no consumir tanta CPU
reloj = pygame.time.Clock() # objeto (reloj)
FPS = 60

# Cargar Assets (Imágenes)
ASSETS_DIR = "assets" # nombre de la carpeta

# Intentar cargar el background
try:
    ruta_fondo = os.path.join(ASSETS_DIR, "granero.png")
    fondo_granero = pygame.image.load(ruta_fondo).convert_alpha() # convert_alpha para mayor optimización con Pygame
    fondo_granero = pygame.transform.scale(fondo_granero, (ANCHO_PANTALLA, ALTO_PANTALLA))
# Manejo del error
except pygame.error as e:
    print(f"No se pudo cargar '{ruta_fondo}': {e}. Usando color de fondo por defecto.")
    fondo_granero = None # dejarlo en None, para saber que no se pudo cargar

# Tamaños de las imágenes (en pixeles)
GRANJERO_ANCHO_IMG = 70
GRANJERO_ALTO_IMG = 70
PLAGA_ANCHO_IMG = 45
PLAGA_ALTO_IMG = 45

# Cargar imagen del granjero y crear variantes para él
granjero_img_base = None 
granjero_img_quieto = None
granjero_img_derecha = None
granjero_img_izquierda = None
granjero_mask_quieto = None
granjero_mask_derecha = None
granjero_mask_izquierda = None
imagen_granjero_actual = None
mascara_granjero_actual = None

ruta_granjero_base = os.path.join(ASSETS_DIR, "granjero.png") # ruta de la imagen del granjero

try:
    img_temp_base = pygame.image.load(ruta_granjero_base).convert_alpha() # optimizarla
    granjero_img_base = pygame.transform.scale(img_temp_base, (GRANJERO_ANCHO_IMG, GRANJERO_ALTO_IMG)) 

    # El granjero hacía la derecha y quieto, son lo mismo, por eso se iguala
    granjero_img_quieto = granjero_img_base
    granjero_img_derecha = granjero_img_base
    # Creación de la máscara apartir de la imagen, para ver que pixeles son opacos (para la colisiones)
    granjero_mask_quieto = pygame.mask.from_surface(granjero_img_quieto)
    granjero_mask_derecha = granjero_mask_quieto

    # Para ponerlo a la izquierda, se voltea horizontalmente
    granjero_img_izquierda = pygame.transform.flip(granjero_img_base, True, False)
    granjero_mask_izquierda = pygame.mask.from_surface(granjero_img_izquierda) # nueva máscara con la imagen volteada

    print(f"'{ruta_granjero_base}' cargada correctamente.")
# Manejo de errores
except pygame.error as e:
    print(f"Error al cargar '{ruta_granjero_base}': {e}")

if granjero_img_quieto:
    imagen_granjero_actual = granjero_img_quieto
    if granjero_mask_quieto:
        mascara_granjero_actual = granjero_mask_quieto
else:
    print("La imagen granjero no se cargó bien. Colisión y visualización afectadas.")

# Cargar imagen y máscara de la plaga 
plaga_img = None
plaga_mask = None
try:
    ruta_plaga = os.path.join(ASSETS_DIR, "scarab.png")
    plaga_img_original = pygame.image.load(ruta_plaga).convert_alpha() # optimización
    plaga_img = pygame.transform.scale(plaga_img_original, (PLAGA_ANCHO_IMG, PLAGA_ALTO_IMG))
    plaga_mask = pygame.mask.from_surface(plaga_img) # crear la máscara
except pygame.error as e:
    print(f"No se pudo cargar '{ruta_plaga}' o crear su máscara: {e}. Se usará círculo y rect para la colisión.")

# Fuentes para el mensaje de puntos
fuente_puntos = pygame.font.Font(None, 50)
fuente_game_over = pygame.font.Font(None, 74)

# Variables del granjero
granjero_x = 50 # posición inicial X del granjero
granjero_y = ALTO_PANTALLA - GRANJERO_ALTO_IMG - 20 # posición inicial Y del granjero
granjero_velocidad = 7 # los pixeles que se moverá el granjero al presionar las flechas
granjero_rect = pygame.Rect(granjero_x, granjero_y, GRANJERO_ANCHO_IMG, GRANJERO_ALTO_IMG) # detección de colisiones simples

# VCariables de las plagas
plagas = [] # lista vacía (diccionario)
NUM_PLAGAS_INICIAL = 3 # plagas al iniciar el juego
VELOCIDAD_PLAGA_MIN = 2 # velocidad mínima de un plaga al caer
VELOCIDAD_PLAGA_MAX = 5 # velocidad máxima de una plaga al caer
MAX_PLAGAS = 10 # límite máximo de plagas en pantalla

# Puntuación
puntos = 0 # se empieza con 0 puntos

# Estado del juego (manejo con variables booleanas)
game_over = False
mostrando_menu_inicio = True

# Funciones
def crear_plaga():
    # Generación de la plaga aleatoriamente, pero sin que se vaya a salir de la pantalla
    x = random.randint(0, ANCHO_PANTALLA - PLAGA_ANCHO_IMG)
    y = random.randint(-100, -PLAGA_ALTO_IMG)
    velocidad = random.randint(VELOCIDAD_PLAGA_MIN, VELOCIDAD_PLAGA_MAX)
    return {'rect': pygame.Rect(x, y, PLAGA_ANCHO_IMG, PLAGA_ALTO_IMG),
            'velocidad': velocidad,
            'mask': plaga_mask}

def mover_plagas(lista_plagas):
    # Recorre cada plaga en la lista de plagas
    for plaga_data in lista_plagas:
        plaga_data['rect'].y += plaga_data['velocidad'] # mover la plaga hacía abajo según la velocidad que tenga
        if plaga_data['rect'].top > ALTO_PANTALLA: # si la plaga sale por debajo de la pantalla, se tendría que reciclar y volverla a la parte de arriba con una nueva velocidad, dándole una nueva posición en X y en Y
            plaga_data['rect'].x = random.randint(0, ANCHO_PANTALLA - PLAGA_ANCHO_IMG)
            plaga_data['rect'].y = random.randint(-100, -PLAGA_ALTO_IMG)
            plaga_data['velocidad'] = random.randint(VELOCIDAD_PLAGA_MIN, VELOCIDAD_PLAGA_MAX)

def dibujar_elementos():
    # dibujar todo en la pantalla (granero, granjero y la plaga)
    if fondo_granero:
        pantalla.blit(fondo_granero, (0, 0)) # dibuja el granero (pues, si se cargó correctamente)
    else:
        pantalla.fill(COLOR_FONDO_DEFECTO) # si no hay fondo, lo rellena con el color por defecto definido

    if imagen_granjero_actual:
        pantalla.blit(imagen_granjero_actual, granjero_rect) # dibuja el granjero
    else:
        pygame.draw.rect(pantalla, (0,150,0), granjero_rect) # si no está, se dibuja un rectángulo verde 

    for plaga_data in plagas:
        if plaga_img:
            pantalla.blit(plaga_img, plaga_data['rect']) # dibuja las plagas
        else:
            pygame.draw.circle(pantalla, (80,80,80), plaga_data['rect'].center, PLAGA_ANCHO_IMG // 2) # sí no, un circulo gris como plaga


    texto_puntos = fuente_puntos.render(f"Puntos: {puntos}", True, COLOR_BLANCO) # dibuja puntuación, creando una imagen apartir del texto
    pantalla.blit(texto_puntos, (10, 10)) # se dibuja en la esquina de arriba a la izquierda

    # Mostrar los mensajes del game over
    if game_over:
        texto_go = fuente_game_over.render("GAME OVER", True, COLOR_NEGRO)
        texto_reiniciar = fuente_puntos.render("Presiona R para reiniciar", True, COLOR_NEGRO) 
        go_rect = texto_go.get_rect(center=(ANCHO_PANTALLA / 2, ALTO_PANTALLA / 2 - 30)) # para centrar
        reiniciar_rect = texto_reiniciar.get_rect(center=(ANCHO_PANTALLA / 2, ALTO_PANTALLA / 2 + 30))
        pantalla.blit(texto_go, go_rect)
        pantalla.blit(texto_reiniciar, reiniciar_rect)

    # Mostrar todos los mensajes en el menú de inicio
    if mostrando_menu_inicio:
        if not fondo_granero:
             pantalla.fill(COLOR_FONDO_DEFECTO)
        else:
            pantalla.blit(fondo_granero, (0,0))

        titulo = fuente_game_over.render("EL GRANJERO VALIENTE", True, COLOR_NEGRO)
        instruccion = fuente_puntos.render("Presiona ESPACIO para empezar", True, COLOR_NEGRO)
        titulo_rect = titulo.get_rect(center=(ANCHO_PANTALLA / 2, ALTO_PANTALLA / 2 - 50))
        instruccion_rect = instruccion.get_rect(center=(ANCHO_PANTALLA / 2, ALTO_PANTALLA / 2 + 30))
        pantalla.blit(titulo, titulo_rect)
        pantalla.blit(instruccion, instruccion_rect)


def reiniciar_juego():
    # se reseteará todas las variables para comenzar de nuevo
    global granjero_x, granjero_y, granjero_rect, puntos, game_over, plagas
    global imagen_granjero_actual, mascara_granjero_actual

    granjero_x = 50
    granjero_y = ALTO_PANTALLA - GRANJERO_ALTO_IMG - 20
    granjero_rect.topleft = (granjero_x, granjero_y)
    puntos = 0
    game_over = False
    plagas.clear()
    for _ in range(NUM_PLAGAS_INICIAL):
        plagas.append(crear_plaga())
    
    if granjero_img_quieto and granjero_mask_quieto:
        imagen_granjero_actual = granjero_img_quieto
        mascara_granjero_actual = granjero_mask_quieto
    else: 
        imagen_granjero_actual = None
        mascara_granjero_actual = None


# Bucle del juego
ejecutando = True
while ejecutando:
    # Manejo de eventos (todas las entradas del jugador, como las teclas que se oprimen)
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT: # evento sí el jugador cierra la ventana
            ejecutando = False
        if evento.type == pygame.KEYDOWN: # sí se presionó una tecla
            if mostrando_menu_inicio:
                if evento.key == pygame.K_SPACE: # sí se presionó el espacio
                    mostrando_menu_inicio = False
                    reiniciar_juego()
            elif game_over:
                if evento.key == pygame.K_r: # sí se presionó la tecla R
                    reiniciar_juego()

    if not mostrando_menu_inicio and not game_over:
        teclas = pygame.key.get_pressed()
        
        # Granjero quieto, mirando a la derecha
        if granjero_img_quieto and granjero_mask_quieto:
            imagen_granjero_actual = granjero_img_quieto
            mascara_granjero_actual = granjero_mask_quieto

        # Movimiento del granjero
        if teclas[pygame.K_LEFT] and granjero_rect.left > 0:
            granjero_rect.x -= granjero_velocidad
            if granjero_img_izquierda and granjero_mask_izquierda:
                imagen_granjero_actual = granjero_img_izquierda
                mascara_granjero_actual = granjero_mask_izquierda
        elif teclas[pygame.K_RIGHT] and granjero_rect.right < ANCHO_PANTALLA:
            granjero_rect.x += granjero_velocidad
            if granjero_img_derecha and granjero_mask_derecha:
                imagen_granjero_actual = granjero_img_derecha
                mascara_granjero_actual = granjero_mask_derecha
        
        mover_plagas(plagas)

        # Detección de colisiones
        colision_detectada_este_frame = False
        if mascara_granjero_actual and plaga_mask: # intentar si ambas máscaras existen (granjero, plagas)
            for plaga_data in plagas:
                if granjero_rect.colliderect(plaga_data['rect']):
                    offset_x = plaga_data['rect'].x - granjero_rect.x
                    offset_y = plaga_data['rect'].y - granjero_rect.y
                    
                    if mascara_granjero_actual.overlap(plaga_data['mask'], (offset_x, offset_y)):
                        game_over = True # colisión y poner el game over en true
                        colision_detectada_este_frame = True
                        break # salir del bucle, ya que hubo colisión
        # Utilizar rectángulos en tal caso sí alguna máscara falla
        elif not mascara_granjero_actual or not plaga_mask:
            for plaga_data in plagas:
                 if granjero_rect.colliderect(plaga_data['rect']):
                    game_over = True
                    colision_detectada_este_frame = True
                    break
        
        # Si no hubo colisión y el granjero llega al final de la pantalla
        if not game_over and granjero_rect.right >= ANCHO_PANTALLA:
            puntos += 10
            granjero_rect.left = 0 # Reiniciar la posición del granjero al lado izquierdo
            
            # Aumentar el número de plagas cada 50 puntos, hasta un máximo
            if len(plagas) < MAX_PLAGAS and puntos > 0 and puntos % 50 == 0:
                plagas.append(crear_plaga())
                print(f"Nueva plaga añadida. Total plagas: {len(plagas)}")
    
    dibujar_elementos() # llamado a la función para dibujar todo
    pygame.display.flip() # actualizar la pantalla, para ver lo nuevo dibujado
    reloj.tick(FPS) # limitar los FPS a 60

pygame.quit() # desactivación de los módulos de Pygame
sys.exit() # cierre limpio