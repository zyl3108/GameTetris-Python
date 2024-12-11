from settings import *
from random import choice
from sys import exit
from os.path import join
import sqlite3
import heapq
from timer import Timer # type: ignore


class Game:
    def __init__(self, get_next_shape, update_score,username):
        # General setup
        self.font = pygame.font.Font(join('assets/graphics/Russo_One.ttf'), 50)
        self.game_over = False
        self.username = username
        
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.display_surface = pygame.display.get_surface()
        self.rect = self.surface.get_rect(topleft=(PADDING, PADDING))
        self.sprites = pygame.sprite.Group()

        # Game connection
        self.get_next_shape = get_next_shape
        self.update_score = update_score

        # Lines
        self.line_surface = self.surface.copy()
        self.line_surface.fill((0, 255, 0))
        self.line_surface.set_colorkey((0, 255, 0))
        self.line_surface.set_alpha(120)

        # Tetromino
        self.field_data = [[0 for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.tetromino = Tetromino(
            choice(list(TETROMINOS.keys())),
            self.sprites,
            self.create_new_tetromino,
            self.field_data
        )

        # Timer
        self.down_speed = UPDATE_START_SPEED
        self.down_speed_faster = self.down_speed * 0.3
        self.down_pressed = False
        self.timers = {
            'vertical move': Timer(self.down_speed, True, self.move_down),
            'horizontal move': Timer(MOVE_WAIT_TIME),
            'rotate': Timer(ROTATE_WAIT_TIME)
        }
        self.timers['vertical move'].activate()

        # Score
        self.current_level = 1
        self.current_score = 0
        self.current_lines = 0

        # Sound
        self.landing_sound = pygame.mixer.Sound(join('assets/sound/landing.wav'))
        self.landing_sound.set_volume(0.1)

    def save_highscore(self):
        connection = sqlite3.connect('highscores.db')
        cursor = connection.cursor()
        
        # Kiểm tra xem tên người dùng đã tồn tại hay chưa
        cursor.execute('SELECT score FROM highscores WHERE username = ?', (self.username,))
        existing_score = cursor.fetchone()
        
        if existing_score:
            # Nếu đã tồn tại, cập nhật số điểm nếu cao hơn
            if self.current_score > existing_score[0]:
                cursor.execute('UPDATE highscores SET score = ? WHERE username = ?', (self.current_score, self.username))
        else:
            # Nếu chưa tồn tại, thêm mới
            cursor.execute('INSERT INTO highscores (username, score) VALUES (?, ?)', (self.username, self.current_score))

        connection.commit()
        connection.close()


    def calculate_score(self, num_lines):
        self.current_lines += num_lines
        self.current_score += SCORE_DATA.get(num_lines, 0) * self.current_level

        # Level up
        if self.current_lines % 5 == 0 and self.current_lines > 0:  # Sửa ở đây
            self.current_level += 1
            self.down_speed *= 0.75
            self.down_speed_faster = self.down_speed * 0.3
            self.timers['vertical move'].duration = self.down_speed

        self.update_score(self.current_lines, self.current_score, self.current_level)


    def display_game_over(self):
        """Display the 'Game Over' message, score, highscores, and restart instructions."""
        self.save_highscore()  # Save the high score

        # Tạo các bề mặt cho thông điệp
        game_over_surface = self.font.render("GAME OVER", True, 'white')
        high_score_surface = self.font.render("High Score", True, 'yellow')
        score_surface = self.font.render(f"Score: {self.current_score}", True, 'yellow')
        highscores_surface = self.get_highscores_surface()
        restart_surface = self.font.render("Press R to Restart", True, 'yellow')

        # Tính toán vị trí trung tâm cho văn bản
        game_over_rect = game_over_surface.get_rect(center=(self.display_surface.get_width() // 2, self.display_surface.get_height() // 2 - 350))
        score_rect = score_surface.get_rect(center=(self.display_surface.get_width() // 2, self.display_surface.get_height() // 2-20))
        highscores_rect = highscores_surface.get_rect(center=(self.display_surface.get_width() // 2, self.display_surface.get_height() // 2 + 60))
        restart_rect = restart_surface.get_rect(center=(self.display_surface.get_width() // 2, self.display_surface.get_height() // 2 + 250))
        high_rect = high_score_surface.get_rect(center=(self.display_surface.get_width() // 2, self.display_surface.get_height() // 2 -120))

        # Vẽ các bề mặt lên màn hình
        self.display_surface.blit(game_over_surface, game_over_rect)
        self.display_surface.blit(score_surface, score_rect)
        self.display_surface.blit(highscores_surface, highscores_rect)
        self.display_surface.blit(restart_surface, restart_rect)
        self.display_surface.blit(high_score_surface, high_rect)
        pygame.display.update()

        # Chờ đợi cho đầu vào để khởi động lại
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        waiting = False
                        self.reset_game()
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()



    def get_highscores_surface(self):
        connection = sqlite3.connect('highscores.db')
        cursor = connection.cursor()
        cursor.execute('SELECT username, score FROM highscores ORDER BY score DESC LIMIT 10')
        highscores = cursor.fetchall()
        connection.close()

        highscores_surface = pygame.Surface((400, 300))
        highscores_surface.fill((0, 0, 0))  # Nền đen cho bảng xếp hạng
        font = pygame.font.Font(None, 36)
        
        for i, (username, score) in enumerate(highscores):
            score_surface = font.render(f"{i + 1}. {username}: {score}", True, 'white')
            highscores_surface.blit(score_surface, (10, 20 + i * 30))

        return highscores_surface

    def reset_game(self):
        """Reset the game state."""
        self.game_over = False
        self.field_data = [[0 for _ in range(COLUMNS)] for _ in range(ROWS)]
        
        # Reset score and level
        self.current_level = 1
        self.current_score = 0
        self.current_lines = 0
        
        # Clear sprites
        self.sprites.empty()
        
        # Create new tetromino
        self.tetromino = Tetromino(
            self.get_next_shape(),
            self.sprites,
            self.create_new_tetromino,
            self.field_data
        )

        # Reset timers and speeds
        self.down_speed = UPDATE_START_SPEED
        self.down_speed_faster = self.down_speed * 0.3
        self.timers['vertical move'].duration = self.down_speed
        self.timers['vertical move'].activate()

        # Update score display
        self.update_score(self.current_lines, self.current_score, self.current_level)

    def check_game_over(self):
        """Check if any block is above the screen, indicating game over."""
        for block in self.tetromino.blocks:
            if block.pos.y < 0:
                self.game_over = True

    def create_new_tetromino(self):
        self.landing_sound.play()
        self.check_game_over()
        if self.game_over:
            self.display_game_over()
        else:
            self.check_finished_rows()
            self.tetromino = Tetromino(
                self.get_next_shape(),
                self.sprites,
                self.create_new_tetromino,
                self.field_data
            )

    def timer_update(self):
        for timer in self.timers.values():
            timer.update()

    def move_down(self):
        self.tetromino.move_down()

    def draw_grid(self):
        for col in range(1, COLUMNS):
            x = col * CELL_SIZE
            pygame.draw.line(self.line_surface, LINE_COLOR, (x, 0), (x, self.surface.get_height()), 1)

        for row in range(1, ROWS):
            y = row * CELL_SIZE
            pygame.draw.line(self.line_surface, LINE_COLOR, (0, y), (self.surface.get_width(), y))

        self.surface.blit(self.line_surface, (0, 0))

    def input(self):
        keys = pygame.key.get_pressed()

        # Check horizontal movement
        if not self.timers['horizontal move'].active:
            if keys[pygame.K_LEFT]:
                self.tetromino.move_horizontal(-1)
                self.timers['horizontal move'].activate()
            if keys[pygame.K_RIGHT]:
                self.tetromino.move_horizontal(1)
                self.timers['horizontal move'].activate()

        # Check for rotation
        if not self.timers['rotate'].active:
            if keys[pygame.K_UP]:
                self.tetromino.rotate()
                self.timers['rotate'].activate()

        # Down speedup
        if not self.down_pressed and keys[pygame.K_DOWN]:
            self.down_pressed = True
            self.timers['vertical move'].duration = self.down_speed_faster

        if self.down_pressed and not keys[pygame.K_DOWN]:
            self.down_pressed = False
            self.timers['vertical move'].duration = self.down_speed

    def check_finished_rows(self):
        delete_rows = []
        for i, row in enumerate(self.field_data):
            if all(row):
                delete_rows.append(i)

        if delete_rows:
            for delete_row in delete_rows:
                # Delete full rows
                for block in self.field_data[delete_row]:
                    if block:
                        block.kill()

                # Move down blocks
                for row in range(delete_row, 0, -1):
                    for block in self.field_data[row]:
                        if block:
                            block.pos.y += 1

            # Update field data
            self.field_data = [[0 for _ in range(COLUMNS)] for _ in range(ROWS)]
            for block in self.sprites:
                self.field_data[int(block.pos.y)][int(block.pos.x)] = block

            # Update score
            self.calculate_score(len(delete_rows))

    def run(self):
        if not self.game_over:
            # Update inputs, timers, and sprite movements
            self.input()
            self.timer_update()
            self.sprites.update()

            # Drawing
            self.surface.fill(GRAY)
            self.sprites.draw(self.surface)
            self.draw_grid()
            self.display_surface.blit(self.surface, (PADDING, PADDING))
            pygame.draw.rect(self.display_surface, LINE_COLOR, self.rect, 2, 2)
        else:
            self.display_game_over()


class Tetromino:
    def __init__(self, shape, group, create_new_tetromino, field_data):
        # Setup 
        self.shape = shape
        self.block_positions = TETROMINOS[shape]['shape']
        self.color = TETROMINOS[shape]['color']
        self.create_new_tetromino = create_new_tetromino
        self.field_data = field_data

        # Create blocks
        self.blocks = [Block(group, pos, self.color) for pos in self.block_positions]

    # Collisions
    def next_move_horizontal_collide(self, blocks, amount):
        collision_list = [block.horizontal_collide(int(block.pos.x + amount), self.field_data) for block in blocks]
        return any(collision_list)

    def next_move_vertical_collide(self, blocks, amount):
        collision_list = [block.vertical_collide(int(block.pos.y + amount), self.field_data) for block in blocks]
        return any(collision_list)

    # Movement
    def move_horizontal(self, amount):
        if not self.next_move_horizontal_collide(self.blocks, amount):
            for block in self.blocks:
                block.pos.x += amount

    def move_down(self):
        # Check for vertical collision
        if not self.next_move_vertical_collide(self.blocks, 1):
            # Move each block down
            for block in self.blocks:
                block.pos.y += 1
        else:
            # If collision occurs, add the blocks to the field_data
            for block in self.blocks:
                if 0 <= int(block.pos.y) < ROWS and 0 <= int(block.pos.x) < COLUMNS:
                    self.field_data[int(block.pos.y)][int(block.pos.x)] = block
            self.create_new_tetromino()

    # Rotate
    def rotate(self):
        if self.shape != 'O':
            # 1. Pivot point 
            pivot_pos = self.blocks[0].pos

            # 2. New block positions
            new_block_positions = [block.rotate(pivot_pos) for block in self.blocks]

            # 3. Collision check
            for pos in new_block_positions:
                # Check horizontal boundaries
                if pos.x < 0 or pos.x >= COLUMNS:
                    return

                # Check if position is within the field
                if int(pos.y) < 0 or int(pos.y) >= ROWS or self.field_data[int(pos.y)][int(pos.x)]:
                    return

            # 4. Implement new positions
            for i, block in enumerate(self.blocks):
                block.pos = new_block_positions[i]

import heapq

class Node:
    def __init__(self, tetromino, field_data, g=0):
        self.tetromino = tetromino
        self.field_data = field_data
        self.g = g  # Chi phí từ điểm bắt đầu đến nút hiện tại

    def evaluate(self):
        # Hàm đánh giá: đếm số hàng đã đầy
        return sum([row.count(1) for row in self.field_data])

    def __lt__(self, other):
        return self.evaluate() < other.evaluate()

def heuristic(tetromino, field_data):
    # Heuristic đơn giản: đếm số hàng đã đầy
    return sum([row.count(1) for row in field_data])

def a_star(tetromino, field_data):
    open_list = []
    closed_list = set()

    start_node = Node(tetromino, field_data)
    heapq.heappush(open_list, start_node)

    while open_list:
        current_node = heapq.heappop(open_list)

        if current_node.tetromino.move_down():  # Kiểm tra nếu tetromino đã chạm đáy
            return current_node.tetromino

        closed_list.add(tuple(map(tuple, current_node.field_data)))

        for move in [(0, 1), (1, 0), (-1, 0), (0, -1)]:  # Đi xuống, phải, trái, xoay
            new_tetromino = current_node.tetromino.move(move)  # Tạo trạng thái mới
            new_field_data = update_field(current_node.field_data, new_tetromino)

            if tuple(map(tuple, new_field_data)) in closed_list:
                continue

            g_cost = current_node.g + 1  # Chi phí di chuyển
            h_cost = heuristic(new_tetromino, new_field_data)

            neighbor_node = Node(new_tetromino, new_field_data, g_cost)

            if neighbor_node not in open_list:
                heapq.heappush(open_list, neighbor_node)

    return tetromino  # Không tìm thấy đường

def hill_climbing(tetromino, field_data):
    current_node = Node(tetromino, field_data)

    while True:
        best_node = current_node
        best_score = best_node.evaluate()

        for move in [(0, 1), (1, 0), (-1, 0), (0, -1)]:  # Đi xuống, phải, trái, xoay
            new_tetromino = current_node.tetromino.move(move)  # Tạo trạng thái mới
            new_field_data = update_field(current_node.field_data, new_tetromino)
            neighbor_node = Node(new_tetromino, new_field_data)

            score = neighbor_node.evaluate()
            if score < best_score:  # Tìm trạng thái tốt hơn
                best_node = neighbor_node
                best_score = score

        if best_node == current_node:  # Không tìm thấy trạng thái tốt hơn
            break

        current_node = best_node  # Cập nhật trạng thái hiện tại

    return current_node.tetromino  # Trả về trạng thái tốt nhất cuối cùng

def update_field(field_data, tetromino):
    # Cập nhật dữ liệu field với vị trí mới của tetromino
    for block in tetromino.blocks:
        if 0 <= block.pos.y < ROWS and 0 <= block.pos.x < COLUMNS:
            field_data[int(block.pos.y)][int(block.pos.x)] = block
    return field_data

def bfs(tetromino, field_data):
    queue = [(tetromino, field_data)]
    visited = set()

    while queue:
        current_tetromino, current_field_data = queue.pop(0)

        if current_tetromino.move_down():  # Kiểm tra nếu tetromino đã chạm đáy
            return current_tetromino

        for move in [(0, 1), (1, 0), (-1, 0), (0, -1)]:  # Đi xuống, phải, trái, xoay
            new_tetromino = current_tetromino.move(move)  # Tạo trạng thái mới
            new_field_data = update_field(current_field_data, new_tetromino)

            if tuple(map(tuple, new_field_data)) not in visited:
                visited.add(tuple(map(tuple, new_field_data)))
                queue.append((new_tetromino, new_field_data))

    return tetromino  # Không tìm thấy đường



class Block(pygame.sprite.Sprite):
	def __init__(self, group, pos, color):
		
		# general
		super().__init__(group)
		self.image = pygame.Surface((CELL_SIZE,CELL_SIZE))
		self.image.fill(color)
		
		# position
		self.pos = pygame.Vector2(pos) + BLOCK_OFFSET
		self.rect = self.image.get_rect(topleft = self.pos * CELL_SIZE)

	def rotate(self, pivot_pos):

		return pivot_pos + (self.pos - pivot_pos).rotate(90)

	def horizontal_collide(self, x, field_data):
		if not 0 <= x < COLUMNS:
			return True

		if field_data[int(self.pos.y)][x]:
			return True

	def vertical_collide(self, y, field_data):
		if y >= ROWS:
			return True

		if y >= 0 and field_data[y][int(self.pos.x)]:
			return True

	def update(self):

		self.rect.topleft = self.pos * CELL_SIZE