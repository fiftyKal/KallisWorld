import math
import random
import os
import arcade

# arcade.examples.sprite_bullets_aimed
# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Kalli's World"

# Constants used to scale our sprites from their original size
TILE_SCALING = 0.5
CHARACTER_SCALING = TILE_SCALING * 2
COIN_SCALING = TILE_SCALING
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

# Constants for meteors
METEOR_SCALING = 0.5
METEOR_COUNT = 20

# Constants for bullets
SPRITE_SCALING_LASER = 1
BULLET_SPEED = 5

# Movement speed of player, in pixels per frame
PLAYER_MOVEMENT_SPEED = 10
GRAVITY = 1
PLAYER_JUMP_SPEED = 20

# Player starting position
PLAYER_START_X = 64
PLAYER_START_Y = 225

# Layer Names from our TileMap
LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_COINS = "Coins"
LAYER_NAME_FOREGROUND = "Foreground"
LAYER_NAME_BACKGROUND = "Background"
LAYER_NAME_DONT_TOUCH = "Don't Touch"


class InstructionView(arcade.View):
    def on_show_view(self):
        arcade.set_background_color(arcade.color.LIGHT_BLUE)

    def on_draw(self):
        self.clear()
        arcade.draw_text(" Welcome to Kalli's World", SCREEN_WIDTH / 2,
                         SCREEN_HEIGHT / 1.5,
                         arcade.color.DARK_BLUE, font_size=50, anchor_x="center")
        arcade.draw_text(" Use the LEFT and RIGHT arrow keys to MOVE", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.DARK_BLUE, font_size=20, anchor_x="center")
        arcade.draw_text(" Use the UP arrow to JUMP", SCREEN_WIDTH / 2,
                         SCREEN_HEIGHT / 2.5,
                         arcade.color.DARK_BLUE, font_size=20, anchor_x="center")
        arcade.draw_text("left click mouse to shoot meteors", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3,
                         arcade.color.DARK_BLUE, font_size=20, anchor_x="center")

        arcade.draw_text("Click to advance", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4,
                         arcade.color.DARK_GREEN, font_size=20, anchor_x="center")

    def on_mouse_press(self, x, y, button, modifiers):
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)


class GameView(arcade.View):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__()

        # Our TileMap Object
        self.tile_map = None

        self.player_collision_list = None

        self.width = 1000

        # Our Scene Object
        self.scene = None

        # variables that will hold sprite lists
        self.player_list = None
        self.bullet_list = None
        self.meteor_list = None
        self.enemy_list = None

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Creating variable for enemy sprite
        self.enemy = None

        # Our physics engine
        self.physics_engine = None

        # A Camera that can be used for scrolling the screen
        self.camera = None

        # A Camera that can be used to draw GUI elements
        self.gui_camera = None

        # Keep track of the score
        self.score = 0

        # Do we need to reset the score?

        self.reset_score = True

        # Where is the right edge of the map?

        self.end_of_map = 0

        # Level
        self.level = 1

        # sounds sounds from kenney.nl
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")
        self.game_over = arcade.load_sound(":resources:sounds/gameover1.wav")
        self.hit_sound = arcade.sound.load_sound(":resources:sounds/laser1.wav")

        arcade.set_background_color(arcade.color.PINK_SHERBET)

    def setup(self):
        """Set up the game here. Call this function to restart the game."""
        # sprite lists
        self.player_list = arcade.SpriteList()
        self.meteor_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()

        # Set up the Cameras
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.score = 0

        # Keep track of the score, make sure we keep the score if the player finishes a level
        if self.reset_score:
            self.score = 0
        self.reset_score = True

        # Map name
        map_name = f":resources:tiled_maps/map2_level_{self.level}.json"

        # Layer Specific Options for the Tilemap
        layer_options = {
            LAYER_NAME_PLATFORMS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_COINS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_DONT_TOUCH: {
                "use_spatial_hash": True,
            },
        }

        # Load in TileMap
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)

        # Initiate New Scene with our TileMap, this will automatically add all layers
        # from the map as SpriteLists in the scene in the proper order.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Add Player Sprite list before "Foreground" layer.
        self.scene.add_sprite_list_after("Player", LAYER_NAME_FOREGROUND)

        # Set up the player, specifically placing it at these coordinates.
        image_source = ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png"
        self.player_sprite = arcade.Sprite(image_source, CHARACTER_SCALING)
        self.player_sprite.center_x = PLAYER_START_X

        self.player_sprite.center_y = PLAYER_START_Y
        self.scene.add_sprite("Player", self.player_sprite)

        # Calculate the right edge of the my_map in pixels
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE

        # Use a loop to place some coins for our character to pick up
        for x in range(300, 2000, 258):
            coin = arcade.Sprite(":resources:images/items/coinGold.png", COIN_SCALING)
            coin.center_x = x
            coin.center_y = 215
            self.scene.add_sprite("Coins", coin)

        for i in range(METEOR_COUNT):
            meteor = arcade.Sprite(":resources:images/space_shooter/meteorGrey_med1.png", METEOR_SCALING)

            meteor.center_x = random.randrange(SCREEN_WIDTH)
            meteor.center_y = random.randrange(120, SCREEN_HEIGHT)

            self.meteor_list.append(meteor)

        # --- Other stuff
        # Set the background color
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        # Create the 'physics engine'
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            gravity_constant=GRAVITY,
            walls=self.scene[LAYER_NAME_PLATFORMS],
        )

    def on_draw(self):
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()

        # Draw everything
        self.meteor_list.draw()
        self.bullet_list.draw()
        self.player_list.draw()

        # Activate the game camera
        self.camera.use()

        # Draw our Scene
        self.scene.draw()

        # Activate the GUI camera before drawing GUI elements
        self.gui_camera.use()

        # Draw our score on the screen, scrolling it with the viewport
        score_text = f"Score: {self.score}"
        arcade.draw_text(
            score_text,
            10,
            10,
            arcade.csscolor.BLACK,
            18,
        )

    def on_mouse_press(self, x, y, button, modifiers):
        """ Called whenever the mouse button is clicked. """

        # Create a bullet
        bullet = arcade.Sprite(":resources:images/space_shooter/laserBlue01.png", SPRITE_SCALING_LASER)

        # Position the bullet at the player's current location
        start_x = self.player_sprite.center_x
        start_y = self.player_sprite.center_y
        bullet.center_x = start_x
        bullet.center_y = start_y

        # Get from the mouse the destination location for the bullet
        # IMPORTANT! If you have a scrolling screen, you will also need
        # to add in self.view_bottom and self.view_left.
        dest_x = x
        dest_y = y
        # Do math to calculate how to get the bullet to the destination.
        # Calculation the angle in radians between the start points
        # and end points. This is the angle the bullet will travel.
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)

        # Angle the bullet sprite so it doesn't look like it is flying
        # sideways.
        bullet.angle = math.degrees(angle)
        print(f"Bullet angle: {bullet.angle:.2f}")

        # Taking into account the angle, calculate our change_x
        # and change_y. Velocity is how fast the bullet travels.
        bullet.change_x = math.cos(angle) * BULLET_SPEED
        bullet.change_y = math.sin(angle) * BULLET_SPEED

        # Add the bullet to the appropriate lists
        self.bullet_list.append(bullet)
        arcade.play_sound(self.hit_sound)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                arcade.play_sound(self.jump_sound)
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0

    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2
        )
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = screen_center_x, screen_center_y

        self.camera.move_to(player_centered)

    def update(self, delta_time):
        """Movement and game logic"""

        # Call update on bullet list
        self.bullet_list.update()

        # Loop through each bullet
        for bullet in self.bullet_list:

            # Check this bullet to see if it hit a meteor
            hit_list = arcade.check_for_collision_with_list(bullet, self.meteor_list)

            # If it did, get rid of the meteor
            if len(hit_list) > 0:
                bullet.remove_from_sprite_lists()

            # For every meteor we hit, add to the score and remove the meteor
            for meteor in hit_list:
                meteor.remove_from_sprite_lists()
                self.score += 2

            # If the bullet flies off-screen, remove it.
            if bullet.bottom > self.width or bullet.top < 0 or bullet.right < 0 or bullet.left > self.width:
                bullet.remove_from_sprite_lists()

        # Move the player with the physics engine
        self.physics_engine.update()

        # Did the player fall off the map?
        if self.player_sprite.center_y < -100:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y

            arcade.play_sound(self.game_over)

        # Did the player touch something they should not?
        if arcade.check_for_collision_with_list(self.player_sprite, self.scene[LAYER_NAME_DONT_TOUCH]):

            self.player_sprite.change_x = 0

            self.player_sprite.change_y = 0

            self.player_sprite.center_x = PLAYER_START_X

            self.player_sprite.center_y = PLAYER_START_Y

            gameoverView = GameOverView()
            self.window.show_view(gameoverView)

            arcade.play_sound(self.game_over)

        # See if we hit any coins
        coin_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[LAYER_NAME_COINS]
        )

        # Loop through each coin we hit (if any) and remove it
        for coin in coin_hit_list:
            # Remove the coin
            coin.remove_from_sprite_lists()
            # Play a sound
            arcade.play_sound(self.collect_coin_sound)
            self.score += 1

        # See if the user got to the end of the level
        if self.player_sprite.center_x >= self.end_of_map:

            # Advance to the next level
            self.level += 1

            # Make sure to keep the score from this level when setting up the next level
            self.reset_score = False

            # Load the next level
            self.setup()

        # Position the camera
        self.center_camera_to_player()


class GameOverView(arcade.View):
    # class to manage the game overview

    def on_show_view(self):
        # when switching to this view
        arcade.set_background_color(arcade.color.RED)
        arcade.play_sound(self.game_over)

    def on_draw(self):
        # draw game overview
        self.clear()
        arcade.draw_text(
            "GAME OVER - Click to restart",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2,
            arcade.color.WHITE,
            30, anchor_x="center",
            )

    def on_mouse_press(self, x, y, button, modifiers):
        # press mouse to advance to "game" view
        game_view = GameView()
        self.window.show_view(game_view)


def main():
    """Main function"""
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    instructionView = InstructionView()
    window.show_view(instructionView)
    arcade.run()


if __name__ == "__main__":
    main()
