import pygame
from settings import *
from sys import exit
from os.path import join, dirname, abspath
from random import choice
import sqlite3
from game import Game
from score import Score
from preview import Preview

# Hàm tạo cơ sở dữ liệu
def create_database():
    connection = sqlite3.connect('highscores.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS highscores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            score INTEGER NOT NULL
        )
    ''')
    connection.commit()
    connection.close()

# Hàm hiển thị giao diện nhập tên
# Hàm hiển thị giao diện nhập tên
def show_start_screen():
    username_input = ''
    input_active = True
    screen = pygame.display.get_surface()

    while input_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and username_input:
                    input_active = False  # Ngừng nhập tên
                elif event.key == pygame.K_BACKSPACE:
                    username_input = username_input[:-1]
                else:
                    username_input += event.unicode

        # Vẽ giao diện
        screen.fill(GRAY)
        font = pygame.font.Font(None, 74)
        title_surface = font.render('Enter your name', True, 'white')
        title_rect = title_surface.get_rect(center=(GAME_WIDTH // 1.3, 150))
        screen.blit(title_surface, title_rect)

        input_font = pygame.font.Font(None, 48)
        input_surface = input_font.render(username_input, True, 'white')
        input_rect = input_surface.get_rect(center=(GAME_WIDTH // 1.6, 250))
        screen.blit(input_surface, input_rect)

        # Vẽ nút bắt đầu
        start_surface = font.render('Press Enter to Start', True, 'yellow')
        start_rect = start_surface.get_rect(center=(GAME_WIDTH // 1.3, 350))
        screen.blit(start_surface, start_rect)

        pygame.display.update()

    return username_input


# Lớp Main
# Lớp Main
class Main:
    def __init__(self):
        pygame.init()
        create_database()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Tetris')

        self.username = show_start_screen()  # Hiển thị giao diện nhập tên
        self.clock = pygame.time.Clock()

        # shapes
        self.next_shapes = [choice(list(TETROMINOS.keys())) for shape in range(3)]

        # components
        self.game = Game(self.get_next_shape, self.update_score, self.username)
        self.score = Score()
        self.preview = Preview()

        # audio
        base_path = dirname(abspath(__file__))
        self.music = pygame.mixer.Sound(join('assets/sound/music.wav'))
        self.music.set_volume(0.05)
        self.music.play(-1)

        # Bắt đầu game
        self.run()  # Di chuyển vào đây để chạy game ngay

    def update_score(self, lines, score, level):
        self.score.lines = lines
        self.score.score = score
        self.score.level = level

    def get_next_shape(self):
        next_shape = self.next_shapes.pop(0)
        self.next_shapes.append(choice(list(TETROMINOS.keys())))
        return next_shape

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            # Vẽ nền
            self.display_surface.fill(GRAY)

            # Chạy game và các thành phần khác
            self.game.run()
            self.score.run()
            self.preview.run(self.next_shapes)

            # Cập nhật giao diện
            pygame.display.update()
            self.clock.tick(60)  # Giới hạn FPS



if __name__ == '__main__':
    main = Main()
    main.run()
