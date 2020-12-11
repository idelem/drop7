import sys, pygame
from pygame.locals import *
import random
import pygcurse

N = 7
MAX_DROPS = 5
PER_LEVEL = 17000

# import curses
# stdscr = curses.initscr()
# # turn off automatic echoing of keys to the screen
# curses.noecho()
# # react to keys instantly, without requiring the Enter key to be pressed
# curses.cbreak()

def _calcfontsize(font):
    """Returns the maximum width and maximum height used by any character in this font. This function is used to calculate the cell size."""
    maxwidth = 0
    maxheight = 0
    for i in range(32, 127):
        surf = font.render(chr(i), True, (0,0,0))
        if 2 * surf.get_width() > maxwidth:
            maxwidth = 2 * surf.get_width()
        if surf.get_height() > maxheight:
            maxheight = surf.get_height()

    return maxwidth, maxheight

pygcurse.calcfontsize = _calcfontsize

class Board():
    tiles = {0:' ', 1:'1', 2:'2', 3:'3', 4:'4', 5:'5', 6:'6', 7:'7', -1:'○', -2:'◎'}
    color = {
        0: pygame.Color(0, 0, 0), 
        1: pygame.Color(107, 186, 61), 
        2: pygame.Color(206, 206, 0), 
        3: pygame.Color(241, 139, 38), 
        4: pygame.Color(211, 44, 36), 
        5: pygame.Color(192, 64, 149), 
        6: pygame.Color(11, 186, 249), 
        7: pygame.Color(71, 94, 174), 
        -1: pygame.Color(158, 160, 159), 
        -2: pygame.Color(158, 160, 159)
    }
    # tiles = {0:' ', 1:'①', 2:'②', 3: '③', 4:'④', 5:'⑤', 6:' ⑥', 7:'⑦', -1:'○', -2:'◎'}

    counts = {'row': [[0 for i in range(N)] for j in range(N)], 'col': [0 for i in range(N)]}

    def __init__(self, win):
        self.win = win
        self.board = [[0 for i in range(N)] for j in range(N)]
        # init 4 rows
        for i in range (N-4, N):
            self.board[i] = [random.randint(-2, 7) for j in range(N)]
        
        self._dirty = False
        self._score = 0
        self.update(wait=0, redraw=False)
        self._score = 0
        self._chain = 0
        self._blown = 0
        self._level = 0

    def update(self, wait=100, redraw=True):
        self._dirty = True
        self._chain = 0
        while self._dirty:
            self._blown = 0
            self.count()
            if redraw:
                self.draw(wait=wait)
            self.blow()
            if redraw:
                self.draw(wait=wait)
            self.drop()
            self.score()
            self._chain += 1

    def drop(self):
        for row in range(N-1, -1, -1):
            for col in range(N):
                if self.board[row][col] == 0:
                    cur_col = [self.board[r][col] for r in range(N)]
                    cur_col = [e for e in cur_col if e != 0]
                    for i in range(N - len(cur_col)):
                        cur_col.insert(0, 0)
                    for i in range(N):
                        self.board[i][col] = cur_col[i]
        return
    
    def blow(self):
        self._dirty = False
        for row in range(N-1, -1, -1):
            for col in range(N):
                cur = self.board[row][col]
                if cur == 0:
                    continue
                if cur == self.counts['row'][row][col] or cur == self.counts['col'][col]:
                    self.board[row][col] = 0
                    self.break_neighbor(row, col)
                    self._dirty = True
                    self._blown += 1
        return

    def break_neighbor(self, row, col):
        for x,y in [(col-1, row), (col+1, row), (col, row-1), (col, row+1)]:
                if x < 0 or x >= N or y < 0 or y >= N:
                    continue
                if self.board[y][x] == -2:
                    self.board[y][x] = -1
                elif self.board[y][x] == -1:
                    self.board[y][x] = random.randint(1,N)
        # self.draw()
        return

    def score(self):
        self._score += N * int((self._chain + 1) ** 2.5) * self._blown
        self.draw_score()
        return

    def count(self):
        for row in range(N):
            self.counts['row'][row] = [0 for i in range(N)]
            start = 0
            for col in range(N):
                if self.board[row][col] == 0:
                    streak = col - start
                    if streak == 0:
                        self.counts['row'][row][col] = 0
                    else:
                        self.counts['row'][row][start:col] = [streak for i in range(streak)]
                    start = col + 1
            streak = N - start
            if streak > 0:
                self.counts['row'][row][start:N] = [streak for i in range(streak)]

        for col in range(N):
            col_i = [self.board[row][col] for row in range(N)]
            self.counts['col'][col] = N - col_i.count(0)

    def __str__(self):
        s = [''.join([self.tiles[n] for n in row]) for row in self.board]
        s = '\n'.join(s)
        return s

    def pp(self):
        s = [' '.join([str(n) for n in row]) for row in self.board]
        s = '\n'.join(s)
        return s

    def rise(self):
        is_dead = self.is_full()
        del self.board[0]
        self.board.append([-2 for i in range(N)])
        self._level += 1
        self._score += self._level * PER_LEVEL
        self.update()
        return is_dead
    
    def is_full(self):
        for i in range(N):
            if self.counts['col'][i] == N:
                return True
        return False
    
    def put(self, col, piece):
        if self.counts['col'][col] == N:
            return False
        self.board[0][col] = piece
        self.drop()
        self.count()
        self.draw()
        return True
    
    def draw(self, wait=50):
        X = 1
        Y = 1
        for row in range(N):
            for col in range(N):
                ch = self.tiles[self.board[row][col]]
                cl = self.color[self.board[row][col]]
                self.win.putchar(ch, x=col+X, y=row+Y, fgcolor=cl, bgcolor='black')
        pygame.time.delay(wait)
        return
    
    def draw_pieces_left(self, n):
        p = '◆' * n + '◇' * (MAX_DROPS-n)
        for row in range(MAX_DROPS): # 2-6
            self.win.putchar(p[row], x=0, y=6-row)
    
    def draw_score(self):
        s = '{:0>9d}'.format(self._score)
        self.win.putchars(s, x=0, y=8)

pygame.init()
font = pygame.font.Font("Silver.ttf", 24)
win = pygcurse.PygcurseWindow(9, 9, 'Hello World Program', fgcolor='black', bgcolor='gray', font=font)
win.setscreencolors('black', 'gray', clear=True)
# win.autowindowupdate = False
# win.autoupdate = False

def main():
    gameover = False
    board = Board(win)
    drops = MAX_DROPS
    pos = N // 2
    dropping = False

    board.draw_pieces_left(drops)
    board.draw_score()

    while not gameover:

        if drops == 0:
            gameover = board.rise()
            drops = MAX_DROPS if not gameover else 0
            board.draw_pieces_left(drops)
        if gameover:
            win.putchars("GAME OVER", x=0, y=0)
            # TODO: start again
        
        # win.putchars(str(board), x=1, y=2, fgcolor='white', bgcolor='black', indent=True)
        board.draw(wait=0)

        piece = random.randint(1, N)
        win.putchar(str(piece), x=pos+1, y=0)

        while True:
            turn_ends = False
            for event in pygame.event.get(): # event handling loop
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == KEYUP:
                    if (event.key == K_LEFT or event.key == K_a):
                        win.putchar(" ", x=pos+1, y=0)
                        pos = max(0, pos - 1)
                        win.putchar(str(piece), x=pos+1, y=0)
                    elif (event.key == K_RIGHT or event.key == K_d):
                        win.putchar(" ", x=pos+1, y=0)
                        pos = min(N-1, pos + 1)
                        win.putchar(str(piece), x=pos+1, y=0)
                    elif (event.key == K_DOWN or event.key == K_s):
                        # TODO animate
                        if board.put(pos, piece):
                            win.putchar(" ", x=pos+1, y=0)
                            drops -= 1
                            board.update()
                            board.draw_pieces_left(drops)
                            turn_ends = True
                            break
            if turn_ends:
                break

if __name__ == '__main__':
    main()