import sys
import subprocess
import os
from random import randint

# Автоматическая установка Ursina
try:
    from ursina import *
    from ursina.prefabs.first_person_controller import FirstPersonController
except ImportError:
    print("Устанавливаем Ursina...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ursina"])
    from ursina import *
    from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

# ===== ОПТИМИЗАЦИИ ===== #
window.fps_counter.enabled = False
window.exit_button.visible = False
scene.fog_density = 0.02
# Убрана строка с render.setShaderAuto() так как она не нужна

# ===== НАСТРОЙКИ ===== #
BLOCK_TYPES = ['grass', 'stone', 'wood', 'water', 'plank', 'leaf', 'lava', 'dirt']
selected_block = 0
inventory = {block: 99 for block in BLOCK_TYPES}
show_inventory = False

# ===== ЗАГРУЗКА ТЕКСТУР ===== #
textures = {
    'grass': load_texture('grass_block.png'),
    'stone': load_texture('stone.jpeg'),
    'wood': load_texture('wood.jpg'),
    'water': load_texture('water.png'),
    'plank': load_texture('doski.jpg'),
    'leaf': load_texture('leaves.jpg'),
    'lava': load_texture('lava.jpg'),
    'dirt': load_texture('zemlya.jpg')
}

# Проверка загрузки текстур
for name, tex in textures.items():
    if not tex:
        print(f"Ошибка загрузки текстуры: {name}")
        textures[name] = 'white_cube'

# ===== ОТКЛЮЧЕНИЕ ТЕНЕЙ ===== #
if hasattr(Entity, 'default_shader'):
    Entity.default_shader = Shader.load(Shader.GLSL, 
        vertex='''
        #version 140
        uniform mat4 p3d_ModelViewProjectionMatrix;
        in vec4 p3d_Vertex;
        in vec2 p3d_MultiTexCoord0;
        out vec2 uv;
        void main() {
            gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
            uv = p3d_MultiTexCoord0;
        }
        ''',
        fragment='''
        #version 140
        uniform sampler2D p3d_Texture0;
        uniform vec4 p3d_Color;
        in vec2 uv;
        out vec4 fragColor;
        void main() {
            fragColor = texture(p3d_Texture0, uv) * p3d_Color;
        }
        '''
    )

# ===== ИНВЕНТАРЬ ===== #
class Inventory(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.bg = Entity(
            parent=self,
            model='quad',
            color=color.black66,
            scale=(0.6, 0.3),
            y=-0.3
        )
        self.slots = []
        for i, block in enumerate(BLOCK_TYPES):
            slot = Entity(
                parent=self,
                model='quad',
                texture=textures[block],
                scale=(0.08, 0.08),
                x=-0.25 + i*0.07,
                y=-0.3
            )
            self.slots.append(slot)
        self.enabled = False

inventory_ui = Inventory()

# ===== БЛОКИ ===== #
class Block(Button):
    def __init__(self, position=(0,0,0), block_type='grass'):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            texture=textures[block_type],
            color=color.white,
            scale=1,
            origin_y=0.5,
            collision=True,
            collider='box'
        )
        self.block_type = block_type

# ===== ГЕНЕРАЦИЯ МИРА ===== #
def generate_tree(x, z):
    height = randint(4,6)
    for y in range(1, height+1):
        Block(position=(x,y,z), block_type='wood')
    for dy in [height-1, height, height+1]:
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) + abs(dz) + abs(dy-height) < 4:
                    Block(position=(x+dx, dy+1, z+dz), block_type='leaf')

def generate_terrain():
    for x in range(-20, 20):
        for z in range(-20, 20):
            for y in range(-3, 0):
                Block(position=(x,y,z), block_type='stone')
            Block(position=(x,0,z), block_type='grass')
            Block(position=(x,-1,z), block_type='dirt')
            if randint(0,20) == 1:
                generate_tree(x,z)
            if randint(0,30) == 1:
                Block(position=(x,-1,z), block_type='lava')

# ===== УПРАВЛЕНИЕ ===== #
def input(key):
    global selected_block, show_inventory
    
    if key == 'tab':
        show_inventory = not show_inventory
        inventory_ui.enabled = show_inventory
        mouse.locked = not show_inventory
    
    if not show_inventory:
        if key == 'left mouse down' and mouse.hovered_entity:
            inventory[mouse.hovered_entity.block_type] += 1
            destroy(mouse.hovered_entity)
        elif key == 'right mouse down' and mouse.hovered_entity:
            if inventory[BLOCK_TYPES[selected_block]] > 0:
                Block(
                    position=mouse.hovered_entity.position + mouse.normal,
                    block_type=BLOCK_TYPES[selected_block]
                )
                inventory[BLOCK_TYPES[selected_block]] -= 1
        
        for i in range(len(BLOCK_TYPES)):
            if key == str(i+1):
                selected_block = i

def update():
    if show_inventory:
        for i, slot in enumerate(inventory_ui.slots):
            slot.color = color.gray if i != selected_block else color.white

# ===== ЗАПУСК ===== #
generate_terrain()
player = FirstPersonController(
    position=(0,10,0),
    gravity=1.8,
    jump_height=0.25,
    speed=5
)
Sky(color=color.rgb(135, 206, 235))
mouse.locked = True


app.run()
