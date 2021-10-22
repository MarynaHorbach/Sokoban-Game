import arcade
import copy
from datetime import datetime

SPRITE_SCALING = 0.5
SPRITE_NATIVE_SIZE = 64
SPRITE_SIZE = int(SPRITE_NATIVE_SIZE * SPRITE_SCALING)

HEIGHT = 20
WIDTH = 30

SCREEN_WIDTH = SPRITE_SIZE * WIDTH
SCREEN_HEIGHT = SPRITE_SIZE * HEIGHT
SCREEN_TITLE = "Sokoban"

FLOOR = " "
WALL = "X"
PLAYER = "@"
BOX = "*"
TARGET = "."
BOX_ON_TARGET = "$"
PLAYER_ON_TARGET = "+"

SPRITES = {
    FLOOR: "floor.png",
    WALL: "wall.png",
    PLAYER: "player.png",
    BOX: "box.png",
    TARGET: "target.png",
    BOX_ON_TARGET: "box_on_target.png",
    PLAYER_ON_TARGET: "target.png"
}

#creating list of levels
LEVELS = list()
for i in range(20):
    LEVELS.append(str(i + 1) + '.txt')


def inside(x, y):
    return 0 <= x < HEIGHT and 0 <= y < WIDTH


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("start.png")
        arcade.set_background_color(arcade.color.WHITE)

    def on_draw(self):
        arcade.start_render()

        arcade.draw_lrwh_rectangle_textured(
            0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)

        arcade.draw_text("SOKOBAN",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 200,
                         arcade.color.YELLOW, font_size = 50,
                         anchor_x = "center")
 
        arcade.draw_text("Use ←, →, ↑, ↓ to move player",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150,
                         arcade.color.BLACK, font_size = 25,
                         anchor_x = "center")
        arcade.draw_text("Use U to undo the step",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100,
                         arcade.color.BLACK, font_size = 25,
                         anchor_x = "center")
        arcade.draw_text("Use R to return to the original state",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.BLACK, font_size = 25,
                         anchor_x = "center")

        arcade.draw_text("Press SPACE key to start",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.BLUE, font_size = 20,
                         anchor_x = "center")


    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            game = LevelView()
            self.window.show_view(game)


class LevelView(arcade.View):
    def __init__(self, level_id = 0):
        super().__init__()

        self.level_id = level_id
        self.state = self.load_level(level_id)
        self.history = []
        self.time = datetime.now()
        self.steps = 0
        copy_state = copy.deepcopy(self.state)
        self.history.append(copy_state)
        arcade.set_background_color(arcade.color.GRAY)


    def load_level(self, level_id):
        level_file = open("levels/" + LEVELS[level_id])
        level = [[" "] * WIDTH for i in range(HEIGHT)]
        cnt = 0
        for l in level_file:
            line = l.rstrip("\n")
            for j in range(len(line)):
                level[cnt][j] = line[j]
            cnt += 1
        level_file.close()
        return level


    def sprite(self, cell, i, j):
        sprite = arcade.Sprite("sprites/" + SPRITES[cell], SPRITE_SCALING)
        sprite.center_x = j * SPRITE_SIZE + (SPRITE_SIZE // 2)
        sprite.center_y = (HEIGHT - 1 - i) * SPRITE_SIZE + (SPRITE_SIZE // 2)
        return sprite


    def on_draw(self):
        arcade.start_render()

        sprites = arcade.SpriteList()

        for i in range(HEIGHT):
            for j in range(WIDTH):
                cell = self.state[i][j]

                sprite = self.sprite(FLOOR, i, j)
                sprites.append(sprite)
                if cell == FLOOR:
                    continue
                elif cell == PLAYER_ON_TARGET:
                    sprite = self.sprite(TARGET, i, j)
                    sprites.append(sprite)
                    sprite = self.sprite(PLAYER, i, j)
                    sprites.append(sprite)
                    continue
                elif cell == BOX_ON_TARGET:
                    sprite = self.sprite(TARGET, i, j)
                    sprites.append(sprite)
                    sprite = self.sprite(BOX_ON_TARGET, i, j)
                    sprites.append(sprite)
                    continue
                else:
                    sprite = self.sprite(cell, i, j)
                    sprites.append(sprite)


        sprites.draw()

        if self.completed():
            arcade.finish_render()
            self.time = (datetime.now() - self.time).total_seconds()
            arcade.pause(1)
            view = LevelCompletedView(self.level_id, self.time, self.steps)
            self.window.show_view(view)


    def move(self, dx, dy):
        copy_state = copy.deepcopy(self.state)
        self.history.append(copy_state)
        self.steps += 1
        px, py = -1, -1
        for i in range(HEIGHT):
            for j in range(WIDTH):
                cell = self.state[i][j]
                if cell in [PLAYER, PLAYER_ON_TARGET]:
                    px, py = i, j

        cell_orig = FLOOR
        if self.state[px][py] == PLAYER_ON_TARGET:
            cell_orig = TARGET

        c1x, c1y = px + dx, py + dy
        if not inside(c1x, c1y):
            return
        cell1 = self.state[c1x][c1y]

        if cell1 == WALL:
            return

        if cell1 == FLOOR:
            self.state[px][py] = cell_orig
            self.state[c1x][c1y] = PLAYER
            return

        if cell1 == TARGET:
            self.state[px][py] = cell_orig
            self.state[c1x][c1y] = PLAYER_ON_TARGET
            return

        # ok, cell1 is either BOX or BOX_ON_TARGET (it can't be PLAYER or PLAYER_ON_TARGET)

        c2x, c2y = px + 2 * dx, py + 2 * dy
        if not inside(c2x, c2y):
            return
        cell2 = self.state[c2x][c2y]

        if cell2 in [WALL, BOX, BOX_ON_TARGET]:
            return

        # ok, cell2 is either FLOOR or TARGET (it can't be PLAYER or PLAYER_ON_TARGET)

        self.state[px][py] = cell_orig
        if cell1 == BOX:
            self.state[c1x][c1y] = PLAYER
        else:  # it is BOX_ON_TARGET
            self.state[c1x][c1y] = PLAYER_ON_TARGET
        if cell2 == FLOOR:
            self.state[c2x][c2y] = BOX
        else:  # it is TARGET
            self.state[c2x][c2y] = BOX_ON_TARGET


    def completed(self):
        for i in range(HEIGHT):
            for j in range(WIDTH):
                if self.state[i][j] == BOX:
                    return False
        return True


    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.move(-1, 0)
        elif key == arcade.key.DOWN:
            self.move(+1, 0)
        elif key == arcade.key.LEFT:
            self.move(0, -1)
        elif key == arcade.key.RIGHT:
            self.move(0, +1)
        elif key == arcade.key.U:
            if len(self.history) > 0:
                self.state = self.history.pop()
        elif key == arcade.key.R:
            if len(self.history) > 0:
                self.state = self.history[0]
                self.history = []

    def on_hide_view(self):
        print("level " + str(self.level_id) + " is hidden")


class LevelCompletedView(arcade.View):
    def __init__(self, level_id, time, steps):
        super().__init__()
        self.level_id = level_id
        self.time = time
        self.steps = steps
        self.background = arcade.load_texture("finish_bg.jpg") 
        arcade.set_background_color(arcade.color.WHITE)
        
    def on_draw(self):
        arcade.start_render()
        
        arcade.draw_lrwh_rectangle_textured(
            0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)
        
        arcade.draw_text("CONGRATULATIONS!",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.BLACK, font_size = 40,
                         anchor_x = "center")
        
        arcade.draw_text("LEVEL " + str(self.level_id + 1) + " FINISHED!",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.BLACK, font_size = 40,
                         anchor_x = "center")

        arcade.draw_text("Time:" + str(int(self.time) // 60) + ":" + str(int(self.time) % 60),
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50,
                         arcade.color.BLACK, font_size = 40,
                         anchor_x = "center")

        arcade.draw_text("Number of steps:" + str(self.steps),
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100,
                         arcade.color.BLACK, font_size = 40,
                         anchor_x = "center")

        arcade.draw_text("Press SPACE key to continue",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 150,
                         arcade.color.BLACK, font_size = 20,
                         anchor_x = "center")


    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            if self.level_id + 1 == len(LEVELS):
                view = GameCompletedView()
                self.window.show_view(view)
            else:
                game = LevelView(self.level_id + 1)
                self.window.show_view(game)


class GameCompletedView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background = arcade.load_texture("finish_game_bg.jpg")
        arcade.set_background_color(arcade.color.WHITE)
        

    def on_draw(self):
        arcade.start_render()
        
        arcade.draw_lrwh_rectangle_textured(
            0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)
        
        arcade.draw_text("CONGRATULATIONS!",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100,
                         arcade.color.RED, font_size = 25,
                         anchor_x = "center")

        arcade.draw_text("GAME FINISHED!",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 150,
                         arcade.color.RED, font_size = 25,
                         anchor_x = "center")

        arcade.draw_text("Press SPACE key to restart",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 200,
                         arcade.color.GRAY, font_size = 20,
                         anchor_x = "center")


    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            game = LevelView()
            self.window.show_view(game)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu = MenuView()
    window.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    main()

