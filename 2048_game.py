import curses
from random import choice
from collections import defaultdict
import numpy as np

letter_codes = [ord ( ch ) for ch in 'WASDRQwasdrq']
actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit']
actions_dict = dict ( zip ( letter_codes, actions * 2 ) )
def winv():
    try:
        max_score = int(input("max score: "))
        if max_score <= 0:
            max_score = 2048
            print("maximum score set to default.")
        return  max_score
    except:
        print ( "maximum score set to default." )
        return 2048

def board_size():
    try:
        bsize = int(input("Board size: "))
        if bsize <= 0:
            bsize = 5
            print ( "board size set to default." )
        return  bsize
    except:
        print ( "board size set to default." )
        return 5


bsize = board_size()
max_score = winv()

def get_user_action(keyboard):
    char = "N"
    while char not in actions_dict:
        char = keyboard.getch()
        if char not in actions_dict :
            keyboard.addstr('Enter a valid input: \n')
            keyboard.refresh()
    return actions_dict[char]


def transpose(field):
    return [list ( row ) for row in zip ( *field )]


def invert(field):
    return [row[::-1] for row in field]


class GameField ( object ):
    def __init__(self, size=4, win=2048):
        self.size = size
        self.win_value = win
        self.reset ( )

    def reset(self):
        self.field = np.zeros((self.size,self.size), dtype=int)
        self.spawn ( )

    def move(self, direction):
        def move_row_left(row):
            def tighten(row):
                new_row = [i for i in row if i != 0]
                new_row += [0 for i in range ( len ( row ) - len ( new_row ) )]
                return new_row

            def merge(row):
                pair = False
                new_row = []
                for i in range ( len ( row ) ):
                    if pair:
                        new_row.append ( 2 * row[i] )
                        pair = False
                    else:
                        if i + 1 < len ( row ) and row[i] == row[i + 1]:
                            pair = True
                            new_row.append ( 0 )
                        else:
                            new_row.append ( row[i] )
                assert len ( new_row ) == len ( row )
                return new_row

            return tighten ( merge ( tighten ( row ) ) )

        moves = {}
        moves['Left'] = lambda field: \
            [move_row_left ( row ) for row in field]
        moves['Right'] = lambda field: \
            invert ( moves['Left'] ( invert ( field ) ) )
        moves['Up'] = lambda field: \
            transpose ( moves['Left'] ( transpose ( field ) ) )
        moves['Down'] = lambda field: \
            transpose ( moves['Right'] ( transpose ( field ) ) )

        if direction in moves:
            if self.move_is_possible ( direction ):
                self.field = moves[direction] ( self.field )
                self.spawn ( )
                return True
            else:
                return False

    def is_win(self):
        return any ( any ( i >= self.win_value for i in row ) for row in self.field )

    def is_gameover(self):
        return not any ( self.move_is_possible ( move ) for move in actions )

    def draw(self, screen):
        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '     (R)Restart (Q)Exit'
        gameover_string = '           GAME OVER'
        win_string = '          YOU WIN!'

        def cast(string):
            screen.addstr ( string + '\n' )

        def draw_hor_separator():
            top = ' ' + ('       ' * self.size + ' ')[1:]
            mid = ' ' + ('       ' * self.size + ' ')[1:]
            bot = ' ' + ('       ' * self.size + ' ')[1:]
            separator = defaultdict ( lambda: mid )
            separator[0], separator[self.size] = top, bot
            if not hasattr ( draw_hor_separator, "counter" ):
                draw_hor_separator.counter = 0
            cast ( separator[draw_hor_separator.counter] )
            draw_hor_separator.counter += 1

        def draw_row(row):
            cast ( ''.join ( ' {: ^5} '.format ( num ) if num > 0 else '   .   '  for num in row ) )

        screen.clear ( )

        for row in self.field:
            draw_hor_separator ( )
            draw_row ( row )
        draw_hor_separator ( )
        if self.is_win ( ):
            cast ( win_string )
        else:
            if self.is_gameover ( ):
                cast ( gameover_string )
            else:
                cast ( help_string1 )
        cast ( help_string2 )

    def spawn(self):
        (i, j) = choice (
            [(i, j) for i in range ( self.size ) for j in range ( self.size ) if self.field[i][j] == 0] )
        self.field[i][j] = 2

    def move_is_possible(self, direction):
        def row_is_left_movable(row):
            def change(i):  # true if there'll be change in i-th tile
                if row[i] == 0 and row[i + 1] != 0:  # Move
                    return True
                if row[i] != 0 and row[i + 1] == row[i]:  # Merge
                    return True
                return False

            return any ( change ( i ) for i in range ( len ( row ) - 1 ) )

        check = {}
        check['Left'] = lambda field: \
            any ( row_is_left_movable ( row ) for row in field )

        check['Right'] = lambda field: \
            check['Left'] ( invert ( field ) )

        check['Up'] = lambda field: \
            check['Left'] ( transpose ( field ) )

        check['Down'] = lambda field: \
            check['Right'] ( transpose ( field ) )

        if direction in check:
            return check[direction] ( self.field )
        else:
            return False


def main(stdscr):

    curses.use_default_colors ( )
    game_field = GameField (size=bsize, win=max_score )
    state_actions = {}  # Init, Game, Win, Gameover, Exit

    def init():
        game_field.reset ( )
        return 'Game'

    state_actions['Init'] = init

    def not_game(state):
        game_field.draw ( stdscr )
        action = get_user_action ( stdscr )
        responses = defaultdict ( lambda: state )
        responses['Restart'], responses['Exit'] = 'Init', 'Exit'
        return responses[action]

    state_actions['Win'] = lambda: not_game ( 'Win' )
    state_actions['Gameover'] = lambda: not_game ( 'Gameover' )

    def game():
        game_field.draw ( stdscr )
        action = get_user_action ( stdscr )
        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if game_field.move ( action ):  # move successful
            if game_field.is_win ( ):
                return 'Win'
            if game_field.is_gameover ( ):
                return 'Gameover'
        return 'Game'

    state_actions['Game'] = game

    state = 'Init'
    while state != 'Exit':
        state = state_actions[state] ( )


curses.wrapper ( main )
