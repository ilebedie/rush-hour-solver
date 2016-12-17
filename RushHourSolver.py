import fileinput
import copy

class Car:
    """ Car is convenience class to calculate collisions and track
        coordinates, without it one should work with Grid directly
    """
    def __init__(self, id, pos_row, pos_column, length, grid):
        self.pos_row = pos_row
        self.pos_col = pos_column
        self.horizontal = True
        self.length = length
        self.id = id
        self.grid = grid

        if self.grid.get_field(self.pos_row, self.pos_col + 1) == self.id:
            self.horizontal = True
        else:
            self.horizontal = False

    def is_at_right_wall(self):
        return self.pos_col == self.grid.num_cols - self.length

    def collides(self):
        if self.horizontal:
            wall_on_the_left = self.pos_col == -1
            wall_on_the_right = self.pos_col + self.length == self.grid.num_cols + 1
            if wall_on_the_left or wall_on_the_right :
                return True
        else:
            wall_on_the_top = self.pos_row == -1
            wall_on_the_bottom = self.pos_row + self.length == self.grid.num_rows + 1
            if wall_on_the_top or wall_on_the_bottom:
                return True

        car_back = self.grid.get_field(self.pos_row, self.pos_col)
        # Check for case  when move to the left or up
        if car_back != '.' and car_back != self.id:
            return True

        car_front = ''
        if self.horizontal:
            car_front = self.grid.get_field(self.pos_row, self.pos_col + self.length - 1)
        else:
            car_front = self.grid.get_field(self.pos_row + self.length - 1, self.pos_col)

        if car_front != '.' and car_front != self.id:
            return True

        return False

    def remove_from_grid(self):
        if self.horizontal is True:
            for col in range(self.length):
                self.grid.set_field('.', self.pos_row, self.pos_col + col)
        else:
            for row in range(self.length):
                self.grid.set_field('.', self.pos_row + row, self.pos_col)

    def place_on_grid(self):
        if self.horizontal is True:
            for col in range(self.length):
                self.grid.set_field(self.id, self.pos_row, self.pos_col + col)
        else:
            for row in range(self.length):
                self.grid.set_field(self.id, self.pos_row + row, self.pos_col)

    def can_move_to(self, direction):
        if self.horizontal is True and (direction == 'Up' or direction == 'Down'):
            return False
        if self.horizontal is False and (direction == 'Left' or direction == 'Right'):
            return False
        return True

    def move(self, direction):
        if direction == 'Left':
            self.pos_col -= 1
        if direction == 'Right':
            self.pos_col += 1
        if direction == 'Down':
            self.pos_row += 1
        if direction == 'Up':
            self.pos_row -= 1

class Grid:
    """Grid describes the board with pieces on it
    """
    def __init__(self, data, num_rows, num_cols):
        self.data = data
        self.num_rows = num_rows
        self.num_cols = num_cols

    def __iter__(self):
        return self.data.__iter__()

    def set_field(self, val, row, col):
        self.data[self.get_index(row, col)] = val

    def get_field(self, row, col):
        return self.data[self.get_index(row, col)]

    def get_index(self, row, col):
        return row * self.num_cols + col

    def get_coord(self, index):
        col = index % self.num_cols
        row = (index - col) // self.num_cols
        return row, col

    def __str__(self):
        return ''.join(self.data)

    def pretty_print(self):
        for row in range(self.num_rows):
            for col in range(self.num_cols):
                print(self.get_field(row, col), end="")
            print("")
        print("")


class GameState:
    """ Tracks the state of current grid and tries to
        figure out which moves are possible
    """
    def __init__(self, grid):
        self.num_rows = grid.num_rows
        self.num_columns = grid.num_cols
        self.grid = grid
        self.cars = {}
        self.setup_cars_from_grid()
        if 'r' not in self.cars:
            raise Exception("Red car is not set")

    def setup_cars_from_grid(self):
        # Identify cars on a board
        for idx, field in enumerate(self.grid):
            if field == '.':
                continue
            if field not in self.cars:
                row, col = self.grid.get_coord(idx)
                self.cars[field] = Car(id=field, pos_row=row, pos_column=col, length=1, grid=self.grid)
            else:
                self.cars[field].length += 1

        #for name, car in self.cars.items():
        #    print(name, " row:", car.pos_row, " col:", car.pos_col, " length:", car.length, " horizontal:", car.horizontal)

    def is_solution(self):
        red_car = self.cars['r']
        return red_car.is_at_right_wall()

    def try_move_car(self, car_id, direction):
        car = self.cars[car_id]
        if not car.can_move_to(direction):
            return False

        car_to_move = copy.copy(car)
        car_to_move.move(direction)

        if car_to_move.collides():
            return False

        car.remove_from_grid()
        car_to_move.place_on_grid()
        self.cars[car_id] = car_to_move

        return True

    def generate_next_move(self):
        for car_id in self.cars:
            for direction in ['Right', 'Left', 'Down', 'Up']:
                new_board = copy.deepcopy(self)
                if new_board.try_move_car(car_id, direction) is True:
                    yield (car_id + ' ' + direction, new_board)

    def __str__(self):
        return str(self.grid)

    def pretty_print(self):
        self.grid.pretty_print()


class Solver:
    ''' Solver implements BFS in order to find puzzle solution
    '''
    def __init__(self, initial_board_state, debug_mode):
        # BFS queue:
        # Board states have to be checked, also contains the sequence of moves
        self.queue = [(initial_board_state, 'initial position')]
        # We should memoize board states that we already checked
        self.checked_moves = set()

    def solve(self):
        while len(self.queue) > 0:
            board_state, moves = self.queue.pop()
            #print(moves)
            #board_state.pretty_print()
            if board_state.is_solution():
                # Instead of returning the first answer
                # we can also proceed here, add this solution
                # to solution list and to try to find another solutions
                board_state.pretty_print()
                return moves
            self.checked_moves.add(str(board_state))

            # Try all possible moves with every car on the board
            for move, new_board in board_state.generate_next_move():
                # skip the moves that we already checked
                if str(new_board) in self.checked_moves:
                    continue
                self.queue.insert(0, (new_board, moves + ';\n' + move))

        return "It is not possible to solve this configuration"

def read_input(file):
    grid_data = []
    for line in fileinput.input(file):
        row = (line.strip())
        grid_data.extend(list(row))
    initial_grid = Grid(grid_data, num_rows=6, num_cols=6)
    initial_board = GameState(initial_grid)
    return initial_board

if __name__ == '__main__':
    initial_board = read_input('input_empty.txt')
    #initial_board = read_input('input_1_car_on_a_way.txt')
    #initial_board = read_input('input_2_car_on_a_way.txt')
    solution = Solver(initial_board, debug_mode=True).solve()
    print(solution)

