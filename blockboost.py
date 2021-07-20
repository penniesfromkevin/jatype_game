#!/usr/bin/env python3
"""A dashing game, without geometry.
"""
__author__ = 'Kevin'

import argparse
import logging
import os
import random
import sys

import pygame


FRAME_RATE = 30
BOARD_WIDTH, BOARD_HEIGHT = BOARD_SIZE = 640, 480
DEFAULT_SPEED = 10
DEFAULT_ENEMIES = 10
INCREASE_TIME = 5
DEFAULT_INCREMENT = 20
GOAL_X = 300

SECTION_MIN = 4
DIAMETER_MIN = 6
DIAMETER_MAX = 14

LOG_LEVELS = ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG')
DEFAULT_LOG_LEVEL = LOG_LEVELS[3]
LOGGER = logging.getLogger()


class ImageStore(object):
    """Image store.
    """
    def __init__(self, path, ext='png'):
        """Initialize the store.
        Args:
            path: Path to image files.
            ext: File extension image files.
        """
        self._store = {}
        self._path = path
        self._ext = ext

    def get(self, name):
        """Get image object.
        If the image does not exist in the store, this will also try to
        add it first, but it is better to pre-add images as there is
        less delay.
        Args:
            name: Name of image to get.
        Returns:
            Image object, or None if object could not be found.
        """
        if name in self._store:
            image = self._store[name]
        else:
            image = self.add(name)
        LOGGER.debug(self._store)
        return image

    def add(self, name):
        """Add image object to the store.
        Args:
            name: Name of image to add.
        Returns:
            Image object, or None if object could not be loaded.
        """
        image_path = os.path.join(self._path, '%s.%s' % (name, self._ext))
        try:
            image_object = pygame.image.load(image_path).convert_alpha()
        except pygame.error:
            LOGGER.error('Could not load image %s', image_path)
            #font = pygame.font.Font(None, 48)
            #image_object = font.render('X', True, (255, 0, 0))
            image_object = None
        self._store[name] = image_object
        return image_object


class Character(pygame.sprite.Sprite):
    """All controllable things.
    """
    def __init__(self, kind, board, x_pos=0, y_pos=0):
        """Initialize character.
        """
        #super(Character, self).__init__()
        pygame.sprite.Sprite.__init__(self)

        self.kind = kind
        self.board = board
        self.speed = DEFAULT_SPEED

        self.image = IMAGES.get(kind)
        self.width, self.height = self.image.get_size()

        # Fetch the rectangle object that has the dimensions of the image
        # Update position by setting the values of rect.x and rect.y
        self.rect = self.image.get_rect()

        self.rect.x = self.x_pos = x_pos
        self.rect.y = self.y_pos = y_pos

        self.speed_x = 0
        self.speed_y = 0

    def display(self, x_pos=None, y_pos=None):
        """Display the character.
        """
        if x_pos is None:
            x_pos = self.x_pos
        if y_pos is None:
            y_pos = self.y_pos
        self.board.blit(self.image, (x_pos, y_pos))

    def update(self):
        """Update sprite.
        """
        self.x_pos += self.speed_x
        self.y_pos += self.speed_y
        self.rect.x = self.x_pos
        self.rect.y = self.y_pos
        #self.display()


class Enemy(Character):
    """All user-controllable things.
    """
    def __init__(self, kind, board):
        """Initialize Enemy.
        Args:
            kind: image type to use.
            board: PyGame display surface.
        """
        board_x, board_y = board.get_size()
        x_pos = random.randint(0, board_x) + board_x
        image = 'enemy/%s' % kind
        super(Enemy, self).__init__(image, board, x_pos)
        self.speed = random.randint(2, DEFAULT_SPEED * 2)
        self.speed_x = -self.speed
        y_max = board_y - self.height
        self.y_pos = random.randint(0, y_max)


class Player(Character):
    """All user-controllable things.
    """
    def __init__(self, kind, board, x_pos=0, y_pos=0):
        """Initialize Player.
        """
        image = 'player/%s' % kind
        super(Player, self).__init__(image, board, x_pos, y_pos)
        self.speed_y = DEFAULT_SPEED #self.speed
        self.mirror = False
        self.guided = False

    def get_input(self):
        """Get user input.
        Returns:
            String: 'quit', 'pause', or '' (empty string)
        """
        return_value = ''
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ## Did the user click the 'close' icon on the game window?
                return_value = 'quit'
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return_value = 'quit'
                elif event.key == pygame.K_p:
                    return_value = 'pause'

                elif event.key == pygame.K_SPACE:
                    self.speed_y = -self.speed

                elif event.key == pygame.K_e:
                    ARGS.enemies = not ARGS.enemies
                elif event.key == pygame.K_t:
                    ARGS.tube = not ARGS.tube
                elif event.key == pygame.K_i:
                    ARGS.infinite = not ARGS.infinite

                elif event.key == pygame.K_m:
                    self.mirror = not self.mirror
                elif event.key == pygame.K_g:
                    self.guided = not self.guided
                elif event.key == pygame.K_0:
                    self.speed_y = 0
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_SPACE,):
                    self.speed_y = self.speed
        return return_value

    def update(self):
        """Update player.
        """
        if self.x_pos + self.speed_x > BOARD_WIDTH - self.width:
            self.x_pos = BOARD_WIDTH - self.width
            self.speed_x = 0
        elif self.x_pos + self.speed_x < 0:
            self.x_pos = 0
            self.speed_x = 0
        if self.y_pos + self.speed_y > BOARD_HEIGHT - self.height:
            self.y_pos = BOARD_HEIGHT - self.height - self.speed_y
        elif self.y_pos + self.speed_y < 0:
            self.y_pos = self.speed
        super(Player, self).update()
        if self.mirror:
            half_board = self.board.get_height() / 2
            mirror_y = half_board - (self.y_pos - half_board) - self.height
            self.display(y_pos=mirror_y)


class Block(Character):
    """Block.
    """
    def __init__(self, kind, board, x_pos=0, y_pos=0, speed=0):
        """Put a block on a grid.
        Args:
            kind: image type to use.
            board: PyGame display surface.
            x_pos: X location.
            y_pos: Y location.
        """
        image = 'block/%s' % kind
        super(Block, self).__init__(image, board, x_pos, y_pos)
        self.speed_x = speed


class BlockTube(object):
    """The tube that serves as the game track.
    """
    def __init__(self, kind, board, speed=0):
        """Set up how the tube 'moves'.
        """
        self.blocks_top = pygame.sprite.Group()
        self.blocks_bottom = pygame.sprite.Group()

        self.board = board
        self.board_width, self.board_height = self.board.get_size()

        self.kind = kind
        block = Block(self.kind, self.board, self.board_width)
        self.block_width = block.width
        self.block_height = block.height

        self.grid_width = self.board_width // self.block_width
        self.grid_height = (self.board_height // self.block_height)

        self.diameter = DIAMETER_MAX
        self.grid_x = self.grid_width
        self.grid_y = self.get_grid_y_max()

        self._section_length = SECTION_MIN
        self._speed = speed
        self._x_pos, _ = self.grid_to_display(self.grid_width, 0)
        self._delta_y = 0

    def get_grid_y_max(self):
        """Get maximum grid Y for a given specification.
        """
        grid_y_max = self.grid_height - self.diameter - 2
        return grid_y_max

    def get_y_at_x(self, x_pos):
        """Gets the y_position of the tube at a given x-position.
        Args:
            x_pos: X-position for which to get the y-position.
        Returns:
            Y-position, as display coordinate.
        """
        tube_y = None
        for block in self.blocks_top:
            if x_pos >= block.x_pos and x_pos <= block.x_pos + block.width:
                tube_y = block.y_pos + block.height
        return tube_y

    def grid_to_display(self, grid_x, grid_y):
        """Converts from grid-coordinates to display coordinates.
        Args:
            grid_x: X location on grid.
            grid_y: Y location on grid.
        Returns:
            Tuple: (display_x, display_y)
        """
        x_pos = int(grid_x * self.block_width)
        y_pos = int(grid_y * self.block_height)
        return x_pos, y_pos

    def add_section(self):
        """Adds a one-block section of the tube.
        Args:
            kind: Image type to use for the section.
        """
        x_pos, y_pos = self.grid_to_display(self.grid_width, self.grid_y)
        new_block = Block(self.kind, self.board, x_pos, y_pos, self._speed)
        self.blocks_top.add(new_block)
        grid_y_side = int(self.grid_y + self.diameter + 1)
        x_end, y_end = self.grid_to_display(self.grid_width, grid_y_side)
        new_block = Block(self.kind, self.board, x_end, y_end, self._speed)
        self.blocks_bottom.add(new_block)

    def update(self):
        """Update tube movement.
        """
        self._x_pos += self._speed
        if self._x_pos < self.board_width - self.block_width:
            self._x_pos += self.block_width
            if self._section_length:
                self._section_length -= 1
                if self._delta_y:
                    grid_y = self.grid_y + self._delta_y
                    grid_y_max = self.get_grid_y_max()
                    if grid_y < 0:
                        grid_y = 0
                    elif grid_y > grid_y_max:
                        grid_y = grid_y_max
                    self.grid_y = grid_y
                else:
                    # only change diameter if Y has not changed
                    delta_d = random.choice([-1, 0, 1])
                    diameter = self.diameter + delta_d
                    if diameter < DIAMETER_MIN:
                        diameter = DIAMETER_MIN
                    elif diameter > DIAMETER_MAX:
                        diameter = DIAMETER_MAX
                    if self.grid_y + diameter + 2 <= self.grid_height:
                        self.diameter = diameter
            else:
                self._section_length = SECTION_MIN
                self._delta_y = random.choice([-1, -1, 0, 1, 1])
            self.add_section()

        for block_group in (self.blocks_top, self.blocks_bottom):
            block_group.update()
            for block in block_group:
                if block.x_pos < -self.block_width:
                    block_group.remove(block)


class Background(object):
    """Backgrounds.  Yes, plural.
    """
    def __init__(self, layers, board, speed_x=0, speed_y=0):
        """Initialize scrolling background object.
        Args:
            layers: A list of background names.
        """
        self.board = board
        if not isinstance(layers, (list, tuple)):
            layers = [layers]
        self.layers = pygame.sprite.Group()
        for incr, layer_name in enumerate(layers):
            image = 'background/%s' % layer_name
            layer = Character(image, self.board, 0, 0)
            layer.speed_x = speed_x + int(speed_x * (incr + 1) / len(layers))
            layer.speed_y = speed_y + int(speed_y * (incr + 1) / len(layers))
            LOGGER.debug('x: %d, y: %d', layer.speed_x, layer.speed_y)
            self.layers.add(layer)

    def update(self):
        """Update backgrounds.
        """
        for layer in self.layers:
            if layer.x_pos <= -layer.width or layer.x_pos >= layer.width:
                layer.x_pos = 0
            if layer.y_pos <= -layer.height or layer.y_pos >= layer.height:
                layer.y_pos = 0

            if layer.speed_x:
                self.board.blit(layer.image,
                        (layer.x_pos - cmp(layer.speed_x, 0) * layer.width,
                         layer.y_pos))
            if layer.speed_y:
                self.board.blit(layer.image,
                        (layer.x_pos,
                         layer.y_pos - cmp(layer.speed_y, 0) * layer.height))
                # If movement is diagonal, a fourth copy is required
                if layer.speed_x:
                    self.board.blit(layer.image,
                            (layer.x_pos - cmp(layer.speed_x, 0) * layer.width,
                            layer.y_pos - cmp(layer.speed_y, 0) * layer.height))
        self.layers.update()
        self.layers.draw(self.board)


def cmp(x, y):
    if x < y:
        result = -1
    elif x > y:
        result = 1
    else:
        result = 0
    return result


def parse_args():
    """Parse user arguments and return as parser object.
    Returns:
        Parser object with arguments as attributes.
    """
    parser = argparse.ArgumentParser(
            description='Test basic functionality.')
    parser.add_argument('-e', '--enemies', action='store_true',
            help='Enable enemies.')
    parser.add_argument('-t', '--tube', action='store_true',
            help='Enable tube.')
    parser.add_argument('-i', '--infinite', action='store_true',
            help='Enable infinite mode (no dying).')

    parser.add_argument('-L', '--loglevel', choices=LOG_LEVELS,
            default=DEFAULT_LOG_LEVEL, help='Set the logging level.')
    args = parser.parse_args()
    return args


def pause_game(pause=500):
    """Pause the game.
    Args:
        pause: Time, in milliseconds.
    """
    paused = True
    while paused:
        pygame.time.delay(pause)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = False


def main():
    """Main script.
    """
    exit_code = 0
    #To play music, simply select and play
    #pygame.mixer.music.load('Track1.mp3')
    #pygame.mixer.music.play()

    backdrop = Background(('far', 'near'), BOARD, -4)
    y_half = BOARD_HEIGHT / 2
    player = Player('default', BOARD, DEFAULT_INCREMENT * 5, y_half)

    increase_counter = 0
    enemy_count = DEFAULT_ENEMIES
    enemies = pygame.sprite.Group()

    tube = BlockTube('sprite', BOARD, -DEFAULT_SPEED)

    game_over = False
    while not game_over:
        BOARD.fill((10, 0, 15))
        backdrop.update()

        intent = player.get_input()
        player.update()
        if player.guided and ARGS.tube:
            tube_y = tube.get_y_at_x(player.x_pos + player.width)
            if tube_y:
                player.y_pos = tube_y + tube.block_height * 3
        player.display()

        if ARGS.enemies:
            if len(enemies) < enemy_count:
                new_enemy = Enemy('manta', BOARD)
                enemies.add(new_enemy)

            enemies_gone = [enemy for enemy in enemies
                            if enemy.x_pos < -enemy.width]
            enemies.remove(enemies_gone)
            enemies.update()
            enemies.draw(BOARD)

            collisions = pygame.sprite.spritecollide(player, enemies, True)
            if collisions:
                LOGGER.info('Gack!')
                player.x_pos -= DEFAULT_INCREMENT // 2
                increase_counter = 0

        if ARGS.tube:
            tube.update()
            collisions = pygame.sprite.spritecollide(player, tube.blocks_top,
                                                     False)
            if collisions:
                player.y_pos += collisions[0].height
            else:
                collisions = pygame.sprite.spritecollide(
                    player, tube.blocks_bottom, False)
                if collisions:
                    player.y_pos -= collisions[0].height
            if collisions:
                LOGGER.info('Ouch')
                player.x_pos -= DEFAULT_INCREMENT // 3
                increase_counter = 0
            tube.blocks_top.draw(BOARD)
            tube.blocks_bottom.draw(BOARD)

        increase_counter += 1
        if increase_counter > INCREASE_TIME * FRAME_RATE:
            increase_counter = 0
            player.x_pos += DEFAULT_INCREMENT
            enemy_count += 1

        if intent == 'quit':
            game_over = True
        elif intent == 'pause':
            pause_game()
        if player.x_pos < 0 and not ARGS.infinite:
            game_over = True
        elif player.x_pos >= GOAL_X:
            LOGGER.info('OMG, you did it...')
            game_over = True

        CLOCK.tick(FRAME_RATE)
        pygame.display.flip()

    return exit_code


if __name__ == '__main__':
    ARGS = parse_args()
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        level=getattr(logging, ARGS.loglevel))

    pygame.init()
    BOARD = pygame.display.set_mode(BOARD_SIZE)
    CLOCK = pygame.time.Clock()
    IMAGES = ImageStore(os.path.join(sys.path[0], 'images'), 'png')

    exit_code = main()

    pygame.quit()
    sys.exit(exit_code)
