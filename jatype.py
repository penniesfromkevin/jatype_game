#!/usr/bin/env python3
"""Terrible test program.
"""
import argparse
import os
import random
import sys

import pygame


IMAGE_PATH = 'images'

FRAME_RATE = 60
BOARD_WIDTH, BOARD_HEIGHT = BOARD_SIZE = 640, 480

SPEED_MIN = 1
SPEED_MAX = 6
SPEED_DEFAULT = 2
LIVES_MAX = 99
LIVES_DEFAULT = 3
HEALTH_DEFAULT = LIVES_DEFAULT

ENEMY_MAX = 16
ENEMIES = {
    'default': {
        'points': 50,
        'speed': 1,
        'deviation': 8,  # How far up and down an enemy "waves"
        'strength': 1,
        'bonuses': [],
        },
    'cargo': {
        'points': 100,
        'speed': 2,
        'deviation': 0,
        'strength': 2,  # some enemies are tougher than others...
        'bonuses': [
            'life',
            'weapon',
            ],
        },
    'manta': {
        'points': 150,
        'speed': 3,
        'deviation': 20,
        'strength': 1,
        'bonuses': [
            'point'
            ],
        },
    }
BONUSES = {
    'weapon': {
        'points': 50,
        'lives': 0,
        'weapons': 1,
        'speed': 1,
        },
    'life': {
        'points': 50,
        'lives': 1,
        'weapons': 0,
        'speed': 1,
        },
    'point': {
        'points': 500,
        'lives': 0,
        'weapons': 0,
        'speed': 2,
        },
    }
WEAPONS = {
    'default': {
        'cooldown': 20,
        'speed': 7,
        'count_max': 20,
        'strength': 1,
        },
    'fire': {
        'cooldown': 30,
        'speed': 6,
        'count_max': 10,
        'strength': 1,
        },
    'laser': {
        'cooldown': 6,
        'speed': 9,
        'count_max': 10,
        'strength': 2,  # some bullets can hit more than one target...
        },
    'power': {
        'cooldown': 40,
        'speed': 8,
        'count_max': 10,
        'strength': 3,
        },
    'safety': {
        'cooldown': 10,
        'speed': 7,
        'count_max': 10,
        'strength': 1,
        },
    }


class ImageStore():
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
        return image

    def add(self, name):
        """Add image object to the store.

        Args:
            name: Name of image to add.

        Returns:
            Image object, or None if object could not be loaded.
        """
        image_path = os.path.join(self._path, '%s.%s' % (name, self._ext))
        image_object = pygame.image.load(image_path).convert_alpha()
        self._store[name] = image_object
        return image_object


class Character(pygame.sprite.Sprite):
    """All controllable things.
    """
    def __init__(self, kind, name, x_pos=0, y_pos=0, speed=SPEED_DEFAULT):
        """Initialize character.

        Args:
            kind: Type of character (bullet, enemy, etc)
            name: Specific name of character.
            x_pos: X coordinate of character.
            y_pos: Y coordinate of character.
        """
        super().__init__()
        self.kind = kind
        self.name = name
        self.speed = speed

        self.image = IMAGES.get('%s/%s' % (kind, name))
        self.width, self.height = self.image.get_size()

        # Fetch the rectangle object that has the dimensions of the image
        self.rect = self.image.get_rect()
        self.rect.x = self.x_pos = x_pos
        self.rect.y = self.y_pos = y_pos
        self.x_inc = self.y_inc = 0

    def display(self):
        """Draw the character image on the game board.
        """
        BOARD.blit(self.image, (self.x_pos, self.y_pos))

    def update(self):
        """Update sprite.
        """
        self.x_pos += self.x_inc
        self.y_pos += self.y_inc
        self.rect.x = self.x_pos
        self.rect.y = self.y_pos
        self.display()


class Player(Character):
    """Player class.
    """
    def __init__(self, name='default', x_pos=0, y_pos=0):
        """Initialize player.

        Args:
            name:
            x_pos:
            y_pos:
        """
        super().__init__('player', name, x_pos, y_pos)
        self.weapons = {}  # dictionary of weapons, and how many of each
        self.weapon_index = 0
        self.weapon = None
        self.cooldown = None
        self.cooldown_left = 0
        self.invulnerability = 0  # Player is invulnerable when starting out
        self.reset(weapons=True, position=True)

        self.image_orig = self.image  # invulnerability makes player blink
        self.image_alt = pygame.transform.laplacian(self.image)

        self.lives = LIVES_DEFAULT
        self.score = 0
        self.bullets = pygame.sprite.Group()


    def get_input(self):
        """Get input from the user (keyboard)
        """
        game_over = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_over = True
                elif event.key == pygame.K_p:
                    pause_game()
                elif event.key == pygame.K_x:
                    if self.speed < SPEED_MAX:
                        self.speed += 1
                elif event.key == pygame.K_z:
                    if self.speed > SPEED_MIN:
                        self.speed -= 1
                elif event.key == pygame.K_c:
                    self.equip(increment=True)
                elif event.key == pygame.K_UP:
                    self.y_inc = -self.speed
                elif event.key == pygame.K_DOWN:
                    self.y_inc = self.speed
                elif event.key == pygame.K_LEFT:
                    self.x_inc = -self.speed
                elif event.key == pygame.K_RIGHT:
                    self.x_inc = self.speed
                elif event.key == pygame.K_SPACE:  # shoot weapon
                    self.shoot()

                # Cheats
                elif event.key == pygame.K_1:
                    self.weapons[self.weapon] = 8

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_RIGHT, pygame.K_LEFT):
                    self.x_inc = 0
                elif event.key in (pygame.K_UP, pygame.K_DOWN):
                    self.y_inc = 0
        return game_over

    def reset(self, weapons=False, position=False):
        """Reset position and make invulnerable for a bit.
        """
        self.invulnerability = FRAME_RATE * 5
        if position:
            self.x_pos = BOARD_WIDTH // 2
            self.y_pos = BOARD_HEIGHT // 2
        if weapons:
            self.weapons = {'default': 1}
            self.weapon_index = 0
            self.equip()

    def equip(self, increment=False):
        """equip weapons

        Args:
            increment: Equip the next weapon in the list.
        """
        if increment:
            self.weapon_index += 1
        if self.weapon_index >= len(self.weapons):
            self.weapon_index = 0
        self.weapon = sorted(self.weapons.keys())[self.weapon_index]
        self.cooldown = WEAPONS[self.weapon]['cooldown']
        self.cooldown_left = 0

    def shoot(self):
        """Shoot weapon.
        """
        if (self.cooldown_left < 1 and
                len(self.bullets) < WEAPONS[self.weapon]['count_max']):
            speed = WEAPONS[self.weapon]['speed']
            directions = (
                (speed, 0),
                (speed, speed // 2 or 1),
                (speed, -speed // 2 or -1),
                (0, speed),
                (0, -speed),
                (-speed, 0),
                (-speed, speed // 2 or 1),
                (-speed, -speed // 2 or -1),
                )
            guns = self.weapons[self.weapon]
            for x_inc, y_inc in directions[:guns]:
                bullet = Bullet(self.weapon, self.x_pos, self.y_pos,
                                x_inc=x_inc, y_inc=y_inc)
                bullet.strength = WEAPONS[self.weapon]['strength']
                self.bullets.add(bullet)
            self.cooldown_left += self.cooldown

    def update(self):
        """Update Player.
        """
        if self.lives > LIVES_MAX:
            self.lives = LIVES_MAX
        self.cooldown_left -= 1
        if self.x_pos < 0:
            self.x_pos = 0
        elif self.x_pos > BOARD_WIDTH - self.width:
            self.x_pos = BOARD_WIDTH - self.width
        if self.y_pos < 0:
            self.y_pos = 0
        elif self.y_pos > BOARD_HEIGHT - self.height:
            self.y_pos = BOARD_HEIGHT - self.height
        if self.invulnerability > 0:
            self.invulnerability -= 1
            if self.invulnerability > FRAME_RATE * 3:
                mod, remain = 10, 5
            elif self.invulnerability > FRAME_RATE * 2:
                mod, remain = 5, 3
            else:
                mod, remain = 2, 1
            if self.invulnerability % mod > remain:
                self.image = self.image_alt
            else:
                self.image = self.image_orig
        super().update()
        self.bullets.update()
        useless = [bullet for bullet in self.bullets
                   if bullet.x_pos > BOARD_WIDTH
                   or bullet.x_pos < -bullet.width
                   or bullet.y_pos > BOARD_HEIGHT
                   or bullet.y_pos < -bullet.height]
        for bullet in useless:
            self.bullets.remove(bullet)


class Bullet(Character):
    """Bullet class.
    """
    def __init__(self, name, x_pos, y_pos, x_inc, y_inc):
        """Initialize bullets.
        """
        super().__init__('bullet', name, x_pos, y_pos, 0)
        self.strength = WEAPONS[self.name]['strength']
        self.x_inc = x_inc
        self.y_inc = y_inc


class Enemy(Character):
    """Enemy class.
    """
    def __init__(self, name=None):
        """Initialize enemy.

        Args:
            name: Enemy name; if None, random from ENEMIES
            x_pos:
            y_pos:
        """
        if not name:
            names = list(ENEMIES.keys())
            name = random.choice(names)
        speed = ENEMIES[name]['speed']
        super().__init__('enemy', name, x_pos=0, y_pos=0, speed=speed)
        self.points = ENEMIES[name]['points']
        self.x_inc = -self.speed
        self.direction = random.choice(['up', 'down'])
        self.deviation = ENEMIES[name]['deviation']
        self.strength = ENEMIES[name]['strength']
        self.bonuses = ENEMIES[name]['bonuses']
        self.reset()
        self.y_initial = self.y_pos

    def reset(self):
        """Reset position to randomly off the right side of the screen.
        """
        self.x_pos = random.randint(BOARD_WIDTH, BOARD_WIDTH * 2)
        self.y_pos = self.y_initial = random.randint(0, BOARD_HEIGHT)

    def update(self):
        if self.deviation:
            ## Enemy will wave up and down
            if self.direction == 'up':
                self.y_inc = -self.speed
                if self.y_pos <= self.y_initial - self.deviation:
                    self.direction = 'down'
            else:
                self.y_inc = self.speed
                if self.y_pos >= self.y_initial + self.deviation:
                    self.direction = 'up'
        #else:
        #    ## Else it is 'default' behavior: head toward player
        #    if player.x_pos < self.x_pos:
        #        self.x_pos -= self.speed

        #    if player.y_pos < self.y_pos:
        #        self.y_pos -= self.speed
        #    else:
        #        self.y_pos += self.speed

        super().update()
        if self.x_pos < -self.width:
            self.reset()


class Bonus(Character):
    """Bonus class.
    """
    def __init__(self, name=None, x_pos=0, y_pos=0):
        """Initialize bonus.
        """
        if not name:
            names = list(BONUSES.keys())
            name = random.choice(names)
        speed = BONUSES[name]['speed']
        super().__init__('bonus', name, x_pos, y_pos, speed)
        self.x_inc = random.randint(-self.speed, self.speed)
        self.y_inc = random.randint(-self.speed, self.speed)
        if name == 'weapon':
            weapons = list(WEAPONS.keys())
            self.weapon = random.choice(weapons)
        else:
            self.weapon = None
        self.points = BONUSES[name]['points']
        self.lives = BONUSES[name]['lives']


class Background():
    """Backgrounds.  Yes, plural.
    """
    def __init__(self, levels, x_inc=0, y_inc=0):
        """Initialize scrolling background object.

        Args:
            levels: A single background name, or list of backgrounds.
        """
        if not isinstance(levels, (list, tuple)):
            levels = [levels]
        self.levels = []
        for incr, level in enumerate(levels):
            background = Character('background', level, 0, 0)
            background.display()
            background.x_inc = x_inc + int(x_inc * (incr + 1) / len(levels))
            background.y_inc = y_inc + int(y_inc * (incr + 1) / len(levels))
            self.levels.append(background)

    def update(self):
        """Update backgrounds.
        """
        for level in self.levels:
            level.update()
            if level.x_pos <= -level.width or level.x_pos >= level.width:
                level.x_pos = 0
            if level.y_pos <= -level.height or level.y_pos >= level.height:
                level.y_pos = 0

            if level.x_inc:
                BOARD.blit(
                    level.image,
                    (
                        level.x_pos - cmp(level.x_inc, 0) * level.width,
                        level.y_pos
                        )
                    )
            if level.y_inc:
                BOARD.blit(
                    level.image,
                    (
                        level.x_pos,
                        level.y_pos - cmp(level.y_inc, 0) * level.height
                        )
                    )
                # If movement is diagonal, a fourth copy is required
                if level.x_inc:
                    BOARD.blit(
                        level.image,
                        (
                            level.x_pos - cmp(level.x_inc, 0) * level.width,
                            level.y_pos - cmp(level.y_inc, 0) * level.height
                            )
                        )


def parse_args():
    """Parse user arguments and return as parser object.

    Returns:
        Parser object with arguments as attributes.
    """
    parser = argparse.ArgumentParser(description='Test basic functionality.')
    parser.add_argument('-i', '--infinite', action='store_true',
                        help='Enable infinite mode (no deaths).')
    args = parser.parse_args()
    return args


def cmp(one, two):
    """Re-implementing removed cmp() function.
    """
    if one > two:
        result = 1
    elif one < two:
        result = -1
    else:
        result = 0
    return result


def show_stats(lives, score, weapons):
    """Show stats
    """
    weapon_stat = ''
    for weapon in sorted(weapons):
        weapon_stat += weapon[0]  # Just show first letter of each weapon
    stats = GAME_FONT.render(
        'Lives: %d  Score: %06d  Weapons: %s' % (lives, score, weapon_stat),
        True, (0, 0, 0), (255, 255, 255))
    BOARD.blit(stats, (0, 0))


def show_text(text, timer=-1, size=48, color=(255, 255, 0), py_key='any'):
    """Display text on screen for a given amount of time
    """
    text_pic = GAME_FONT.render(text, 1, color)
    # Center the input text (single line)
    half_size = (len(text) / 2) * (size / 3)
    # Position the text (single line) in the center of the screen
    text_position = ((BOARD_WIDTH / 2) - half_size, BOARD_HEIGHT / 2)
    BOARD.blit(text_pic, text_position)
    pygame.display.flip()
    wait_for_keypress(py_key, timer)


def wait_for_keypress(py_key='any', timer=-1):
    """Waits for a keypress.

    Args:
        py_key: Pygame constant keyboard key referemce.
        timer: Amount of time to wait, in seconds.  -1 is infinite.
    """
    pygame.event.clear()
    while timer != 0:
        pygame.time.wait(1000)
        CLOCK.tick(10)
        if timer > 0:
            timer -= 1
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if py_key in ('any', event.key):
                    timer = 0


def pause_game():
    """Pause the game until the pause key is pressed again.
    """
    show_text('Paused', py_key=pygame.K_p)


def main():
    """The game itself.
    """
    exit_code = 0
    # To play music, simply select and play
    #pygame.mixer.music.load('Track1.mp3')
    #pygame.mixer.music.play()
    background = Background(('far', 'near'), x_inc=-2, y_inc=-1)
    enemies = pygame.sprite.Group()
    bonuses = pygame.sprite.Group()
    player = Player()

    game_over = False
    while not game_over:
        BOARD.fill((10, 0, 15))
        # blit the backdrops first
        background.update()
        show_stats(player.lives, player.score, player.weapons.keys())

        game_over = player.get_input()
        player.update()

        # Add enemies
        if len(enemies) < ENEMY_MAX:
            enemy = Enemy()
            enemies.add(enemy)
        enemies.update()

        # bonuses disappear when they float off screen.
        useless = [bonus for bonus in bonuses if bonus.x_pos > BOARD_WIDTH
                   or bonus.x_pos < -bonus.width or bonus.y_pos > BOARD_HEIGHT
                   or bonus.y_pos < -bonus.height]
        for buff in useless:
            bonuses.remove(buff)
        bonuses.update()

        # Check if player crashed into an enemy (enemy is always destroyed)
        if not player.invulnerability:
            collisions = pygame.sprite.spritecollide(player, enemies, True)
            for collision in collisions:
                player.score -= collision.points
                player.weapons[player.weapon] -= 1
                if player.weapons[player.weapon] < 1:
                    player.weapons.pop(player.weapon, None)
                    player.weapon_index = 0
                if not player.weapons:
                    player.lives -= 1
                    player.reset(weapons=True)
                player.equip()

        # player shoots an enemy
        hits = pygame.sprite.groupcollide(enemies, player.bullets,
                                          False, False)
        bits = []
        for enemy in hits:
            damage = 0
            for bit in hits[enemy]:
                damage += bit.strength
                if bit not in bits:
                    bits.append(bit)
            enemy.strength -= damage
            if enemy.strength < 1:
                player.score += enemy.points
                if enemy.bonuses:
                    name = random.choice(enemy.bonuses)
                    bonus = Bonus(name, x_pos=enemy.x_pos, y_pos=enemy.y_pos)
                    bonuses.add(bonus)
                enemies.remove(enemy)
        # bullet is not always destroyed
        for bit in bits:  # some bullets are stronger than others...
            bit.strength -= 1
            if bit.strength < 1:
                player.bullets.remove(bit)

        # player touches a bonus
        buffs = pygame.sprite.spritecollide(player, bonuses, True)
        for buff in buffs:
            player.score += buff.points
            player.lives += buff.lives
            if buff.weapon:
                if buff.weapon not in player.weapons:
                    player.weapons[buff.weapon] = 1
                elif player.weapons[buff.weapon] < 8:
                    player.weapons[buff.weapon] += 1

        # Player shoots a bonus
        hits = pygame.sprite.groupcollide(player.bullets, bonuses,
                                          False, False)
        bits = []
        for bullet in hits:
            if bullet.name != 'safety':  # safety bullets do not kill bonuses
                bullet.strength -= 1
                for bit in hits[bullet]:
                    if bit not in bits:
                        bits.append(bit)
            if bullet.strength < 1:
                player.bullets.remove(bullet)
        for bonus in bits:
            bonuses.remove(bonus)
            player.score += bonus.points // 2  # player still get half points

        if player.lives <= 0:
            if ARGS.infinite:
                player.lives = 1
            else:
                game_over = True

        CLOCK.tick(FRAME_RATE)
        pygame.display.flip()

    return exit_code


if __name__ == '__main__':
    ARGS = parse_args()
    pygame.init()
    BOARD = pygame.display.set_mode(BOARD_SIZE)
    CLOCK = pygame.time.Clock()
    GAME_FONT = pygame.font.Font(None, 20)
    IMAGES = ImageStore(os.path.join(sys.path[0], IMAGE_PATH), 'png')

    EXIT_CODE = main()
    show_text('Good-bye!', 2)
    pygame.quit()
    sys.exit(EXIT_CODE)
